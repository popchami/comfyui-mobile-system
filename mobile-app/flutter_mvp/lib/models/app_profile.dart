class AppProfile {
  const AppProfile({
    required this.schemaVersion,
    required this.profileId,
    required this.profileName,
    required this.profileVersion,
    required this.workflowId,
    required this.simpleFields,
    required this.patchTargets,
    required this.missingNodes,
    required this.missingModels,
    required this.warnings,
  });

  final String schemaVersion;
  final String profileId;
  final String profileName;
  final String profileVersion;
  final String workflowId;
  final List<UiField> simpleFields;
  final List<PatchTarget> patchTargets;
  final List<MissingNode> missingNodes;
  final List<MissingModel> missingModels;
  final List<String> warnings;

  factory AppProfile.fromJson(Map<String, dynamic> json) {
    final ui = json['ui'] as Map<String, dynamic>? ?? const {};
    final simple = ui['simple'] as List<dynamic>? ?? const [];
    final targets = json['patch_targets'] as List<dynamic>? ?? const [];
    final missingNodes = json['missing_nodes'] as List<dynamic>? ?? const [];
    final missingModels = json['missing_models'] as List<dynamic>? ?? const [];
    final warnings = json['warnings'] as List<dynamic>? ?? const [];

    return AppProfile(
      schemaVersion: json['schema_version'] as String? ?? '',
      profileId: json['profile_id'] as String? ?? '',
      profileName: json['profile_name'] as String? ?? '',
      profileVersion: json['profile_version'] as String? ?? '',
      workflowId: json['workflow_id'] as String? ?? '',
      simpleFields: simple
          .whereType<Map<String, dynamic>>()
          .map(UiField.fromJson)
          .toList(),
      patchTargets: targets
          .whereType<Map<String, dynamic>>()
          .map(PatchTarget.fromJson)
          .toList(),
      missingNodes: missingNodes
          .whereType<Map<String, dynamic>>()
          .map(MissingNode.fromJson)
          .toList(),
      missingModels: missingModels
          .whereType<Map<String, dynamic>>()
          .map(MissingModel.fromJson)
          .toList(),
      warnings: warnings.map((value) => value.toString()).where((value) => value.isNotEmpty).toList(),
    );
  }
}

class UiField {
  const UiField({
    required this.fieldId,
    required this.label,
    required this.type,
    required this.section,
    required this.nodeId,
    required this.input,
    required this.defaultValue,
    required this.patchTargetId,
    this.nodeColor = '',
    this.nodeBgColor = '',
  });

  final String fieldId;
  final String label;
  final String type;
  final String section;
  final String nodeId;
  final String input;
  final dynamic defaultValue;
  final String patchTargetId;
  final String nodeColor;
  final String nodeBgColor;

  factory UiField.fromJson(Map<String, dynamic> json) {
    return UiField(
      fieldId: json['field_id'] as String? ?? '',
      label: json['label'] as String? ?? '',
      type: json['type'] as String? ?? 'text',
      section: json['section'] as String? ?? '',
      nodeId: json['node_id']?.toString() ?? '',
      input: json['input'] as String? ?? '',
      defaultValue: json['default'],
      patchTargetId: json['patch_target_id'] as String? ?? '',
      nodeColor: json['node_color'] as String? ?? '',
      nodeBgColor: json['node_bgcolor'] as String? ?? '',
    );
  }
}

class PatchTarget {
  const PatchTarget({
    required this.patchTargetId,
    required this.fieldId,
    required this.nodeId,
    required this.input,
    required this.valueType,
  });

  final String patchTargetId;
  final String fieldId;
  final String nodeId;
  final String input;
  final String valueType;

  factory PatchTarget.fromJson(Map<String, dynamic> json) {
    return PatchTarget(
      patchTargetId: json['patch_target_id'] as String? ?? '',
      fieldId: json['field_id'] as String? ?? '',
      nodeId: json['node_id']?.toString() ?? '',
      input: json['input'] as String? ?? '',
      valueType: json['value_type'] as String? ?? 'STRING',
    );
  }
}

class MissingNode {
  const MissingNode({
    required this.nodeId,
    required this.classType,
  });

  final String nodeId;
  final String classType;

  factory MissingNode.fromJson(Map<String, dynamic> json) {
    return MissingNode(
      nodeId: json['node_id']?.toString() ?? '',
      classType: json['class_type'] as String? ?? '',
    );
  }
}

class MissingModel {
  const MissingModel({
    required this.type,
    required this.name,
    required this.pathHint,
  });

  final String type;
  final String name;
  final String pathHint;

  factory MissingModel.fromJson(Map<String, dynamic> json) {
    return MissingModel(
      type: json['type'] as String? ?? '',
      name: json['name'] as String? ?? '',
      pathHint: json['path_hint'] as String? ?? '',
    );
  }
}
