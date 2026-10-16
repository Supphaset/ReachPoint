# Video script, v2 (2:50, strictly under 3:00)

Record on the **deployed URL** at 1440 × 900, in a fresh demo room (press **Reset**). The voice-over is in English;
Thai stays on screen with English captions. Rehearse once and time it. If a take runs over 2:55, cut the [optional] lines.

**The line to build around:** *"A flood picture that builds itself from what people say."*

| Time | On screen (exact clicks) | Voice-over |
|---|---|---|
| 0:00–0:12 | The judge page at 25 Nov 06:00. Slow zoom on the satellite map with the water layer | "November 2025, Hat Yai. Tens of thousands of messages for help: phone calls, Facebook posts, LINE. The same family posted ten times; others never at all. Nobody could say how many people were in which street, or how deep the water was there." |
| 0:12–0:35 | **Play the flood**. The water spreads from the canal as the gauge line rises past the bank; dots appear; the households counter climbs | "ReachPoint starts with physics. A flood simulation on the real terrain, driven by the real river gauge and rainfall. Then every message lands on it: victims, posts, bulletins, satellite passes. Watch the picture sharpen as people talk." |
| 0:35–1:10 | Left phone, Thai. Type or hold the mic: *"น้ำถึงเอวแล้ว อยู่กับแม่ แม่เดินไม่ได้ บ้านเลขที่ 52/9 ถนนเพชรเกษม ซอย 2"*. Point at **Understood** chips with quotes. The house lights up yellow on the satellite map | "A daughter asks for help in Thai. The AI agent reads every fact with her own words, and asks only what's missing. Her address becomes a building on the map." |
| 1:10–1:35 | Agent: *"Is anyone in the house on your left?"* Answer *"มียายอยู่คนเดียว"*. The neighbour's house lights up; **Already known · not counted twice** (or **New household added**) | "Then it asks about the neighbours, the way people talk: left, right, across the street. The system finds that exact house. If it already reported, it isn't counted twice. If not, a family nobody had heard from is now on the map." |
| 1:35–2:00 | Zone card: **Most likely ≈ 1.2 m, likely 0.9–1.4**, sources list, **"reports say 0.6 m deeper than simulated (likely blocked drains)"**. Switch **Physics only ↔ Simulation + reports** | "Not every report is right. Each one is checked against the physics and against its neighbours. Where people agree, they correct the model: here the water is deeper than the simulation, probably blocked drains. A report that doesn't fit is marked doubtful, never deleted." |
| 2:00–2:20 | Volunteer box: *"เรือเรา 8 ที่ จะเข้า B-3 ราวบ่ายสอง"* → **Post plan**. The phone shows **"A boat team plans to come about 14:00"**. Press **Rain alert**: a safety check arrives on the phone | "Volunteers just post where they're going. Every household in that zone hears about it. When rain is coming, or the river rises, the agents check on people first, and anyone who stops answering is flagged as lost contact." |
| 2:20–2:38 | `docs/eval/v2-results.md` table, zoomed | "We measure it on a full week of synthetic messages with planned mistakes: water depth at a household within 14 centimetres on average, 13 of 14 wrong reports caught, one percent wrong merges." |
| 2:38–2:50 | Architecture diagram (README), then the line, live URL and GitHub URL | "Gemini on Vertex AI, Earth Engine, Google Open Buildings and Cloud Run. Real water, synthetic people. ReachPoint: a flood picture that builds itself from what people say." |

## Before recording

- [ ] The reader label under the first answer says **Gemini** (not "rules"). On Cloud Run, `REACHPOINT_LLM` must be unset or `gemini`.
- [ ] The satellite map and the water layer load within 5 s on the deployed site.
- [ ] Use the synthetic address above; never show a real name or phone number.
- [ ] Update the eval numbers from the latest `docs/eval/v2-results.md` before recording.
- [ ] Final length 2:50 ± 5 s, checked in the editor. The limit is strictly under 3:00.
