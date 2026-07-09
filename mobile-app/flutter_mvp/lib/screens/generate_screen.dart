import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/app_profile.dart';
import '../models/generated_image.dart';
import '../models/local_profile.dart';
import '../services/comfy_api_client.dart';
import '../services/comfy_progress_client.dart';
import '../services/history_image_extractor.dart';
import '../services/workflow_patcher.dart';

class GenerateScreen extends StatefulWidget {
  const GenerateScreen({super.key, required this.profile});

  final LocalProfile profile;

  @override
  State<GenerateScreen> createState() => _GenerateScreenState();
}

class _GenerateScreenState extends State<GenerateScreen> {
  final Map<String, TextEditingController> _controllers = {};
  final Map<String, File> _selectedImages = {};
  final Map<String, String> _uploadedImageNames = {};
  String _status = 'Ready';
  String _patchedPreview = '';
  String _promptId = '';
  String _historyPreview = '';
  String _lastUsedSeed = '';
  List<GeneratedImage> _images = const [];
  List<GeneratedImage> _sessionHistory = const [];
  bool _submitting = false;
  ComfyProgressClient? _progressClient;
  StreamSubscription<ComfyProgressEvent>? _progressSub;

  AppProfile get _appProfile => widget.profile.appProfile;

  String get _fieldValuesPrefsKey => 'profile_field_values_${widget.profile.id}';

  @override
  void initState() {
    super.initState();
    for (final field in _appProfile.simpleFields) {
      if (field.type == 'image') continue;
      _controllers[field.fieldId] = TextEditingController(text: _defaultValueForField(field));
    }
    _restoreSavedFieldValues();
  }

  @override
  void dispose() {
    for (final controller in _controllers.values) {
      controller.dispose();
    }
    _progressSub?.cancel();
    _progressClient?.dispose();
    super.dispose();
  }

  String _defaultValueForField(UiField field) {
    return field.defaultValue?.toString() ?? '';
  }

  Future<void> _restoreSavedFieldValues() async {
    final prefs = await SharedPreferences.getInstance();
    final encoded = prefs.getString(_fieldValuesPrefsKey);
    if (encoded == null || encoded.isEmpty) return;
    try {
      final decoded = jsonDecode(encoded);
      if (decoded is! Map) return;
      if (!mounted) return;
      setState(() {
        for (final entry in decoded.entries) {
          final controller = _controllers[entry.key.toString()];
          if (controller == null) continue;
          controller.text = entry.value?.toString() ?? '';
        }
        _captureLastUsedSeed();
        _status = 'Restored previous values';
      });
    } catch (_) {
      // Ignore broken saved values. They can be overwritten on the next successful submit.
    }
  }

  Future<void> _saveFieldValues() async {
    final prefs = await SharedPreferences.getInstance();
    final values = <String, String>{};
    for (final entry in _controllers.entries) {
      values[entry.key] = entry.value.text;
    }
    await prefs.setString(_fieldValuesPrefsKey, jsonEncode(values));
  }

  void _resetFieldsToDefault() {
    setState(() {
      for (final field in _appProfile.simpleFields) {
        final controller = _controllers[field.fieldId];
        if (controller == null) continue;
        controller.text = _defaultValueForField(field);
      }
      _uploadedImageNames.clear();
      _selectedImages.clear();
      _captureLastUsedSeed();
      _status = 'Reset fields to profile defaults';
    });
  }

  Map<String, dynamic> _fieldValues() {
    final values = <String, dynamic>{};
    for (final entry in _controllers.entries) {
      values[entry.key] = entry.value.text;
    }
    for (final field in _appProfile.simpleFields.where((field) => field.type == 'image')) {
      final uploadedName = _uploadedImageNames[field.fieldId];
      values[field.fieldId] = uploadedName ?? field.defaultValue ?? '';
    }
    return values;
  }

  Map<String, dynamic> _patchedWorkflow() {
    return WorkflowPatcher.patchWorkflow(
      workflow: widget.profile.rawWorkflowJson,
      profile: _appProfile,
      fieldValues: _fieldValues(),
    );
  }

  Future<void> _pickImage(UiField field) async {
    final result = await FilePicker.platform.pickFiles(type: FileType.image);
    final path = result?.files.single.path;
    if (path == null) return;
    setState(() {
      _selectedImages[field.fieldId] = File(path);
      _uploadedImageNames.remove(field.fieldId);
      _status = 'Selected image for ${field.label}';
    });
  }

  Future<void> _uploadSelectedImages(ComfyApiClient client) async {
    for (final entry in _selectedImages.entries) {
      final uploadedName = await client.uploadImage(entry.value);
      _uploadedImageNames[entry.key] = uploadedName;
    }
  }

  void _buildPatchPreview() {
    try {
      final patched = _patchedWorkflow();
      setState(() {
        _status = 'Patch OK';
        _patchedPreview = const JsonEncoder.withIndent('  ').convert(patched);
      });
    } catch (e) {
      setState(() {
        _status = 'Patch failed: $e';
        _patchedPreview = '';
      });
    }
  }

  Future<void> _connectProgress() async {
    await _progressSub?.cancel();
    await _progressClient?.close();
    final progressClient = ComfyProgressClient(baseUrl: widget.profile.comfyUrl);
    _progressClient = progressClient;
    _progressSub = progressClient.events.listen(_handleProgressEvent);
    progressClient.connect();
  }

  void _handleProgressEvent(ComfyProgressEvent event) {
    if (!mounted) return;
    if (event.isProgress) {
      setState(() => _status = 'Progress ${event.progressValue ?? '?'} / ${event.progressMax ?? '?'}');
    } else if (event.isExecuting) {
      final node = event.executingNode;
      setState(() {
        _status = node == null || node == 'null' ? 'Execution complete; loading history...' : 'Executing node $node';
      });
    } else if (event.isExecutionError) {
      setState(() => _status = 'Execution error');
    }
  }

  Future<void> _submitPrompt() async {
    if (widget.profile.comfyUrl.isEmpty) {
      setState(() => _status = 'ComfyUI URL missing on local profile');
      return;
    }

    setState(() {
      _submitting = true;
      _status = 'Preparing prompt...';
      _promptId = '';
      _historyPreview = '';
      _images = const [];
    });

    try {
      await _connectProgress();
      final client = ComfyApiClient(baseUrl: widget.profile.comfyUrl);
      if (_selectedImages.isNotEmpty) {
        setState(() => _status = 'Uploading selected images...');
        await _uploadSelectedImages(client);
      }
      final patched = _patchedWorkflow();
      _captureLastUsedSeed();
      await _saveFieldValues();
      setState(() => _status = 'Submitting prompt...');
      final promptId = await client.queuePrompt(
        workflow: patched,
        clientId: _progressClient?.clientId,
      );
      setState(() {
        _status = 'Submitted; waiting for history...';
        _promptId = promptId;
        _patchedPreview = const JsonEncoder.withIndent('  ').convert(patched);
      });
      await _fetchHistoryWhenReady(client, promptId);
    } catch (e) {
      setState(() => _status = 'Submit failed: $e');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Future<void> _fetchHistoryWhenReady(ComfyApiClient client, String promptId) async {
    Object? lastError;
    // Match the proven legacy HTML behavior: keep polling /history as a fallback even when /ws is unavailable.
    for (var i = 0; i < 80; i++) {
      await Future<void>.delayed(const Duration(milliseconds: 1500));
      try {
        final history = await client.getHistory(promptId);
        if (history.containsKey(promptId)) {
          final historyItem = history[promptId];
          final itemMap = historyItem is Map<String, dynamic> ? historyItem : <String, dynamic>{};
          final images = HistoryImageExtractor.extractImages(
            historyItem: itemMap,
            client: client,
          );
          setState(() {
            _status = images.isEmpty ? 'History loaded' : 'Generated ${images.length} images';
            _historyPreview = const JsonEncoder.withIndent('  ').convert(historyItem);
            _images = images;
            _mergeIntoSessionHistory(images);
          });
          return;
        }
        if (mounted && i % 5 == 0) {
          setState(() => _status = 'Waiting for history... ${i + 1}/80');
        }
      } catch (e) {
        lastError = e;
        if (mounted && i % 5 == 0) {
          setState(() => _status = 'Waiting for history... ${i + 1}/80');
        }
      }
    }
    setState(() {
      _status = lastError == null ? 'History wait timed out' : 'History wait timed out: $lastError';
    });
  }

  String _imageKey(GeneratedImage image) {
    return '${image.type}/${image.subfolder}/${image.filename}';
  }

  void _mergeIntoSessionHistory(List<GeneratedImage> images) {
    if (images.isEmpty) return;
    final seen = _sessionHistory.map(_imageKey).toSet();
    final newImages = images.where((image) => seen.add(_imageKey(image))).toList();
    if (newImages.isEmpty) return;
    _sessionHistory = [...newImages, ..._sessionHistory];
  }

  void _openImagePreview(GeneratedImage image) {
    showDialog<void>(
      context: context,
      builder: (context) {
        return Dialog(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(image.filename, style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                ConstrainedBox(
                  constraints: const BoxConstraints(maxHeight: 420),
                  child: InteractiveViewer(
                    child: Image.network(image.url.toString(), fit: BoxFit.contain),
                  ),
                ),
                const SizedBox(height: 8),
                SelectableText(image.url.toString(), style: Theme.of(context).textTheme.bodySmall),
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: const Text('Close'),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  bool _containsAny(String value, List<String> needles) {
    final normalized = value.toLowerCase();
    return needles.any((needle) => normalized.contains(needle));
  }

  String _fieldSearchText(UiField field) {
    return '${field.fieldId} ${field.label} ${field.section} ${field.type}'.toLowerCase();
  }

  bool _isSeedField(UiField field) {
    return _containsAny(_fieldSearchText(field), ['seed']);
  }

  bool _isCoreInput(UiField field) {
    final text = _fieldSearchText(field);
    return field.type == 'image' || _containsAny(text, ['prompt', 'negative']);
  }

  bool _isBasicSetting(UiField field) {
    final text = _fieldSearchText(field);
    return _containsAny(text, [
      'basic_sampling',
      'seed',
      'steps',
      'cfg',
      'sampler',
      'scheduler',
      'denoise',
    ]);
  }

  bool _isSizeOrOutput(UiField field) {
    final text = _fieldSearchText(field);
    return _containsAny(text, [
      'size',
      'width',
      'height',
      'batch',
      'output',
      'filename',
      'prefix',
    ]);
  }

  bool _isExpertField(UiField field) {
    final text = _fieldSearchText(field);
    return _containsAny(text, ['unknown', 'debug', 'raw', 'expert']);
  }

  void _captureLastUsedSeed() {
    for (final field in _appProfile.simpleFields) {
      if (!_isSeedField(field)) continue;
      final controller = _controllers[field.fieldId];
      final value = controller?.text.trim() ?? '';
      if (value.isNotEmpty) {
        _lastUsedSeed = value;
        return;
      }
    }
  }

  void _reuseLastSeed(UiField field) {
    final controller = _controllers[field.fieldId];
    if (controller == null || _lastUsedSeed.isEmpty) return;
    setState(() {
      controller.text = _lastUsedSeed;
      _status = 'Reused seed $_lastUsedSeed';
    });
  }

  void _randomizeSeed(UiField field) {
    final controller = _controllers[field.fieldId];
    if (controller == null) return;
    final seed = Random().nextInt(0x7fffffff).toString();
    setState(() {
      controller.text = seed;
      _status = 'Random seed set';
    });
  }

  List<Widget> _buildGeneratedFieldSections(List<UiField> fields) {
    final core = <UiField>[];
    final basic = <UiField>[];
    final size = <UiField>[];
    final advanced = <UiField>[];
    final expert = <UiField>[];

    for (final field in fields) {
      if (_isCoreInput(field)) {
        core.add(field);
      } else if (_isBasicSetting(field)) {
        basic.add(field);
      } else if (_isSizeOrOutput(field)) {
        size.add(field);
      } else if (_isExpertField(field)) {
        expert.add(field);
      } else {
        advanced.add(field);
      }
    }

    if (core.isEmpty) {
      final fallback = fields.isNotEmpty ? fields.first : null;
      if (fallback != null) {
        core.add(fallback);
        basic.remove(fallback);
        size.remove(fallback);
        advanced.remove(fallback);
        expert.remove(fallback);
      }
    }

    final widgets = <Widget>[];
    if (core.isNotEmpty) {
      widgets.add(Text('Core Inputs', style: Theme.of(context).textTheme.titleMedium));
      widgets.add(const SizedBox(height: 8));
      widgets.addAll(core.map(_buildField));
    }
    _addFieldSectionTile(widgets, 'Basic Generation Settings', basic);
    _addFieldSectionTile(widgets, 'Size / Output', size);
    _addFieldSectionTile(widgets, 'Advanced Workflow Features', advanced);
    _addFieldSectionTile(widgets, 'Expert / Debug', expert);
    return widgets;
  }

  void _addFieldSectionTile(List<Widget> widgets, String title, List<UiField> fields) {
    if (fields.isEmpty) return;
    widgets.add(_buildFieldSectionTile(title: title, fields: fields));
  }

  Widget _buildFieldSectionTile({
    required String title,
    required List<UiField> fields,
  }) {
    return Card(
      child: ExpansionTile(
        title: Text(title),
        initiallyExpanded: false,
        childrenPadding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
        children: fields.map(_buildField).toList(),
      ),
    );
  }

  Widget _buildField(UiField field) {
    if (field.type == 'image') {
      return _buildImageField(field);
    }

    final controller = _controllers[field.fieldId]!;
    final maxLines = field.type == 'textarea' ? 4 : 1;
    final keyboardType = field.type == 'number' || field.type == 'slider'
        ? const TextInputType.numberWithOptions(decimal: true)
        : TextInputType.text;

    final textField = TextField(
      controller: controller,
      maxLines: maxLines,
      keyboardType: keyboardType,
      decoration: InputDecoration(
        labelText: field.label,
        helperText: _isSeedField(field) && _lastUsedSeed.isNotEmpty
            ? '${field.fieldId} / ${field.type} / last seed: $_lastUsedSeed'
            : '${field.fieldId} / ${field.type}',
        border: const OutlineInputBorder(),
      ),
    );

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          textField,
          if (_isSeedField(field)) ...[
            const SizedBox(height: 6),
            Wrap(
              alignment: WrapAlignment.end,
              spacing: 8,
              runSpacing: 8,
              children: [
                if (_lastUsedSeed.isNotEmpty)
                  OutlinedButton(
                    onPressed: () => _reuseLastSeed(field),
                    child: const Text('Use last seed'),
                  ),
                OutlinedButton(
                  onPressed: () => _randomizeSeed(field),
                  child: const Text('Random seed'),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildImageField(UiField field) {
    final selected = _selectedImages[field.fieldId];
    final uploadedName = _uploadedImageNames[field.fieldId];
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(field.label, style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 6),
              Text('Default: ${field.defaultValue ?? '-'}'),
              if (selected != null) ...[
                const SizedBox(height: 8),
                ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.file(
                    selected,
                    height: 180,
                    fit: BoxFit.contain,
                  ),
                ),
                const SizedBox(height: 6),
                Text('Selected: ${selected.path}'),
              ],
              if (uploadedName != null) Text('Uploaded: $uploadedName'),
              const SizedBox(height: 8),
              OutlinedButton(
                onPressed: () => _pickImage(field),
                child: const Text('Choose image'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildImage(GeneratedImage image) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () => _openImagePreview(image),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(image.filename),
            const SizedBox(height: 6),
            Image.network(image.url.toString()),
          ],
        ),
      ),
    );
  }

  Widget _buildHistoryStrip() {
    if (_sessionHistory.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text('Session history', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        SizedBox(
          height: 110,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: _sessionHistory.length,
            separatorBuilder: (_, __) => const SizedBox(width: 8),
            itemBuilder: (context, index) {
              final image = _sessionHistory[index];
              return InkWell(
                onTap: () => _openImagePreview(image),
                child: SizedBox(
                  width: 110,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Expanded(
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.network(image.url.toString(), fit: BoxFit.cover),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        image.filename,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
        const SizedBox(height: 12),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final fields = _appProfile.simpleFields;

    return Scaffold(
      appBar: AppBar(title: Text(widget.profile.name)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(_status),
          if (_promptId.isNotEmpty) Text('prompt_id: $_promptId'),
          const SizedBox(height: 12),
          ..._buildGeneratedFieldSections(fields),
          FilledButton(
            onPressed: _buildPatchPreview,
            child: const Text('Patch preview'),
          ),
          const SizedBox(height: 8),
          FilledButton(
            onPressed: _submitting ? null : _submitPrompt,
            child: Text(_submitting ? 'Submitting...' : 'Submit /prompt'),
          ),
          const SizedBox(height: 8),
          OutlinedButton(
            onPressed: _resetFieldsToDefault,
            child: const Text('Reset to profile defaults'),
          ),
          const SizedBox(height: 12),
          _buildHistoryStrip(),
          if (_images.isNotEmpty) ...[
            Text('Generated images', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            ..._images.map(_buildImage),
          ],
          if (_historyPreview.isNotEmpty) ...[
            Text('History', style: Theme.of(context).textTheme.titleMedium),
            SelectableText(
              _historyPreview,
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 12),
          ],
          if (_patchedPreview.isNotEmpty) ...[
            Text('Patched workflow', style: Theme.of(context).textTheme.titleMedium),
            SelectableText(
              _patchedPreview,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ],
      ),
    );
  }
}
