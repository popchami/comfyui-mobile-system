import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';

import '../models/app_profile.dart';
import '../models/local_profile.dart';
import '../services/comfy_api_client.dart';
import '../services/comfy_progress_client.dart';
import '../services/workflow_patcher.dart';

class GenerateScreen extends StatefulWidget {
  const GenerateScreen({super.key, required this.profile});

  final LocalProfile profile;

  @override
  State<GenerateScreen> createState() => _GenerateScreenState();
}

class _GenerateScreenState extends State<GenerateScreen> {
  final Map<String, TextEditingController> _controllers = {};
  String _status = 'Ready';
  String _patchedPreview = '';
  String _promptId = '';
  String _historyPreview = '';
  bool _submitting = false;
  ComfyProgressClient? _progressClient;
  StreamSubscription<ComfyProgressEvent>? _progressSub;

  AppProfile get _appProfile => widget.profile.appProfile;

  @override
  void initState() {
    super.initState();
    for (final field in _appProfile.simpleFields) {
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
    return values;
  }

  Map<String, dynamic> _patchedWorkflow() {
    return WorkflowPatcher.patchWorkflow(
      workflow: widget.profile.rawWorkflowJson,
      profile: _appProfile,
      fieldValues: _fieldValues(),
    );
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
      setState(() => _status = 'Executing node ${event.executingNode ?? '-'}');
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
      _status = 'Submitting prompt...';
      _promptId = '';
      _historyPreview = '';
    });

    try {
      final patched = _patchedWorkflow();
      await _connectProgress();
      final client = ComfyApiClient(baseUrl: widget.profile.comfyUrl);
      final promptId = await client.queuePrompt(
        workflow: patched,
        clientId: _progressClient?.clientId,
      );
      setState(() {
        _status = 'Submitted';
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
    for (var i = 0; i < 60; i++) {
      await Future<void>.delayed(const Duration(seconds: 1));
      final history = await client.getHistory(promptId);
      if (history.containsKey(promptId)) {
        setState(() {
          _status = 'History loaded';
          _historyPreview = const JsonEncoder.withIndent('  ').convert(history[promptId]);
        });
        return;
      }
    }
    setState(() => _status = 'History wait timed out');
  }

  Widget _buildField(UiField field) {
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
