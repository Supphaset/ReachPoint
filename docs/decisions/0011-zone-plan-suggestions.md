# 0011 — Zone plan suggestions

Date: 2026-10-18. Status: accepted, explicit owner instruction in this task.

The owner found the separate free-text copilot page random because it lacked team context. Replace that screen
with a suggestion action inside the zone plan after vehicle, seats and arrival time. The server supplies the current
room’s waiting households, family words, water, access, other plans, shelters and unheard model exposure.

Use one structured Gemini generation with the existing model fallback and budget machinery. Deterministic checks
constrain IDs, quotes, capacity, access, street names and narrative numbers. Rules provide an available fallback.
The team reviews and edits the suggestion before posting; the saved order drives its mission. Exposure uses flooded
building counts, with household ranges explicitly estimated. No new provider or autonomous assignment is approved.

The separate copilot screen is removed. Its backend stays for existing callers/tests and shared validation helpers.
Affected contract and UI: POST zone suggest, POST plans with optional order, zone mission read, volunteer navigation.
Existing privacy, synthetic-data and rescue-state constraints continue; the requested evidence quotes are shown in
the editable suggestion. This decision approves this bounded implementation, not deployment or spending.
