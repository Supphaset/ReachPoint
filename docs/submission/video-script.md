# Demo video (3:51)

Recorded on the live English site (https://reachpoint-main.web.app/?lang=en) by `film/demo2026/record.py`: headless
Chrome driven over the DevTools protocol, one fresh demo room per take, narration by the macOS "Samantha" voice. The
safety call is a real Gemini Live call; because headless Chrome has no microphone, the family's answer is a recorded
voice streamed into the call as 16 kHz audio, exactly what a microphone would send. The rules allow 3–4 minutes.

| Time | On screen | Voice-over |
|---|---|---|
| 0:00–0:15 | Title card. | “November 2025, Hat Yai. A mother spent two days on her roof with her four-year-old daughter. Every day, she said, they would pick up my calls, but nobody came. More than a hundred people died in Songkhla province.” |
| 0:15–0:31 | Problem card with sources: the mother's quote (ABC News), one-way requests and no callback contact (The Nation, ThaiPublica), stale pins (The Nation), deaths (ABC News). | “Help requests went into one-way systems. The forms had no way to call people back, and often no location. Once people were safe, volunteers had to take the pins down by hand. So the picture went stale, and people who couldn't type were never in it.” |
| 0:31–0:49 | Overview → replay the flood week; the AI's labelled decisions. | “ReachPoint keeps the picture current, by asking back. This is that real flood week, replayed with real water data and synthetic people. Messages from every channel become households on one map, and every decision is labelled: Gemini, rules, physics, or action.” |
| 0:49–1:14 | Report as a family → type the English message → send → Gemini's quoted facts, the house, the water. | “A family reports. Gemini reads each fact in the sender's own words, finds the house, checks the water there, and flags it urgent: the mother can't walk.” |
| 1:14–1:28 | Demo → Check-in 2 hours later → the family taps “Water rising fast” → the trace updates. | “Then ReachPoint asks back. At every safety check, and with each rain alert, the family gets one short question. One tap, water rising fast, and their urgency and the map update at once.” |
| 1:28–2:16 | Demo → Safety call → the phone rings → Answer → Gemini Live asks with what it knows; the family answers by voice; live captions; the record updates. | “When a family goes quiet, ReachPoint calls them. No app, no typing. Gemini Live asks one simple question at a time, and what they say updates their record, live, with captions on screen.” |
| 2:16–2:28 | Volunteer → map with water, urgent cases by zone. | “Volunteers see where help is missing, on a real map, with the flood layer, the rain outlook, and urgent cases by zone.” |
| 2:28–2:42 | Sectors → B → zone B5: flooded buildings with no request (estimate). | “This team opens the family's zone. Beyond the requests, the flood model counts over a hundred flooded buildings here where nobody has asked for help.” |
| 2:42–3:02 | I'll go here → Boat, 6 seats → ✦ Suggest visiting order (Gemini). | “The crew enters their boat and six seats, and asks Gemini for a visiting order. Gemini weighs every family's needs, water and own words, explains each choice, keeps seats free, and names the streets to check for people who never asked. ReachPoint checks every house and number before the crew sees it.” |
| 3:02–3:10 | Post plan and tell the families. | “The crew posts the plan, and every household in the zone is told: help is planned, not rescued yet.” |
| 3:10–3:25 | Mission: the boat's route over the water; Picked up → Confirm. | “The mission page routes the boat over the flooded streets, from a launch point to each house and back to a truck, and the crew marks each outcome.” |
| 3:25–3:33 | Family phone: the pickup report to confirm. | “The family confirms the pickup, and their request closes itself. No stale pins.” |
| 3:33–3:51 | Closing card: Google Cloud stack and links. | “ReachPoint runs on Google Cloud. Gemini reads, plans and talks. Cloud Run hosts the agents, Firestore keeps every room, and Firebase Hosting serves it, with rate limits and a Gemini budget. A flood picture that stays current, because it asks back.” |
