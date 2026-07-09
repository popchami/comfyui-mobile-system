# Flutter Screen Scaffold Plan

## Purpose

Define the first Flutter screens that mirror the HTML prototype flow.

## Screens

### SetupScreen

Role:

- Enter ComfyUI URL
- Check `/system_stats`
- Move to remote/local profiles

Initial fields:

- ComfyUI URL text field
- Connection status
- Check connection button
- Remote profiles button
- Local profiles button

### RemoteProfilesScreen

Role:

- Fetch `/mobile_analyzer/profiles`
- Download selected profile zip
- Parse zip
- Save profile locally

Initial actions:

- Load remote profile list
- Download selected profile
- Parse with ProfileZipService
- Save with LocalProfileStore

### LocalProfilesScreen

Role:

- Show saved profiles
- Load selected profile
- Delete profile

Initial actions:

- Load local profile list
- Open GenerateScreen
- Delete selected profile
- Clear all profiles

### GenerateScreen

Role:

- Render `app_profile.ui.simple`
- Collect field values
- Patch workflow with WorkflowPatcher
- Upload selected input image when needed
- Submit to `/prompt`
- Listen to `/ws`
- Read `/history/{prompt_id}`
- Display generated images

### HistoryScreen

Later role:

- Show generated image history
- Reopen generation settings

MVP can skip this screen.

## Navigation

```text
SetupScreen
  -> RemoteProfilesScreen
  -> LocalProfilesScreen
  -> GenerateScreen
```

## Important rule

Every screen must preserve the MVP rule:

```text
Only patch fields listed in app_profile.json.patch_targets.
```
