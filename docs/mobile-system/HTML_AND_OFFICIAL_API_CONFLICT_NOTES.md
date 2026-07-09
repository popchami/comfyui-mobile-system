# HTML and Official API Conflict Notes

## Purpose

This file records whether the user-created full HTML can conflict with official ComfyUI APIs.

## Short answer

```text
The full HTML should not conflict with official ComfyUI APIs when it only acts as a client that calls official endpoints.
```

The HTML is a browser-side control surface.
It sends requests to ComfyUI.
It does not replace ComfyUI server routes by itself.

## Why it usually does not conflict

The existing HTML behavior uses ComfyUI routes such as:

```text
/prompt
/ws
/history/{prompt_id}
/view
/upload/image
/queue
```

This is normal client behavior.

Multiple clients can use the same ComfyUI server:

```text
- ComfyUI web UI
- user-created full HTML
- smartphone app
- Analyzer download route
```

As long as they only call APIs and do not overwrite server routes, they do not conflict by existing at the same time.

## Real conflict risks

Conflicts can happen if the project does any of these:

```text
1. Creates custom server routes with the same path as official ComfyUI routes.
2. Changes the behavior of official routes like /prompt, /upload/image, /history, /view, or /queue.
3. Treats fixed HTML workflow construction as the new app architecture.
4. Reuses fixed node ids from HTML against user-provided workflows.
5. Uses the same output filenames/subfolders in a way that overwrites or confuses generated files.
6. Assumes every ComfyUI version supports the same upload route behavior.
7. Mixes HTML-only state with app_profile.json state without clear source-of-truth rules.
```

## Route namespace rule

Custom routes must use a project-specific namespace.

Allowed custom route pattern:

```text
/mobile_analyzer/...
```

Avoid custom routes such as:

```text
/upload/image
/upload/mask
/prompt
/history
/view
/queue
/object_info
/system_stats
```

Those are official or core ComfyUI-related routes and must not be replaced.

## HTML reuse rule

The full HTML can be used as a proven behavior reference for:

```text
- image upload flow
- i2i toggle behavior
- inpaint mode switching
- mask canvas UX
- mask upload flow
- /prompt submission
- /ws progress
- /history fallback
- /view result display
```

Do not use it as the source of truth for:

```text
- final workflow structure
- fixed node ids
- fixed model names
- fixed prompt lists
- fixed app architecture
```

## Official API priority

When there is overlap between full HTML behavior and official API behavior:

```text
official ComfyUI API behavior wins
```

The app should call official APIs directly when possible.

The HTML is reference material, not a competing API layer.

## App profile source of truth

For the smartphone app:

```text
app_profile.json + workflow.json are the source of truth.
```

The full HTML should not decide what the Flutter app patches.

The Analyzer decides patch_targets based on the user-provided workflow.

## Output and upload safety

Potential filename/subfolder conflicts should be handled by:

```text
- using returned filenames from ComfyUI upload responses
- storing uploaded source image and mask filenames per generation/profile/session
- not assuming fixed upload filenames
- not overwriting generated outputs intentionally
- treating output filename_prefix as workflow data, not global app state
```

## /upload/mask note

The project may use `/upload/mask` if it is available and validated in the target ComfyUI environment.

If not validated:

```text
Use /upload/image for mask PNG only when the workflow accepts it,
or show a clear unsupported mask upload warning.
```

Do not rely on `/upload/mask` as mandatory until RunPod validation confirms it.

## Validation requirements

Validate that these can coexist:

```text
- ComfyUI official UI still works.
- User-created full HTML still works as a separate client.
- Smartphone app can call official APIs.
- Analyzer custom routes under /mobile_analyzer do not collide with official routes.
- Upload/image, prompt, history, and view behavior remain unchanged.
```

## Product guardrail

```text
The full HTML is a client and a behavior reference.
Official ComfyUI APIs are the integration layer.
Analyzer custom routes must stay namespaced.
The smartphone app must stay workflow/profile-driven.
```
