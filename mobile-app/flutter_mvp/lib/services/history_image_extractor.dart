import '../models/generated_image.dart';
import 'comfy_api_client.dart';

class HistoryImageExtractor {
  static List<GeneratedImage> extractImages({
    required Map<String, dynamic> historyItem,
    required ComfyApiClient client,
  }) {
    final images = <GeneratedImage>[];
    final outputs = historyItem['outputs'];
    if (outputs is! Map<String, dynamic>) return images;

    for (final output in outputs.values) {
      if (output is! Map<String, dynamic>) continue;
      final rawImages = output['images'];
      if (rawImages is! List<dynamic>) continue;

      for (final raw in rawImages) {
        if (raw is! Map<String, dynamic>) continue;
        final filename = raw['filename'] as String? ?? '';
        if (filename.isEmpty) continue;
        final subfolder = raw['subfolder'] as String? ?? '';
        final type = raw['type'] as String? ?? 'output';
        images.add(
          GeneratedImage(
            filename: filename,
            subfolder: subfolder,
            type: type,
            url: client.buildViewUri(
              filename: filename,
              subfolder: subfolder,
              type: type,
            ),
          ),
        );
      }
    }

    return images;
  }
}
