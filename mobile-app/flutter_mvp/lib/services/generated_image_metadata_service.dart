import '../models/generated_image.dart';

class GeneratedImageMetadataService {
  const GeneratedImageMetadataService._();

  static List<GeneratedImage> attachSessionMetadata({
    required List<GeneratedImage> images,
    required String promptId,
    required String profileName,
    required String seed,
    String? createdAt,
  }) {
    final timestamp = createdAt ?? DateTime.now().toIso8601String();
    return images
        .map(
          (image) => image.copyWith(
            promptId: promptId,
            profileName: profileName,
            seed: seed,
            createdAt: timestamp,
          ),
        )
        .toList();
  }
}
