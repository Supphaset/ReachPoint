# Call conversation review script

Date: 2026-10-15. Manual review for the local `/callers?data=api` demo. Use invented households and places only. Chat and Gemini Live voice share the same extraction, question order, location choices, read-back and confirmation rule. The 15 shared columns are in [decision 0012](../decisions/0012-shared-caller-schema.md).

## Before each conversation

1. Open `/callers?data=api` and choose **New conversation**. For voice, start hands-free voice and allow the microphone.
2. Watch the information sidebar as answers arrive. A missing count must show unknown, not zero. Corrections must replace the old value.
3. Check that `callers` has no row for this conversation before confirmation. The assistant must not say a team is assigned or give an arrival time.
4. Review the brief summary. In chat, use **Confirm and send to coordinator**. In voice, say **ยืนยันส่งคำขอ** after the summary. Only then should one report and one `callers` row exist.

To inspect the local database from the repository root, note the count before and after confirmation, then use the report ID shown by the app:

```sql
SELECT COUNT(*) FROM callers;

SELECT report_id, channel, phone_number, type, people_details,
       n_children, n_elders, n_pets, location, coordinates,
       location_details, water_level, situation_details,
       emergency_detail, other_details
FROM callers WHERE report_id = 'R-001';
```

The ID above is an example; use the ID shown by the app. A selected Pinpoint place may supply `coordinates`; otherwise it should remain `NULL`.

## 1. Chat: all fields in a short conversation

Start with this synthetic message:

> เบอร์ติดต่อ 0000000000 ต้องการอพยพ อยู่กับผู้ใหญ่ 2 คน เด็ก 1 คน ผู้สูงอายุ 1 คน และสุนัข 2 ตัวที่อาคารสมมติ A เขต P-A ชั้นสอง ทางเข้าฝั่งตะวันออก น้ำสูงถึงเอวและยังเพิ่มขึ้น ตอนนี้ทุกคนอยู่ชั้นสอง ไม่มีใครบาดเจ็บ แต่ต้องการเรือ ไม่มีข้อมูลอื่นแล้ว

Answer any follow-up with only the missing fact; do not invent a coordinate. Review the sidebar and summary before confirming.

| Field | Expected reported value |
|---|---|
| `channel` | `chat` |
| `phone_number` | `0000000000` (synthetic placeholder only) |
| `type` | `evacuation` |
| `people_details` | Contains two adults, one child and one older person; does not add the pets to the people count |
| `n_children`, `n_elders`, `n_pets` | `1`, `1`, `2` |
| `location` | อาคารสมมติ A เขต P-A |
| `location_details` | ชั้นสอง ทางเข้า ฝั่งตะวันออก |
| `coordinates` | `NULL` unless the caller chooses a returned location candidate |
| `water_level` | เอว |
| `situation_details` | Water rising; everyone on the second floor |
| `emergency_detail` | No injuries reported; boat requested |
| `other_details` | Caller said there is nothing else |

Expected result: the brief summary includes the five form fields and any volunteered extra details, and the row is created only after confirmation. The report remains awaiting coordinator review.

## 2. Chat: a short conversation and one optional prompt

| Turn | Caller types | Next assistant behavior |
|---|---|---|
| Opening | — | Ask location; a Google Maps link or place description is accepted |
| 1 | อยู่ที่อาคารสมมติ B เขต P-B | Ask food or evacuation; if place candidates appear, choose or reject them first |
| 2 | ต้องการอาหาร | Ask a reachable phone number |
| 3 | 0000000000 | Ask one optional question about people and how high the water is |
| 4 | ข้าม | Show the brief summary; **Skip details** does the same without typing |
| Correction | แก้ไข เบอร์โทร 0000000001 | Update the summary without restarting optional questions |

If the caller answers the optional prompt with only people details, situation details remain unknown and the summary appears immediately. The one optional prompt must explicitly ask how high the water is when unknown, even if a general situation was already supplied. Do not ask separate counts, access, injury or other-detail questions. If all five fields and water level arrive together, show the summary directly. Declared urgent danger skips the optional prompt, but location, phone and help type are still needed. Unresolved contradictions and caller-selected location candidates may need clarification. No missing count becomes zero. Supplied water, danger, access and count facts remain visible in the summary/sidebar and saved record.

On sending a chat answer, the caller bubble must appear immediately with a reading indicator. The reply arrives through SSE; an interrupted turn must show a retryable error and keep the draft, with the same turn ID on retry.

Before confirmation, there must be no new `callers` row. After confirmation, there is exactly one row and a usable status link. Reconnect while the optional prompt is pending, then skip or answer it: it must not repeat. Corrections after skipping must not restart it.

## 3. Voice: hands-free collection and place choice

Start a new conversation and enable voice. The assistant should speak the current question without requiring a typed or spoken trigger. Speak the same kind of synthetic answers as scenario 1, pausing after each answer. The assistant should speak the server's next question, not invent a new field or dispatch promise. Check that the sidebar updates after each spoken turn. Switching from chat to voice midway should start by speaking the pending question or summary, then continue the same session.

If the app finds numbered location candidates, the assistant should read them aloud. Say **เลือก 1** to select the first, or **ไม่ใช่ทั้งหมด** to reject them. It must not select a place without your choice. If Pinpoint is unavailable, mark this location-choice step as skipped and continue with the reported location text.

When the assistant reads the brief summary (without enumerating unknown extra fields), correct one detail by voice and listen to the revised summary. Say **ยืนยันส่งคำขอ** (or **ยืนยันส่งคำขอค่ะ**) only after it is correct. Expected result: `channel = 'voice'`, one `callers` row with the corrected values, and one report/status link. Stopping voice before confirmation must leave no row.

## 4. Urgent situation: ask location first

Start a new chat or voice conversation with: “มีคนหายใจลำบาก น้ำกำลังขึ้นเร็ว”. The assistant should give emergency contact guidance and ask for the location first. Answer “อาคารสมมติ C เขต P-C”, then supply the requested help type and phone number. It must offer an early summary retaining the stated danger without asking the optional people/situation question. Pet count and other optional fields can remain unknown. Unknown values stay `NULL`. Confirmation is still required before saving; the assistant must not claim a team is on the way.

## 5. Retry and restart

Confirm one synthetic request, then refresh `/callers?data=api` and reopen its status link. The report ID and summary should remain. Repeating the same confirmation after a reconnect must not create a second report or `callers` row. Restarting the local server with the same `REACHPOINT_DB_PATH` should preserve the confirmed row and status link.

## 6. Structured form

Choose **Form**. Check exactly five inputs: phone number, help type, Google Maps location link, people details, and situation details. `report_id` is generated after submission and `channel` is `form`. Enter a synthetic phone number, select Food or Evacuation, and paste a synthetic Google Maps link; all three are required. People and situation details may be blank. Review the fields and click **Confirm and send to coordinator**. Verify one `callers` row with exactly the 15 stored columns, omitted details unknown, and the original link preserved. Repeating a submission for the same session must not create a second row. Switching from chat to Form should populate the extracted details; spoken locations must be replaced with a Maps link before form submission.

## Review notes

Record any missed field, repeated question, incorrect zero, wrong location choice, cut-off spoken summary, or premature save with the exact scenario and turn. Gemini extraction can vary, so compare the final sidebar and SQLite row with the caller's actual words; never treat an AI inference as a reported fact.
