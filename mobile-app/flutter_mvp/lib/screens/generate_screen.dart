import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

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
  List<GeneratedImage> _images = const [];
  bool _submitting = false;
  ComfyProgressClient? _progressClient;
  StreamSubscription<ComfyProgressEvent>? _progressSub;

  AppProfile get _appProfile => widget.profile.appProfile;

  @override
  void initState() {
    super.initState();
    for (final field in _appProfile.simpleFields) {
      if (field.type == 'image') continue;
      _controllers[field.fieldId] = TextEditingController(text: field.defaultValue?.toString() ?? '');
    }
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

  Widget _buildField(UiField field) {
    if (field.type == 'image') {
      return _buildImageField(field);
    }

    final controller = _controllers[field.fieldId]!;
    final maxLines = field.type == 'textarea' ? 4 : 1;
    final keyboardType = field.type == 'number' || field.type == 'slider'
        ? const TextInputType.numberWithOptions(decimal: true)
        : TextInputType.text;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextField(
        controller: controller,
        maxLines: maxLines,
        keyboardType: keyboardType,
        decoration: InputDecoration(
          labelText: field.label,
          helperText: '${field.fieldId} / ${field.type}',
          border: const OutlineInputBorder(),
        ),
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(image.filename),
          const SizedBox(height: 6),
          Image.network(image.url.toString()),
        ],
      ),
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
          ...fields.map(_buildField),
          FilledButton(
            onPressed: _buildPatchPreview,
            child: const Text('Patch preview'),
          ),
          const SizedBox(height: 8),
          FilledButton(
            onPressed: _submitting ? null : _submitPrompt,
            child: Text(_submitting ? 'Submitting...' : 'Submit /prompt'),
          ),
          const SizedBox(height: 12),
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
              style: Theme.of(context).textTheme.bodySmall),
          ],
        ],
      ),
    );
  }
}
