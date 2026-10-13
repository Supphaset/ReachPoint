# Judge Q&A

Current answers, 13 Oct 2026. The [morning judge reports](../reviews/judge-2026-10-13.md) and [Codex review](../reviews/codex-judge-2026-10-13.md) prompted these questions; their older implementation descriptions are not current evidence.

1. **Show the agent doing something rules can't.**
   Show a same-landmark, ambiguous-household request: ADK can select candidate lookup and propose a caller-specific clarification instead of linking it. This is implemented intent, not measured superiority: the recorded agent run fell back entirely; show a trace labelled `agent` before claiming a live demonstration. [Agent](../../api/ai/triage.py), [results](../eval/results.md).

2. **Can voice submit by itself?**
   The browser voice interface can submit after the caller says the exact confirmation phrase and the server checks that the session is ready. It cannot submit autonomously, assign a team or promise arrival; there is no telephone line. [Voice transport](../../api/intake/live_voice.py), [conversation](../../api/intake/conversation.py).

3. **Why trust Gemini's facts?**
   Treat them as proposals: extraction checks caller quotes, denied dangers and counts, then a coordinator reviews. A valid quote proves provenance, not truth or correct interpretation; chat fields do not each carry quotes, and ranking uses a fixed safety rule. [Extraction](../../api/intake/extract.py), [triage](../../api/ai/triage.py).

4. **What happens on restart, or if Gemini fails?**
   Restart loses in-memory requests, commitments and conversations; demo rooms restart from synthetic seed data. Extraction/triage can use labelled keyword/rules fallbacks; chat may fail a turn and voice may become unavailable, so this is not a durable emergency service. [Rooms](../../api/server/rooms.py), [conversation](../../api/intake/conversation.py), [results](../eval/results.md).

5. **Who runs it, and what does it cost?**
   Proposed operator: a volunteer rescue foundation or provincial disaster office, using manual handoffs from hotline/LINE reports. Estimated cloud cost is $70–130/month for 1,000 requests under stated assumptions; no operator, payer or funding is confirmed, and excluded costs are listed. [Business case](../product/business-case.md).

6. **How is this different from thaifloodhelp?**
   thaifloodhelp already describes Gemini extraction, human review, duplicates and mobile use. Our demo focuses on unchecked quiet segments, withdrawing failed-boat estimates and quote-checked request facts; competitor features we could not establish stay unknown. [Comparison table](../research/competitors.md#how-reachpoint-differs).

7. **Is Thai voice reliable?**
   Thai/English browser voice is implemented, but Thai audio accuracy, accents, noise and confirmation reliability have not been measured. The 36 intake cases are text cases, not voice validation; use synthetic calls and corrections in the next drill. [Voice](../../api/intake/live_voice.py), [evaluation method](../eval/README.md).

8. **How do you protect exact locations?**
   Views keep exact pickup points for the desk and the team holding the job; family status omits exact points and medical notes. These are demo view boundaries, not authenticated production access controls: there is no sign-in, and only synthetic locations are authorized. [Team views](../../api/views/team.py), [status view](../../api/views/resident.py), [data handling](../collaboration/data-handling.md).

9. **Why not Firestore?**
   The current bounded demo uses one service and an in-memory store; Firestore and sign-in remain planned. Local SQLite is an open, unmerged PR (#21); neither durability nor multi-instance correctness should be claimed for this version. [Architecture](../../README.md#architecture-what-actually-runs), [deploy script](../../scripts/deploy.sh).

10. **What evidence shows this helps, including people who never called?**
    We have 36 intake and 12 triage synthetic cases, three Gemini runs, 30.6% intake fallback and 100% agent fallback; successful Gemini readings are scored separately. Quiet-zone discovery is a synthetic workflow, not measured rescue impact or proof of population estimates; the proposed drill measures coverage and review errors. [Results](../eval/results.md), [pilot](../product/business-case.md#first-pilot-a-tabletop-drill).
