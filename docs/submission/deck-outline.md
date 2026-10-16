# Ten-slide submission outline, v2

16 Oct 2026. Outline for the PDF deck. Screenshots come from the deployed site (planned captures are named). Keep
the "synthetic people" label visible; replace pending links only when verified.

| # / Title | One message | What is on it | Speaker note |
|---|---|---|---|
| 1 · Promise | A flood picture that builds itself from what people say. | `01-flood-board.png`: satellite map with the water layer, household dots, the phone. | Prototype, synthetic people, real water data. |
| 2 · Problem | Messages pile up; the picture never forms. | Hat Yai, Nov 2025: tens of thousands of requests across phone, Facebook, LINE; duplicates and silence ([sources](../research/real-rescue-practice.md)). | Requests are not unique people. No operator interviews yet. |
| 3 · What it does | Victims talk; agents build the map; households are told. | The loop: victim → intake agent → building → households → water level → plans → messages. | Volunteers only post one-line plans; nobody enters data. |
| 4 · The judge's minute | Report a case and watch it land. | `04-chat-house.png`: chat with quoted facts; the house on the satellite map; "already known, not counted twice". | Neighbour questions find the exact building on the map. |
| 5 · Physics + people | The simulation is the first guess; reports correct it. | `05-sim-vs-reports.png`: Physics only vs Simulation + reports; "reports say 0.6 m deeper (blocked drains)". | Diffusive shallow water on FABDEM 30 m, canal at gauge X.44, IMERG rain. Not a hydraulic study. |
| 6 · Trust | Not every report is right. | Doubtful labels, leave-one-out check, ranges for possible duplicates, privacy rule. | Urgent requests are never held back for checks. |
| 7 · Outreach | The agents start the conversation. | Timeline: early warning where the simulated water spreads next, rain and river alerts, morning check, lost contact. | Messages are simulated in the app; SMS/LINE/calls not connected. |
| 8 · Evaluation | Measured on a week of synthetic messages with planted mistakes. | Table from [v2-results](../eval/v2-results.md): depth at households 0.14 m; 13/14 wrong reports caught, 3% false; 1% wrong merges; 88% neighbour buildings. | The truth is the simulation plus local effects: shows how physics and reports combine, not field accuracy. |
| 9 · Architecture | Google Cloud end to end. | Cloud Run (web + API), Gemini on Vertex AI (reader, plan line), Earth Engine (Sentinel-1, FABDEM), Google Open Buildings, Maps JS, Pinpoint. | One instance, in-memory demo rooms. |
| 10 · Impact & next | Start with one district drill. | Who runs it (foundation or provincial disaster office), cost per 1,000 messages, next steps: real Pinpoint, SMS/LINE channels, responder drill, persistence and privacy. | No adoption or measured time savings yet. |
