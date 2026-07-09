# LLM-Assisted Workflow Analysis

## Purpose

This file records the concern that the dedicated custom node analysis is likely the hardest part of the project.

The Analyzer must read a user-provided ComfyUI workflow, understand enough of it, and write a smartphone-app-readable profile without corrupting the workflow.

## Core concern

The hardest part is not the smartphone UI alone.

The hardest part is:

```text
Read workflow/code-like JSON
  ↓
Analyze graph structure, node classes, inputs, outputs, dependencies, and editable fields
  ↓
Generate app_profile.json and patch_targets
  ↓
Package for the smartphone app
  ↓
Allow generation without breaking the original workflow
```

This analysis step is the core of the whole product.

If this is wrong, the smartphone app can show the wrong controls, patch the wrong values, misunderstand the output type, or fail generation.

## Can Ollama / Gemma / local LLMs be used?

Yes, they can be considered as optional helper tools for analysis.

Possible candidates:

```text
- Ollama running local models
- Gemma-family models
- other local LLMs
- remote LLMs later if explicitly allowed
```

But they must not be the only source of truth.

## Correct LLM role

LLMs may help with:

```text
- classifying unknown nodes
- suggesting which inputs may be user-editable
- summarizing what the workflow appears to do
- identifying likely output type: image, video, audio, file, text, unknown
- generating human-readable warnings
- suggesting UI grouping labels
- explaining compatibility issues
- producing a draft analysis report
```

LLMs must not be trusted alone for:

```text
- final patch_targets
- destructive workflow changes
- deleting nodes
- rewriting workflow structure
- deciding that a model/custom node should be auto-installed
- deciding that output is image-only
- bypassing deterministic validation
```

## Recommended architecture

Use a hybrid analyzer:

```text
Rule-based analyzer
  = deterministic, safe, schema-based, graph-based

LLM-assisted analyzer
  = optional helper for ambiguous/unknown parts

Validator
  = checks the final app_profile.json and patch_targets before export
```

Flow:

```text
1. Parse workflow JSON deterministically.
2. Build graph/node inventory.
3. Run rule-based detection for known node types.
4. Mark unknown or ambiguous areas.
5. Optionally send a limited summary to LLM helper.
6. LLM returns suggestions only.
7. Deterministic validator checks suggestions.
8. Only safe, validated fields become patch_targets.
9. Export workflow.json + app_profile.json.
```

## Why not rely only on LLM?

Because workflow compatibility must be exact.

LLMs can hallucinate.
They may misread node roles.
They may infer editable fields that are not safe.
They may produce invalid JSON.
They may miss edge cases.

Structured-output research also shows that generating valid schema-conforming JSON is a real reliability problem for language models, so even JSON-looking LLM output must be validated strictly.

So the project must treat LLM output as:

```text
advice / suggestion / explanation
```

not as:

```text
final authority
```

## Where LLM can help most

The best use cases are ambiguous cases.

Examples:

```text
- Unknown custom node class type.
- Workflow has many custom nodes and no obvious output node.
- Node names are unusual but inputs suggest prompt/seed/output behavior.
- Video or audio workflow uses nodes the rule-based analyzer does not know yet.
- Need a human-readable explanation of what is missing.
```

## LLM input should be limited

Do not send the entire workflow blindly if not needed.

Preferred LLM input:

```text
- list of node ids
- class_type values
- input names and primitive values
- link structure summary
- output candidate nodes
- known analyzer findings
- unknown analyzer findings
```

Avoid sending:

```text
- huge raw workflow if summary is enough
- private file paths when not needed
- generated images/audio/video
- secrets or tokens
```

## LLM output should be structured

If LLM is used, require strict JSON-style output such as:

```json
{
  "suggested_editable_fields": [],
  "suggested_output_types": [],
  "unknown_node_explanations": [],
  "warnings": [],
  "confidence": "low|medium|high"
}
```

Then validate it before using it.

## Local model benefits

Using Ollama/Gemma-like local models may help because:

```text
- workflow data can stay on the user's machine/server
- no external API key is required
- it may work inside the RunPod/ComfyUI environment
- analysis can happen near the workflow
```

## Local model risks

```text
- RunPod GPU/VRAM may be busy with ComfyUI generation
- running an LLM may increase cost and memory use
- local models may be weaker than remote models
- structured JSON output may need validation/retry
- installation/setup adds complexity
```

## MVP decision

For MVP, do not require Ollama/Gemma.

MVP should work with:

```text
rule-based analyzer only
```

LLM-assisted analysis should be optional and later.

Reason:

```text
The first milestone must prove that user-provided workflows can be loaded, preserved, exported, imported, and generated safely.
Adding LLM dependency too early makes validation harder.
```

## Future LLM-assisted phase

After MVP validation, consider adding:

```text
- optional local Ollama endpoint setting
- optional model name setting
- Analyze unknown nodes with LLM button
- LLM-generated compatibility summary
- LLM-generated UI grouping suggestions
- LLM-generated warning explanations
```

## Safe analysis modes

Potential future modes:

```text
Safe Mode
- rule-based only
- deterministic
- best for MVP and reliability

Assist Mode
- rule-based + optional LLM help
- better explanations and unknown node guesses
- still validated before export

Debug Mode
- LLM produces a human-readable analysis report
- app_profile behavior remains deterministic
```

## Safety guardrails

```text
- LLM is optional.
- Rule-based analysis always runs first.
- LLM cannot directly modify workflow.json.
- LLM cannot directly write final patch_targets without validation.
- LLM cannot auto-download models.
- LLM cannot auto-install custom nodes.
- User must be able to export without LLM.
- LLM suggestions must refer only to node ids and fields already found by deterministic parsing.
```

## Product direction

The final product may eventually have two user-facing analysis paths:

```text
Reliable export
- deterministic rule-based analysis
- creates the profile
- required path

Optional AI assist
- explains ambiguous workflows
- suggests labels/groups/warnings
- never required
- never allowed to corrupt the workflow
```

## Product guardrail

```text
The dedicated custom node's analysis is the hardest and most important part.
LLM tools such as Ollama/Gemma can assist, but the core system must not depend on them.
Correctness beats convenience.
```
