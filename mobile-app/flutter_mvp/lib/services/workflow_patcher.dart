import '../models/app_profile.dart';

class WorkflowPatcher {
  static Map<String, dynamic> patchWorkflow({
    required Map<String, dynamic> workflow,
    required AppProfile profile,
    required Map<String, dynamic> fieldValues,
  }) {
    final patched = _deepCopyMap(workflow);

    for (final target in profile.patchTargets) {
      if (!fieldValues.containsKey(target.fieldId)) {
        continue;
      }

      final node = patched[target.nodeId];
      if (node is! Map<String, dynamic>) {
        throw WorkflowPatchException('Missing node: ${target.nodeId}');
      }

      final inputs = node['inputs'];
      if (inputs is! Map<String, dynamic>) {
        throw WorkflowPatchException('Missing inputs for node: ${target.nodeId}');
      }

      if (!inputs.containsKey(target.input)) {
        throw WorkflowPatchException('Missing input: ${target.nodeId}.${target.input}');
      }

      inputs[target.input] = _castValue(fieldValues[target.fieldId], target.valueType);
    }

    return patched;
  }

  static dynamic _castValue(dynamic value, String valueType) {
    switch (valueType) {
      case 'INT':
        if (value is int) return value;
        return int.parse(value.toString());
      case 'FLOAT':
        if (value is double) return value;
        if (value is int) return value.toDouble();
        return double.parse(value.toString());
      case 'BOOLEAN':
        if (value is bool) return value;
        return value.toString().toLowerCase() == 'true';
      case 'IMAGE':
      case 'STRING':
      case 'COMBO':
      case 'MODEL_NAME':
      case 'FILE_NAME':
      default:
        return value;
    }
  }

  static Map<String, dynamic> _deepCopyMap(Map<String, dynamic> value) {
    return value.map((key, child) => MapEntry(key, _deepCopyValue(child)));
  }

  static dynamic _deepCopyValue(dynamic value) {
    if (value is Map<String, dynamic>) {
      return _deepCopyMap(value);
    }
    if (value is List) {
      return value.map(_deepCopyValue).toList();
    }
    return value;
  }
}

class WorkflowPatchException implements Exception {
  WorkflowPatchException(this.message);

  final String message;

  @override
  String toString() => 'WorkflowPatchException: $message';
}
