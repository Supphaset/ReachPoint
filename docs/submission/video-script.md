# Video script, v2 (2:55, strictly under 3:00)

Record on the **deployed URL** at 1440 × 900, in a fresh demo room (press **Reset**), in Chrome with the microphone
allowed. The voice-over is in English; Thai stays on screen with English captions. Rehearse once and time it. If a
take runs over 2:55, cut the [optional] lines. Numbers marked ⟨eval⟩ come from the latest `docs/eval/v2-results.md`.

**The line to build around:** *"A flood picture that builds itself from what people say."*

| Time | On screen (exact clicks) | Voice-over |
|---|---|---|
| 0:00–0:12 | The judge page at 25 Nov 06:00. Slow zoom on the satellite map with the water layer | "November 2025, Hat Yai. Tens of thousands of calls for help. The same family posted ten times; others never at all. Nobody could say who was in which street, or how deep the water was there." |
| 0:12–0:30 | **Play the flood**. Water spreads from the hills and canals; dots appear; the households counter climbs | "ReachPoint starts with physics: a flood model of the whole basin, on real terrain and real rain, checked against the real river gauge. Then every message lands on it." |
| 0:30–0:58 | Top left: the house scene, water at the waist. Press **📞 Call** and speak Thai: *"น้ำถึงเอวแล้ว อยู่กับแม่ แม่เดินไม่ได้ บ้านเลขที่ 52/9 ถนนเพชรเกษม ซอย 2"*. Gemini answers by voice; **Understood** chips with quotes; the house lights up on the map and the scene becomes **Your house** | "A daughter calls for help. Gemini Live listens and speaks Thai, but our intake agent decides every question, and every fact keeps her own words. Her address becomes a building, and this is the water at her house now." |
| 0:58–1:22 | Say *"บ้านทางทิศตะวันออกมียายอยู่คนเดียว"*. The satellite picture appears in the chat with the house outlined orange. Tap **ใช่ หลังนี้**. **New household added** (or **Already known · not counted twice**) | "She mentions a neighbour. The agent shows that house on the satellite picture: is it this one? Yes. A grandmother nobody had heard from is now on the map, and never counted twice." |
| 1:22–1:40 | The agent's shelter line ("the way to the nearest shelter is 1.1 m deep: don't walk now"). Map: green shelter squares | "Can she leave on her own? The agent checks the water all the way to the nearest shelter. Here it's too deep, so it tells her to go upstairs, and tells the boat teams." |
| 1:40–1:58 | Press **Rain alert**. AI activity: *"the flood model expects at least 10 cm more water at ⟨n⟩ homes … warned first: families with someone who can't walk"*. The phone shows its own expected rise | "Heavy rain is coming. The flood model works out, house by house, how much the water will rise and when, and warns those who can't walk first." |
| 1:58–2:30 | **Volunteer pages →**: *Where help is missing* (hotspots), then a family's **case**: every message with its words, why it was merged, water at the house, neighbours on the compass. **Plan a trip** → post → the zone is outlined on the map. Tap **We picked them up** | "Volunteers see where help is missing, street by street, and each family's whole story with the evidence. They post where they're going; families there are told. One tap after the visit closes the loop." |
| 2:30–2:45 | `docs/eval/v2-results.md` table, zoomed | "On a full week of synthetic messages with planted mistakes: ⟨eval⟩ households counted against ⟨eval⟩ real families, water at a household within ⟨eval⟩ on average, and ⟨eval⟩ of the wrong reports caught." |
| 2:45–2:55 | Architecture diagram (README), then the line, live URL and GitHub URL | "Gemini and Gemini Live, Earth Engine, Google Open Buildings, Cloud Run. Real water, synthetic people. ReachPoint: a flood picture that builds itself from what people say." |

## Before recording

- [ ] The reader label under the first answer says **Gemini** (not "rules"). On Cloud Run, `REACHPOINT_LLM` must be unset or `gemini`.
- [ ] **📞 Call** connects within 3 s and speaks Thai; if not, type instead and say "by voice or text".
- [ ] The satellite map, the water layer and the house scene load within 5 s on the deployed site.
- [ ] Use the synthetic address above; never show a real name or phone number.
- [ ] Fill the ⟨eval⟩ numbers from the latest `docs/eval/v2-results.md` before recording.
- [ ] Final length 2:55 ± 5 s, checked in the editor. The limit is strictly under 3:00.
