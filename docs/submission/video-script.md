# Video script (2:50, strictly under 3:00)

Record on the **deployed URL**, not localhost. Record the screen at 1440 × 900, with the phone screens in `/demo`. Use a
fresh demo room (**New room**). The voice-over is in English; Thai stays on screen with English captions.
Rehearse once and time it. If a take runs over 2:55, cut the [optional] lines.

**The line to build around:** *"ReachPoint turns flood reports, and gaps in reporting, into accountable rescue work,
with status families can trust."*

| Time | On screen (exact clicks) | Voice-over |
|---|---|---|
| 0:00–0:12 | Home page, Thai. Slow zoom on the headline | "In the Hat Yai flood of November 2025, more than twenty thousand people asked for help in one week. The government's own review found no shared picture: no callback numbers, no locations, no record of who was already reached." |
| 0:12–0:20 | Cut to `/demo`, EN. Hover over the three phones | "ReachPoint is one app with three roles: the person asking for help, a coordinator, and volunteer boat teams." |
| 0:20–0:50 | Left phone, Thai: **Talk instead of typing** (mic). Say a Thai request out loud. The assistant asks one missing thing. Tap **Share your location**, then **Pick on the map**; the readout shows "ใกล้ ตลาดกิมหยง"; tap **ใช้จุดนี้**. Say **"ยืนยันส่งคำขอ"** | "A grandmother's family calls in Thai. Gemini Live listens and asks only for what's missing. It never asks for a name first. They pin their spot instead of describing it. Nothing is sent until they confirm the summary out loud, and the server checks that phrase." |
| 0:50–1:12 | Middle screen: the new request. Highlight the quoted facts, then the line **What the agent did: looked for similar cases → asked a question** | "On the desk, every fact Gemini proposes carries the caller's own words. If they can't be quoted, they're dropped. A triage agent built with Google's ADK checks for duplicates using five allowed tools. Same temple isn't the same family, so it suggests a question instead of merging. A person approves." |
| 1:12–1:25 | Approve (sticky footer). Right phone: **รับงาน** (take job), then set an arrival window. Left phone: the status page shows the window | "A team takes the whole family in one tap. The family sees an honest estimate, not a promise." |
| 1:25–1:45 | `/demo` **2 · The boat breaks down**. Desk: **Mark S1 unavailable**, with a reason and the next update time. All three screens change | "Then the boat's engine fails. Every arrival time it carried is withdrawn on every screen, the unfinished work goes back on the list, and the family sees who will update them next. No stale promises." |
| 1:45–2:15 | `/demo` **3 · The map is quiet**. Desk **Quiet zones**: B-4 has no calls, marked *not checked*. **Publish zone mission**. Team: **Take segment**, then **Send field report**: "Elderly couple on the 2nd floor, one bedridden". Desk: the new reviewed case | "But the most dangerous places can be the quiet ones. Zone B-4 had no calls, so ReachPoint never shows it as safe. It shows 'not checked'. A team is sent street by street. They find an elderly couple who never called, and that report becomes a rescue case." |
| 2:15–2:32 | `docs/eval/results.md` table (zoomed), then a tricky message on the desk: "Nobody is unconscious, we are 2 adults", with no danger flag | "We measure it. Across 36 labelled Thai and English requests, Gemini missed no real dangers and raised no false alarms. Our checks catch a quote that doesn't support the fact, like 'nobody is unconscious'. Every failure is published." |
| 2:32–2:45 | Architecture diagram (README) | "It runs on Google Cloud: Cloud Run, Gemini and Gemini Live on Vertex AI, an ADK agent, OR-Tools for sharing boats fairly, and real Sentinel-1 flood maps from Earth Engine. The people are synthetic; the flood is real." |
| 2:45–2:50 | The line, the live URL and the GitHub URL | "ReachPoint turns flood reports, and gaps in reporting, into accountable rescue work, with status families can trust." |

## Before recording

- [ ] The deployed `/api/call/config` returns `chat: true, voice: true`.
- [ ] The desk shows `What the agent did (Gemini)` on a new request. If it says "rules", fix that before recording.
- [ ] The Thai voice call works on a phone browser. Keep a 20-second backup clip.
- [ ] Use made-up households and addresses only. Never show a real name or phone number.
- [ ] Update the eval numbers on screen from the latest `docs/eval/results.md` (the Vertex run).
- [ ] Final length is 2:50 ± 5 s, checked in the editor. The limit is strictly under 3:00.
