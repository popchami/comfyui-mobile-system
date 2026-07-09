import '../models/app_profile.dart';
import 'comfy_api_client.dart';
import 'model_folder_resolver.dart';

class EnvironmentModelCheckResult {
  const EnvironmentModelCheckResult({
    required this.objectNodeTypeCount,
    required this.foldersChecked,
    required this.foldersUnavailable,
    required this.foundNodeCount,
    required this.totalMissingNodeCount,
    required this.foundModelCount,
    required this.totalCheckableModelCount,
    required this.uncheckableModelCount,
  });

  final int objectNodeTypeCount;
  final Map<String, int> foldersChecked;
  final Map<String, String> foldersUnavailable;
  final int foundNodeCount;
  final int totalMissingNodeCount;
  final int foundModelCount;
  final int totalCheckableModelCount;
  final int uncheckableModelCount;

  int get stillMissingNodeCount => totalMissingNodeCount - foundNodeCount;

  int get stillMissingModelCount => totalCheckableModelCount - foundModelCount;

  String toDisplayText() {
    final lines = <String>[
      'Environment check: node types $objectNodeTypeCount.',
      if (totalMissingNodeCount > 0) 'Custom nodes found $foundNodeCount / $totalMissingNodeCount; still missing $stillMissingNodeCount.',
      if (totalCheckableModelCount > 0) 'Models found $foundModelCount / $totalCheckableModelCount; still missing $stillMissingModelCount.',
      if (uncheckableModelCount > 0) 'Models skipped $uncheckableModelCount because their folder could not be resolved.',
      if (foldersChecked.isNotEmpty) 'Folders checked: ${_formatFolderCounts(foldersChecked)}.',
      if (foldersUnavailable.isNotEmpty) 'Folders unavailable: ${foldersUnavailable.keys.join(', ')}.',
      'No models or custom nodes were installed automatically.',
    ];
    return lines.join('\n');
  }

  static String _formatFolderCounts(Map<String, int> values) {
    return values.entries.map((entry) => '${entry.key} ${entry.value}').join(', ');
  }
}

class EnvironmentModelChecker {
  EnvironmentModelChecker({required this.client});

  final ComfyApiClient client;

  Future<EnvironmentModelCheckResult> check(AppProfile profile) async {
    final objectInfo = await client.getObjectInfo();
    final objectClasses = objectInfo.keys.map((value) => value.toString()).toSet();

    final foundNodes = profile.missingNodes.where((node) => objectClasses.contains(node.classType)).length;

    final modelsByFolder = <String, List<MissingModel>>{};
    var uncheckableModelCount = 0;
    for (final model in profile.missingModels) {
      final folder = ModelFolderResolver.resolveFolder(
        type: model.type,
        pathHint: model.pathHint,
      );
      if (folder == null || folder.isEmpty) {
        uncheckableModelCount++;
        continue;
      }
      modelsByFolder.putIfAbsent(folder, () => <MissingModel>[]).add(model);
    }

    final foldersChecked = <String, int>{};
    final foldersUnavailable = <String, String>{};
    var foundModels = 0;
    var totalCheckableModels = 0;

    for (final entry in modelsByFolder.entries) {
      final folder = entry.key;
      final models = entry.value;
      totalCheckableModels += models.length;
      try {
        final available = await client.getModels(folder: folder);
        final availableSet = available.toSet();
        foldersChecked[folder] = available.length;
        foundModels += models.where((model) => availableSet.contains(model.name)).length;
      } catch (e) {
        foldersUnavailable[folder] = e.toString();
      }
    }

    return EnvironmentModelCheckResult(
      objectNodeTypeCount: objectClasses.length,
      foldersChecked: foldersChecked,
      foldersUnavailable: foldersUnavailable,
      foundNodeCount: foundNodes,
      totalMissingNodeCount: profile.missingNodes.length,
      foundModelCount: foundModels,
      totalCheckableModelCount: totalCheckableModels,
      uncheckableModelCount: uncheckableModelCount,
    );
  }
}
