# Flutter MVP Scaffold

This folder is the planned Flutter version of the ComfyUI Mobile System app.

The current working prototype is still:

```text
mobile-app/prototype/index.html
```

This Flutter scaffold exists so implementation can start from the same architecture once the HTML prototype flow is verified.

## MVP app flow

```text
Setup ComfyUI URL
  ↓
Check /system_stats
  ↓
Fetch /mobile_analyzer/profiles
  ↓
Download profile zip
  ↓
Extract workflow.json + app_profile.json
  ↓
Save profile locally
  ↓
Render simple UI from app_profile.json
  ↓
Patch workflow.json using patch_targets
  ↓
Submit to /prompt
  ↓
Track progress with /ws
  ↓
Read /history/{prompt_id}
  ↓
Display /view images
```

## Suggested packages

```yaml
http: ^1.2.0
web_socket_channel: ^3.0.0
archive: ^3.6.0
path_provider: ^2.1.0
shared_preferences: ^2.3.0
file_picker: ^8.1.0
```

Package versions should be refreshed before actual Flutter implementation.

## Added MVP files

```text
lib/models/app_profile.dart
lib/models/local_profile.dart
lib/models/generated_image.dart
lib/services/workflow_patcher.dart
lib/services/comfy_api_client.dart
lib/services/profile_zip_service.dart
lib/services/local_profile_store.dart
lib/services/comfy_progress_client.dart
lib/services/history_image_extractor.dart
lib/screens/setup_screen.dart
lib/screens/remote_profiles_screen.dart
lib/screens/local_profiles_screen.dart
lib/screens/generate_screen.dart
```

### app_profile.dart

Contains initial Dart models for:

- AppProfile
- UiField
- PatchTarget

### local_profile.dart

Contains the local saved profile model:

- profile id
- profile name
- profile version
- workflow id
- saved timestamp
- raw app_profile JSON
- raw workflow JSON
- source ComfyUI URL

### generated_image.dart

Contains a generated image model with:

- filename
- subfolder
- type
- `/view` URL

### workflow_patcher.dart

Patches workflow JSON using `app_profile.patch_targets` only.

### comfy_api_client.dart

Contains initial HTTP methods for:

- GET `/system_stats`
- GET `/mobile_analyzer/profiles`
- GET `/mobile_analyzer/profiles/{id}/download`
- POST `/prompt`
- GET `/history/{prompt_id}`
- build `/view` image URLs
- POST `/upload/image`

### profile_zip_service.dart

Extracts and validates:

- `app_profile.json`
- `workflow.json`

from `mobile_profile_export.zip`.

### local_profile_store.dart

Uses `shared_preferences` to:

- load saved profiles
- save profiles
- upsert by profile id
- delete one profile
- clear all profiles

### comfy_progress_client.dart

Uses `web_socket_channel` to connect to ComfyUI `/ws` with a generated `clientId`.

It exposes a stream of `ComfyProgressEvent` values for:

- progress
- executing
- execution_error
- socket open/close/error

### history_image_extractor.dart

Extracts image records from `/history/{prompt_id}` output data and builds `/view` URLs through `ComfyApiClient`.

## Screen scaffolds

### setup_screen.dart

Entry screen for entering the ComfyUI URL.

Current behavior:

- accepts a ComfyUI URL
- checks `/system_stats` through `ComfyApiClient`
- opens RemoteProfilesScreen
- opens LocalProfilesScreen

### remote_profiles_screen.dart

Current behavior:

- fetches `/mobile_analyzer/profiles`
- displays remote profiles
- downloads selected profile zip
- parses zip with `ProfileZipService`
- saves profile with `LocalProfileStore`
- stores the source ComfyUI URL on the saved profile

### local_profiles_screen.dart

Current behavior:

- loads saved local profiles
- opens GenerateScreen for selected profile
- deletes a saved profile

### generate_screen.dart

Current behavior:

- reads `LocalProfile.appProfile.simpleFields`
- renders simple text fields
- renders image fields as image pickers
- collects text field values
- lets the user select local image files through `file_picker`
- uploads selected image files to `/upload/image`
- uses uploaded image names when patching image fields
- calls `WorkflowPatcher`
- shows patched workflow JSON as a preview
- submits patched workflow to `/prompt`
- connects to `/ws` with matching `clientId`
- shows basic progress/executing status
- polls `/history/{prompt_id}` until history is available
- extracts generated image records from history
- builds `/view` image URLs
- displays generated images with `Image.network`
- shows history JSON preview

## Initial screens

- SetupScreen
- RemoteProfilesScreen
- LocalProfilesScreen
- GenerateScreen
- HistoryScreen later
- SettingsScreen later

## Initial Dart structure

```text
lib/
  main.dart
  models/
    app_profile.dart
    local_profile.dart
    generated_image.dart
  services/
    comfy_api_client.dart
    profile_zip_service.dart
    local_profile_store.dart
    workflow_patcher.dart
    comfy_progress_client.dart
    history_image_extractor.dart
  screens/
    setup_screen.dart
    remote_profiles_screen.dart
    local_profiles_screen.dart
    generate_screen.dart
  widgets/
    dynamic_field_widget.dart
```

## Rule

Flutter app must follow the same MVP safety rule:

```text
Only patch fields listed in app_profile.json.patch_targets.
```

Do not build a full ComfyUI workflow editor in the first version.
