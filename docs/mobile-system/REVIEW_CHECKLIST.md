# Review Checklist

Review PR #1 before merging to main.

## Main question

Can this design support the first working version of ComfyUI Mobile System?

## Check items

- Is `app_profile.json` enough as the contract between Analyzer and mobile app?
- Are `patch_targets` safe for the MVP?
- Is the `simple / advanced / expert / hidden` UI split practical?
- Should unknown nodes be preserved as currently planned?
- Is `needs_attention` the right status name for special nodes?
- Is the MVP scope acceptable?
- Is `MobileProfileExporter` a reasonable first node?
- Are there obvious issues in `nodes.py` or `server.py`?
- Is the zip structure enough?
- What must be fixed before merge?

## Constraints

- Smartphone operation matters.
- Avoid manual file transfer to phone.
- Do not auto-install custom nodes in MVP.
- Do not auto-download models in MVP.
- Do not make the app a full workflow editor at first.

## Expected review result

Return:

- OK to merge or not OK to merge
- Blocking issues
- Non-blocking improvements
- Suggested implementation order
- Missing documents or files
