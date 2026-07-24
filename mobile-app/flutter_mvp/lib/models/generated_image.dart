class GeneratedImage {
  const GeneratedImage({
    required this.filename,
    required this.subfolder,
    required this.type,
    required this.url,
    this.promptId = '',
    this.profileName = '',
    this.seed = '',
    this.createdAt = '',
  });

  final String filename;
  final String subfolder;
  final String type;
  final Uri url;
  final String promptId;
  final String profileName;
  final String seed;
  final String createdAt;

  GeneratedImage copyWith({
    String? filename,
    String? subfolder,
    String? type,
    Uri? url,
    String? promptId,
    String? profileName,
    String? seed,
    String? createdAt,
  }) {
    return GeneratedImage(
      filename: filename ?? this.filename,
      subfolder: subfolder ?? this.subfolder,
      type: type ?? this.type,
      url: url ?? this.url,
      promptId: promptId ?? this.promptId,
      profileName: profileName ?? this.profileName,
      seed: seed ?? this.seed,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}
