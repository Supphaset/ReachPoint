# ClearSignal: notice-to-action thought experiment

Date: 2026-10-11. Status: proposed discovery exercise, not an accepted pivot or implementation specification.

## Purpose and limits

Test whether an accessible conversation about an official notice could produce a stronger hackathon demonstration than a general relief dashboard. The intended user is a resident who receives a notice but cannot confidently act on it; a coordinator reviews unresolved barriers.

Everything below is fictional and synthetic: place names, notices, residents, conversations and records. These are authored expected behaviors, not transcripts from a working model, user research, a measured evaluation or emergency instructions. No real service, transport, multilingual accuracy or telephone integration is demonstrated. The [accepted brief](../product/brief.md) and [requirements](../product/requirements.md) remain unchanged.

Hypothesis: the valuable moment is discovering that a resident's apparent understanding conceals a practical barrier, then preserving that barrier when the source information changes. Translation, structured intake and version tracking are useful existing approaches; the product must justify why conversation improves on them.

## 1. Fictional source notice

**N1, version 1 — fictional Cedar District Support Desk**

Published: scenario day 1, 08:00, Asia/Bangkok. Effective: that day only. In this exercise, an operator has checked the notice against the fictional issuer's designated source. This is a scenario assumption, not a implemented verification mechanism.

| Clause | Notice text |
|---|---|
| N1.C1 | Residents of Cedar District may collect drinking-water packs at Cedar Community Hall today from 10:00 to 16:00. |
| N1.C2 | The collection desk is at the ground-floor east entrance. |
| N1.C3 | A representative may collect for another household. Tell staff the household reference if known; if unknown, staff will review the request. |
| N1.C4 | This notice does not provide road conditions, safe routes or a transport service. |
| N1.C5 | Residents who cannot collect may report the obstacle to the support desk. A report does not guarantee delivery or transport. |
| N1.C6 | Updates will be published by Cedar District Support Desk through its designated notice channel. |

Neither packs per household nor wheelchair accessibility is specified. Neither should be invented. Real deployment would need an accountable issuer, a defined verification procedure and an expiry policy; these are open dependencies.

## 2. Three resident conversations

The following interactions are an English screenplay. They make no claim about Thai or other language performance. Phone and chat are proposed channels; this exercise tests conversation content only.

### Scene A — a forwarded notice gives the wrong plan

**Resident A:** “My neighbor sent a picture saying the school. I'll go there at five after work.”

**Assistant:** “The current notice I have says Cedar Community Hall, between 10 and 4 today. Your picture may be a different notice; I can't verify it from that description. Would someone be able to collect during those hours?”

**Resident A:** “No. I work until five and live alone.”

**Assistant:** “Then the hours prevent you from collecting. The notice lets you report that obstacle, but does not promise delivery. May I record a request for the desk to review?”

**Resident A:** “Yes. I still don't know how I'll get the water.”

**Expected proposal:** collection-hours barrier; request for another arrangement; contact preference if supplied; current source N1.C1/C5; conflicting forwarded notice remains unverified. A human reviews the proposal. No delivery commitment, receipt or resolved outcome is recorded.

**Why this could matter:** a yes/no “Did you understand?” question would miss the wrong place, wrong time and inability to collect. A good scripted call could also discover all three; conversational AI must show an advantage on varied phrasing rather than this one scripted example.

### Scene B — understanding the words does not establish access

**Resident B:** “East entrance means the door by the parking lot, right? My father uses a wheelchair. I'll take him there.”

**Assistant:** “The notice says east entrance, but it doesn't identify the parking-lot door or confirm wheelchair access. I can't confirm either. Is your main concern getting into the building, getting there, or both?”

**Resident B:** “Getting into the building. We have transport. Could I collect for him instead?”

**Assistant:** “Yes, the notice allows a representative to collect. If you don't know his household reference, staff can review the request. It doesn't specify the quantity available. Does collecting on his behalf address the access concern, or do you still want the desk to check accessibility?”

**Resident B:** “I'll collect. Please still ask whether the entrance is accessible.”

**Expected proposal:** reported plan to collect as representative; accessibility question for staff; no transport request; household relationship reported, not verified; source N1.C2/C3. No diagnosis or assumption that a wheelchair implies medical urgency. Accessibility remains unknown; the father's need remains open until receipt is confirmed.

**Why this could matter:** tailored clarification avoids recording an unnecessary transport request while exposing missing source information. The model must stop short of converting “ground floor” into “wheelchair accessible.”

### Scene C — a shared phone and an answer the source cannot provide

**Resident C:** “I'm calling from the same phone as the last person. We're neighbors, different homes. Can I use the river road to get there?”

**Assistant:** “I won't treat the phone number as proof that you're the same household. This notice has no road-condition information, so I can't tell you that the river road is safe. I can record your collection concern for the desk. Do you want to describe your own household's need?”

**Resident C:** “We haven't received water. I don't want to go until someone checks the road.”

**Assistant:** “I'll record that you report no water received and cannot decide whether to collect without road information. This doesn't confirm the road's condition or arrange a route.”

**Expected proposal:** distinct provisional household, identity unresolved; reported water need, quantity unknown; missing road-information barrier; source N1.C4/C5; human review required. The shared phone is contact information, not a deduplication key. Do not disclose the previous caller's details or promise a callback unless an actual follow-up workflow exists.

**Why this could matter:** a system that confidently answers every question would fail here. Appropriate uncertainty and separate household records are part of the demonstration, although these safeguards are not unique to AI.

## 3. Change the source after the conversations

**N2, version 2 — fictional Cedar District Support Desk**

Published: scenario day 1, 11:30. Effective immediately. Explicitly supersedes N1 for today's water collection.

| Clause | Revised notice text |
|---|---|
| N2.C1 | Today's collection moves to Maple Library, ground-floor south entrance, from 12:00 to 18:00. Cedar Community Hall collection has closed. |
| N2.C2 | Representative collection remains available under the same conditions. |
| N2.C3 | Road conditions and accessibility at Maple Library are not specified. No transport or delivery service is announced. |
| N2.C4 | Residents unable to collect may report their obstacle. A report does not guarantee assistance. |

Assume the same issuer has been checked and explicit supersession confirmed by an operator. If authenticity, authority or supersession is disputed, keep the conflict visible for review; do not silently select whichever document is newest.

The system should identify **all three conversations** as relying on the superseded collection notice. That is a deterministic dependency check, not an AI invention. Old transcripts and extracted facts retain their N1 attribution; new information does not rewrite history.

| Resident | Required review after N2 | What remains unknown |
|---|---|---|
| A | New hours may permit collection after work. Suggest explaining the changed place/time and asking whether the barrier remains. | Availability, ability to reach the library and eventual receipt. Do not auto-resolve from the extended hours. |
| B | The intended destination has changed. Preserve the representative plan as reported; ask whether it still applies. Carry forward the accessibility question for the new venue. | Whether the resident has departed, received the revision or collected anything. Old venue information cannot answer the new accessibility question. |
| C | Communicate the venue change if appropriate contact permission exists. The road-information barrier remains unanswered. | Which route would be considered, current conditions, identity and receipt. A new destination is not proof of a safe journey. |

A proposed follow-up queue must distinguish “needs review,” “approved to contact,” “attempted,” “reached” and “resident reports a revised plan.” None means “received water” or “safe.” Do not automatically contact anyone in this exercise. In a future system, shared-phone follow-up requires consent and recipient confirmation without disclosing another household's information.

The visual demonstration could show one notice revision producing three different review suggestions. Its honest claim is **source changes become visible in unresolved conversations**, not “AI ensures everyone acts safely.”

## 4. Compare against serious alternatives

| Approach | What it already does well | What this exercise still needs to prove |
|---|---|---|
| Notice translation/read-aloud | Makes content accessible and explains stated facts. | Whether tailored questioning uncovers barriers that a clear explanation misses. |
| Good structured intake or call script | Asks about hours, collection help, access, transport and unmet need; keeps unknowns explicit. | Whether free-form conversation handles unexpected misconceptions with less resident and reviewer effort. |
| Structured intake plus versioned workflow | Links records to notices, detects supersession and queues follow-up. This is the strongest baseline. | Whether conversational clarification adds measurable value. Version tracking alone does not establish a GenAI advantage. |
| Proposed ClearSignal | Could clarify a resident's particular misconception and generate a source-linked review proposal. | Reliability, source attribution, language performance, latency, review burden and ability to work through an actual inbound call. None is tested here. |

This is a design walkthrough, not a scored comparison. We authored the conversations to reveal the proposed strengths, so success on these examples would be weak evidence.

## 5. Judge's assessment

**Promising demo, insufficient reason to pivot yet.** The emotional hook is direct: a resident says they understand, but their plan cannot work. A revised notice then forces a visible reassessment. This is easier to grasp quickly than a large coordination dashboard.

The weakness is substantial: explanation, issue intake and revision tracking can be assembled from familiar tools. A polished voice assistant is not enough to establish innovation, and an authored conversation is not proof of technical merit. Removing maps and many modules improves focus; it does not by itself create a stronger product.

My recommendation is to investigate a narrower proposed direction: **source-grounded resident intake feeding Relief Ledger's reviewed, unresolved-needs workflow**. ClearSignal can be the front door; Relief Ledger supplies the distinction between a reported plan, a commitment and confirmed receipt. Avoid combining two broad products. The proposed demonstration would follow one need from misunderstood notice through review and a partial outcome, with a source revision along the way.

This recommendation is not an accepted MVP change. A standalone warning platform would require evidence about who issues notices, who owns follow-up and why their existing communication systems are insufficient. Those dependencies remain unresolved.

## 6. Proposed hackathon demonstration and next gate

If implementation is later authorized, target a 150-second demonstration:

1. 0–20 seconds: show the verified scenario notice and the resident's mistaken plan.
2. 20–65 seconds: an actual inbound call reveals the barrier; the assistant cites the notice and refuses an unsupported claim.
3. 65–95 seconds: the coordinator reviews the evidence-linked need. Show a separate neighbor using the same contact number without merging households.
4. 95–125 seconds: publish the synthetic revision; affected records retain old evidence and enter follow-up review.
5. 125–150 seconds: show one partial receipt, the remaining need and the evaluation result from held-out cases. Only show measurements actually obtained.

For now, the next useful task is a **manual tabletop comparison**, not implementation. Each human independently handles unseen variations with a good intake script and the proposed conversation policy. Rotate which approach is used first and keep the supplied source identical. This can test workflow gaps; it cannot test AI performance or establish real user impact.

Include an unchanged notice, an older forwarded image, conflicting issuer information, a changed venue, an expired notice, a disconnected conversation, a shared phone and an unspecified quantity. Record unsupported assertions, wrong source versions, missed barriers, mistaken household merges, premature closure and reviewer corrections. Include scenarios where the structured script works equally well.

Proceed toward a conversational prototype only if the comparison reveals a repeated, consequential clarification gap that is plausibly suitable for GenAI. If ordinary questions and deterministic tracking cover the cases, reject the standalone ClearSignal pivot. Human scope approval is still required before implementation.

## Evidence behind the hypothesis

Sources accessed 2026-10-11; see the [source register](sources.md) for limitations.

- [WMO early-warning coordination statement](https://wmo.int/content/partners-coordination-meeting-early-warning-services) supports investigating gaps in receiving, trusting and acting on warnings. It does not validate this product or a local customer.
- [UNDRR inclusive early-warning checklist](https://www.undrr.org/publication/documents-and-publications/inclusive-early-warning-early-action-checklist-and-0) supports inclusion as a design consideration. It does not demonstrate conversational AI efficacy.
- [2024 Google Cloud Gemini hackathon winner announcement](https://googlecloudgeminihackathon.devpost.com/updates/32867-and-the-winners-are), [Gemini Radio](https://devpost.com/software/gemini-radio) and [NexusAI](https://devpost.com/software/nexusai) motivate an accessible, beneficiary-visible demonstration. Project descriptions are self-reported; the lesson is our interpretation, not a published explanation of judges' decisions or a prediction of this competition's outcome.
