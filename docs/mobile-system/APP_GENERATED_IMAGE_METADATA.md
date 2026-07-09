# App Generated Image Metadata

## Purpose

This file records session-level metadata attached to generated images in the Flutter MVP.

The goal is to make session history more useful without adding persistent storage yet.

## Current implementation status

```text
Implemented in:
mobile-app/flutter_mvp/lib/models/generated_image.dart
mobile-app/flutter_mvp/lib/services/generated_image_metadata_service.dart
mobile-app/flutter_mvp/lib/screens/generate_screen.dart
```

## Metadata fields

`GeneratedImage` now supports optional metadata:

```text
promptId
profileName
seed
createdAt
```

These fields are optional so existing image extraction code does not break.

## Metadata service

`GeneratedImageMetadataService.attachSessionMetadata()` can attach metadata to a list of generated images:

```text
promptId
profileName
seed
createdAt
```

If `createdAt` is not supplied, it uses the current ISO-8601 timestamp.

## GenerateScreen integration

`GenerateScreen` now attaches metadata after `/history/{prompt_id}` returns generated images and before images are merged into `_sessionHistory`.

Current metadata source:

```text
promptId    -> current prompt_id
profileName -> local profile name
seed        -> last used seed detected from seed field
createdAt   -> ISO-8601 timestamp from GeneratedImageMetadataService
```

Session history thumbnails now show:

```text
filename
seed
profile name
```

Large image preview dialog now shows:

```text
image URL
profile name
seed
prompt_id
created_at
```

## Safety rules

```text
- Do not persist generated image history yet.
- Do not store generated image files permanently yet.
- Do not store private RunPod URLs in exported debug reports by default.
- Keep metadata session-level until Android validation confirms UI behavior.
```

## Deferred until Android validation

```text
- Persistent generated image history.
- Exportable generation metadata.
- Copy prompt_id / seed buttons.
- Filter history by profile or seed.
- Local image file caching.
```

## Runtime validation checklist

During Android validation, confirm:

```text
1. Generated image display still works.
2. Session history still deduplicates by filename/subfolder/type.
3. Metadata does not break image preview.
4. Long prompt_id/profile names do not overflow UI.
5. Session thumbnail height is enough for filename/seed/profile.
6. Large preview metadata remains readable.
7. No persistent storage is added unintentionally.
```
