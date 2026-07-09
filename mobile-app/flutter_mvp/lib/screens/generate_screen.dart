import 'dart:convert';

import 'package:flutter/material.dart';

import '../models/app_profile.dart';
import '../models/local_profile.dart';
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
    super.dispose();
  }

  void _buildPatchPreview() {
    try {
      final values = <String, dynamic>{};
      for (final entry in _controllers.entries) {
        values[entry.key] = entry.value.text;
      }

      final patched = WorkflowPatcher.patchWorkflow(
        workflow: widget.profile.rawWorkflowJson,
        profile: _appProfile,
        fieldValues: values,
      );

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
          const SizedBox(height: 12),
          ...fields.map(_buildField),
          FilledButton(
            onPressed: _buildPatchPreview,
            child: const Text('Patch preview'),
          ),
          const SizedBox(height: 12),
          if (_patchedPreview.isNotEmpty)
            SelectableText(
              _patchedPreview,
              style: Theme.of(context).textTheme.bodySmall,
            ),
        ],
      ),
    );
  }
}
