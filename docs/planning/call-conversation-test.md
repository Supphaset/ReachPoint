# Call conversation review script

Date: 2026-10-13. Manual review for the local `/callers?data=api` demo. Use invented households and places only. Chat and Gemini Live voice share the same extraction, question order, location choices, read-back and confirmation rule. The 15 shared columns are in [decision 0012](../decisions/0012-shared-caller-schema.md).

## Before each conversation

1. Open `/callers?data=api` and choose **New conversation**. For voice, start hands-free voice and allow the microphone.
2. Watch the information sidebar as answers arrive. A missing count must show unknown, not zero. Corrections must replace the old value.
3. Check that `help_requests` has no row for this conversation before confirmation. The assistant must not say a team is assigned or give an arrival time.
4. Review the complete summary. In chat, use **Confirm and send to coordinator**. In voice, say **ยืนยันส่งคำขอ** after the summary. Only then should one report and one `help_requests` row exist.

To inspect the local database from the repository root, note the count before and after confirmation, then use the report ID shown by the app:

```sql
SELECT COUNT(*) FROM help_requests;

SELECT report_id, channel, phone_number, type, people_details,
       n_children, n_elders, n_pets, location, coordinates,
       location_details, water_level, situation_details,
       emergency_detail, other_details
FROM help_requests WHERE report_id = 'R-001';
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

Expected result: the summary includes every field, and the row is created only after confirmation. The report remains awaiting coordinator review.

## 2. Chat: one answer at a time, unknowns and a correction

| Turn | Caller types | Next assistant behavior to review |
|---|---|---|
| 1 | น้ำท่วม มีคนรอความช่วยเหลือ | Ask whether food or evacuation is needed, then ask for a reachable phone number; use synthetic `0000000000`, then answer the people questions |
| 3 | มีผู้ใหญ่ 1 คนกับเด็ก 2 คน รวม 3 คน | Ask for child, elder and pet counts that remain unknown |
| 4 | เด็ก 2 คน ไม่ทราบจำนวนผู้สูงอายุ ไม่มีสัตว์เลี้ยง | Ask for location; `n_elders` stays unknown and `n_pets` becomes 0 |
| 5 | อยู่ที่อาคารสมมติ B เขต P-B | Ask for additional location detail, or show optional place candidates |
| 6 | ไม่มีรายละเอียดตำแหน่งเพิ่ม | Ask water level |
| 7 | ไม่ทราบระดับน้ำ | Ask about the current situation |
| 8 | น้ำยังขึ้นอยู่ ทุกคนอยู่ชั้นบน | Ask about injury, immediate danger and needed help |
| 9 | ไม่มีคนเจ็บ ต้องการอาหาร | Ask whether there is anything else |
| 10 | ไม่มีข้อมูลอื่น | Show the complete summary, with **no saved report yet** |
| 11 | แก้ไข เด็กมี 1 คน ไม่ใช่ 2 | Show a revised summary before confirmation |

Already answered fields should be skipped. Saying “ไม่ทราบ” should leave `n_elders` and `water_level` as `NULL`; saying “ไม่มีสัตว์เลี้ยง” should set `n_pets` to `0`. The later correction should make `n_children = 1` in the sidebar, final summary and saved row. If the location changes after a candidate was selected, old coordinates must be cleared until the new place is chosen.

Before pressing confirm, verify there is no new `help_requests` row. After confirming, verify there is exactly one row and a usable status link.

## 3. Voice: hands-free collection and place choice

Start a new conversation and enable voice. The assistant should speak the current question without requiring a typed or spoken trigger. Speak the same kind of synthetic answers as scenario 1, pausing after each answer. The assistant should speak the server's next question, not invent a new field or dispatch promise. Check that the sidebar updates after each spoken turn. Switching from chat to voice midway should start by speaking the pending question or summary, then continue the same session.

If the app finds numbered location candidates, the assistant should read them aloud. Say **เลือก 1** to select the first, or **ไม่ใช่ทั้งหมด** to reject them. It must not select a place without your choice. If Pinpoint is unavailable, mark this location-choice step as skipped and continue with the reported location text.

When the assistant reads the complete summary, correct one detail by voice and listen to the revised summary. Say **ยืนยันส่งคำขอ** (or **ยืนยันส่งคำขอค่ะ**) only after it is correct. Expected result: `channel = 'voice'`, one `help_requests` row with the corrected values, and one report/status link. Stopping voice before confirmation must leave no row.

## 4. Urgent situation: ask location first

Start a new chat or voice conversation with: “มีคนหายใจลำบาก น้ำกำลังขึ้นเร็ว”. The assistant should give emergency contact guidance and ask for the location first. Answer “อาคารสมมติ C เขต P-C”, then clarify the emergency and who needs help. After the urgent location and situation questions, it must collect a phone number and type before offering an early summary. Pet count and other optional fields can remain unknown. Unknown values stay `NULL`. Confirmation is still required before saving; the assistant must not claim a team is on the way.

## 5. Retry and restart

Confirm one synthetic request, then refresh `/callers?data=api` and reopen its status link. The report ID and summary should remain. Repeating the same confirmation after a reconnect must not create a second report or `help_requests` row. Restarting the local server with the same `REACHPOINT_DB_PATH` should preserve the confirmed row and status link.

## 6. Structured form

Choose **Form**. Check the same 13 editable details as the chat/voice sidebar, with no caller-name field. `report_id` is generated after submission and `channel` is `form`. Enter a synthetic phone number and select Food or Evacuation; submitting without either must fail. Enter the synthetic values from scenario 1, use zero for a known absence, and leave an unknown value blank. Review the fields and click **Confirm and send to coordinator**. Verify one `help_requests` row with exactly the 15 listed columns. Repeating a submission for the same session must not create a second row. Switching from chat to Form should populate the extracted details.

## Review notes

Record any missed field, repeated question, incorrect zero, wrong location choice, cut-off spoken summary, or premature save with the exact scenario and turn. Gemini extraction can vary, so compare the final sidebar and SQLite row with the caller's actual words; never treat an AI inference as a reported fact.
