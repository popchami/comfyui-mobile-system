class ModelFolderResolver {
  const ModelFolderResolver._();

  static String? resolveFolder({
    required String type,
    required String pathHint,
  }) {
    final fromHint = _folderFromPathHint(pathHint);
    if (fromHint != null && fromHint.isNotEmpty) return fromHint;

    final normalizedType = type.toLowerCase().trim();
    if (normalizedType.isEmpty) return null;

    if (normalizedType.contains('checkpoint') || normalizedType == 'ckpt') return 'checkpoints';
    if (normalizedType.contains('lora')) return 'loras';
    if (normalizedType.contains('vae')) return 'vae';
    if (normalizedType.contains('clip')) return 'clip';
    if (normalizedType.contains('controlnet') || normalizedType.contains('control_net')) return 'controlnet';
    if (normalizedType.contains('upscale')) return 'upscale_models';
    if (normalizedType.contains('unet') || normalizedType.contains('diffusion_model')) return 'diffusion_models';
    if (normalizedType.contains('embeddings') || normalizedType.contains('embedding')) return 'embeddings';

    return null;
  }

  static String? _folderFromPathHint(String pathHint) {
    final normalized = pathHint.replaceAll('\\', '/').trim();
    if (normalized.isEmpty) return null;

    final parts = normalized.split('/').where((part) => part.isNotEmpty).toList();
    final modelsIndex = parts.indexWhere((part) => part.toLowerCase() == 'models');
    if (modelsIndex >= 0 && modelsIndex + 1 < parts.length) {
      return parts[modelsIndex + 1];
    }

    if (parts.length == 1) return parts.first;
    return null;
  }
}
