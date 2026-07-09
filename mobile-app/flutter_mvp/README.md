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
lib/services/workflow_patcher.dart
lib/services/comfy_api_client.dart
lib/services/profile_zip_service.dart
lib/services/local_profile_store.dart
lib/services/comfy_progress_client.dart
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

## Screen scaffolds

### setup_screen.dart

Initial entry screen for entering the ComfyUI URL.

### remote_profiles_screen.dart

Placeholder for fetching remote profiles from the Analyzer API.

### local_profiles_screen.dart

Placeholder for saved local profiles.

### generate_screen.dart

Initial screen that reads `LocalProfile.appProfile.simpleFields` and lists fields.

Later this screen should render editable widgets and call `WorkflowPatcher`.

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
  services/
    comfy_api_client.dart
    profile_zip_service.dart
    local_profile_store.dart
    workflow_patcher.dart
    comfy_progress_client.dart
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
