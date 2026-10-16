# 0017 — Desk depth threshold and emergency evaluation

Date: 2026-10-16. Status: **Accepted user request and threshold** in this chat: simplify water-based boat/truck recommendation and create an emergency guideline; the user selected “50 cm threshold.”

## Context and decision

Existing review left transport and urgency unresolved on sparse reports. Gemini now extracts quoted current numeric water depths; the server validates number/unit conversions and applies a 50 cm boat planning preference. Measured shallow/dry access can suggest a truck; hazards/conflicts need assessment. Field route/vehicle suitability and human approval remain required. This revises the earlier rejection of any numeric preference in [0014](0014-desk-caller-ai-review.md), without authorizing a flood-crossing safety cutoff.

Explicit unmet food, water, regular medication or evacuation needs are Level 2 evidence. Level 1a retains serious medical warning signs, 1b immediate rescue danger, and 3 explicit routine/non-urgent circumstances. Missing information and model failure remain unresolved. Human approval remains required under [0016](0016-automatic-desk-review-and-human-approval.md).

For qualitative reports, waist/chest/head-level water can suggest a boat for conservative planning while measured depth stays unknown. A flooded floor alone cannot. A caller-selected food/evacuation type establishes an active assistance request: the operational default is Level 2 after successful review, overridden by stronger warning signs or explicit routine/non-urgent evidence. This does not confirm absence of danger or clinical assessment. These evaluation choices keep the demo useful for concise forms while preserving human approval.

The user asked whether “first floor flooded” exceeds 50 cm. This phrase cannot establish a numeric depth; no floor-height conversion or default depth is accepted. The UI displays the threshold, any reported depth, missing measurements and the emergency guideline.

## Rationale, alternatives and consequences

The explicit threshold makes numeric examples consistent and reviewable. Quote/unit validation prevents invented depth. Forcing boat/truck from an unmeasured flooded floor was discussed but not selected. This remains a synthetic planning policy, not a validated operational/clinical protocol. Original records stay unchanged; AI revisions retain history and preserve human corrections.

Affected documents: [evaluation guideline](../designs/desk-review-guideline.md), [requirements](../product/requirements.md), [API contract](../../contract/api.md), [decision index](README.md).
