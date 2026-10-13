# 0013 — Caller tracking page and demo controls

Date: 2026-10-13. Status: **Accepted by the user** in the caller-page chat: remove “หากกลายเป็นเหตุฉุกเฉิน โทร 1669”, add an outstanding click-to-copy tracking link, use the four listed steps, and add a mock button to show each next step.

## Decision

The tracking page shows:

1. รับคำขอแล้ว
2. ตรวจสอบรายการ
3. ทีมงานกำลังช่วยเหลือ
4. ได้รับการช่วยเหลือ

A prominent button copies the private tracking URL, with success feedback and a selectable-link fallback if the browser refuses clipboard access. The link contains the request token and the API/language parameters, without demo-preview state.

Clearly labelled demo controls advance through the four steps, restart the preview, and return to the actual status. They change only local presentation, persist while the page polls for live status, and make no API writes. The final step asks whether help was received, with exactly Yes and No responses. It remains unconfirmed until Yes is selected. A volunteer completion report opens this question without confirming receipt. Demo responses are local previews; real responses are saved through the private status link.

## Implementation and validation

The tracking page is `web/src/features/resident/StatusPage.tsx`; the labels are in `web/src/i18n/strings.ts`. The caller submission receipt uses the same four step labels and also removes the matching emergency footer. Changes are verified through the frontend build, existing progress-component checks and browser interaction. The request schema stays unchanged. A token-scoped receipt-response endpoint stores each real Yes/No answer and its timestamp separately from volunteer progress and the request table. It does not close allocations or change quantities.

## Follow-up: receipt question and completion times

The user clarified that “ได้รับการช่วยเหลือ” should ask the caller whether help was actually received, specified “just yes and no”, and requested completion times for each step. A Yes response records confirmed receipt and its completion time; No records that help has not arrived and leaves receipt unconfirmed. Responses retain history and retries do not duplicate an event.

Step times come from the original report's `receivedAt`, its `reviewedAt`, the recorded completion of the volunteer visit, and the caller's Yes timestamp. Unknown historical completion times stay unknown. Times are shown in Asia/Bangkok. Demo times are labelled examples; final completion appears only after demo Yes and never writes to the API.
