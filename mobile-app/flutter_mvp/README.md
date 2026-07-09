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
lib/services/workflow_patcher.dart
lib/services/comfy_api_client.dart
lib/services/profile_zip_service.dart
```

### app_profile.dart

Contains initial Dart models for:

- AppProfile
- UiField
- PatchTarget

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

## Initial screens

- SetupScreen
- RemoteProfilesScreen
- LocalProfilesScreen
- GenerateScreen
- HistoryScreen
- SettingsScreen

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
