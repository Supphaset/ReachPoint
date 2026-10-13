# 0012 — Shared caller-request schema

Date: 2026-10-13. Status: **Accepted by the user** in the caller-page chat: “form chat voice and table should share the same schema. (remove the reporter_name)”, followed by the exact field list below.

## Decision

Form, chat and voice use the same request details and the same `help_requests` table:

```text
report_id
channel
phone_number
type
people_details
n_children
n_elders
n_pets
location
coordinates
location_details
water_level
situation_details
emergency_detail
other_details
```

The server assigns `report_id`. `channel` records `chat`, `voice` or `form`; mixed chat/voice conversations use the latest recorded input mode. Counts are nonnegative integers or unknown; an empty input stays null and an explicit zero stays zero. Caller name is no longer requested, extracted, shown in the field summary or stored in a request column.

## Amendment — phone number and help type, 13 Oct 2026

The user subsequently requested “add phone_number as required field” for sending a follow-up after volunteers visit, and “add type (food or evacuation)”. This expands the original 13-column schema to 15 columns. New submissions in every mode require a caller-provided phone number and one type: `food` or `evacuation`. Chat and Voice ask for missing required fields before confirmation; explicit unknown/declined answers cannot bypass this gate. Immediate-danger location and situation questions still come first.

Phone formatting is normalized to 7–15 digits with an optional leading `+`, preserving leading zeros and supplied country prefixes. No phone verification or message delivery integration is added here. Existing rows keep null for new fields until collected; no contact or need is inferred during migration.

## Implementation and consequences

The shared Python model is in `api/intake/schema.py`; the browser contract is in `web/src/data/call.ts`. Chat and Gemini Live extract these details into a conversation with separate control state. The structured form presents these same fields, prefilled from the latest conversation details, including phone number and help type. Form submission uses the same session confirmation and persistence path, preserving one report per session on retry.

On startup, the local SQLite adapter migrates the former 14-column table, preserving request IDs and all retained column values while removing `reporter_name` and accepting the `form` channel. This revises the original schema in [0011](0011-local-sqlite-interim.md). Historical messages are not rewritten. Deployed Firestore remains separate work.

Affected documents: [requirements](../product/requirements.md), [API contract](../../contract/api.md), [conversation review script](../planning/call-conversation-test.md).
