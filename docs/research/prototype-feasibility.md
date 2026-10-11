# Prototype research: workflow, differentiation and telephone feasibility

Date/access date: 2026-10-11. Research only. No services, accounts, numbers or infrastructure were provisioned; no calls or model tests were run. Sources P1–P10 are registered in [sources](sources.md).

## Product insights

1. **An assignment is already an established operational artifact.** INSARAG's [coordination guide](https://insarag.org/wp-content/uploads/2025/02/ICMS-UCC-Guide.pdf) documents team status, quality assurance, worksite assignments and briefing packages. Its workflow is an inspiration, not a flood-household protocol we can adopt wholesale. A new dashboard or generated assignment brief is insufficient differentiation. Investigate clarification and evidence-linked changes within that workflow.
2. **Accountability needs an owner.** IFRC's [emergency community-engagement guide](https://www.communityengagementhub.org/wp-content/uploads/sites/2/2023/12/20231204_IFRC_CEA_Emergencies_LR.pdf) discusses focal points, responsibilities and feedback in operational meetings. Only an indexed relevant excerpt was accessible; direct PDF access returned 403. We cannot claim a complete SOP review or a confirmed local operating procedure.
3. **A meaningful prototype must show both a changed plan and an unchanged control.** This is our inference: if every update lights up every case, the system demonstrates alert noise rather than useful reasoning. Explicit task dependencies allow deterministic checks after review; conversational interpretation is the uncertain part to evaluate.
4. **The opportunity is narrower than “AI disaster coordination.”** Earlier research found a Thai public project already describing Gemini extraction, review and duplicate detection (O4). The proposed gap is whether conversations can reveal current changes with less review effort. Competitor omission, local demand and adoption remain unknown.

## A plausible real inbound-phone path, with unresolved gates

Twilio is a researched candidate, not a selected provider. Its [bidirectional Media Streams documentation](https://www.twilio.com/docs/voice/media-streams) supports sending call audio to a server and playing audio back into the call. Google's [Live API overview](https://ai.google.dev/gemini-api/docs/live-api) documents conversational audio, transcripts and tool use. These make an integration plausible; they do not constitute an available integration or successful end-to-end test.

There is a format mismatch: Twilio specifies 8 kHz mu-law; Google's overview specifies PCM input/output at different sample rates. A bridge would need audio conversion, interruption handling and disconnect recovery. [Twilio formats](https://www.twilio.com/docs/voice/media-streams/websocket-messages). Google's [capabilities guide](https://ai.google.dev/gemini-api/docs/live-api/capabilities) lists Thai; local accents, noisy telephone audio, names and addresses must still be tested.

For a Thai local number, [Twilio's requirements](https://www.twilio.com/en-us/guidelines/th/regulatory) include identity and qualifying local-address documentation. The project's eligible account, number inventory and regulatory approval time are unverified. Do not collect private documents into the repository. [Trial documentation](https://www.twilio.com/docs/usage/trials) imposes country and recipient restrictions; its [Voice trial guide](https://www.twilio.com/docs/usage/trials/try-out-voice) explicitly lists `<Stream>` among blocked trial verbs. The researched Media Streams path therefore requires a suitable full account with separate human approval for upgrade/spend. Trial speech-gathering is a different candidate approach, not evidence of streaming feasibility or equivalent interruption behavior.

The first conditional feasibility milestone after explicit implementation authorization is a real call from a normal telephone to an approved number, with two-way audio, interruption, transcript evidence and a controlled disconnect. A browser microphone can support development, but cannot satisfy the accepted inbound-telephone requirement. If a Thai number is unavailable, any alternative country number needs explicit scope agreement and transparent presentation; international call access and caller charges cannot be assumed.

## Cost illustration, not a budget or purchase approval

[Twilio Thailand pricing](https://www.twilio.com/en-us/voice/pricing/th) currently lists a local number at USD 25/month, inbound local calls at USD 0.0107/minute and Media Streams at USD 0.0044/minute. On that candidate configuration, 100 minutes would imply approximately **USD 26.51** for those three charges, before taxes, caller charges, AI usage, hosting, recording or other features. Availability, billing rules and actual configuration remain unverified; this is not a complete prototype estimate.

Google model, API route, region, quotas and pricing have not been selected. A total cost ceiling and account owner need human approval before enabling paid services. No recording service is necessary to the proposed prototype: consented synthetic transcripts can support review without retaining raw audio, subject to provider behavior being checked.

## Hosting and trusted records

[Cloud Run WebSocket guidance](https://docs.cloud.google.com/run/docs/triggering/websockets) documents support for streaming connections, request timeouts, reconnects, instance synchronization and billing. It is a possible deployment component, not a selected architecture. Do not rely on a process's memory as the sole authoritative case history.

[Gemini structured-output guidance](https://ai.google.dev/gemini-api/docs/structured-output) supports constrained outputs. Our requirement remains stronger: a well-shaped proposal can still be wrong. Validate field types, allowed event types, entity references, source support and state versions; require review before changing operational records.

## Remaining decisions

- Human owner of the prototype accounts, allowable spend and telephone geography.
- Selected Google model/API route, quota, region and data handling, checked against current documentation at architecture review.
- A local operating organization and authority for approving facts and assignments. Prototype role simulation does not establish these.
- Human acceptance of the proposed MVP deferrals and Thai-intake/English-interface target.
- Whether dependency-aware conversation review actually improves on a structured board. The [draft PRD](../product/prototype-prd.md) specifies how to test that hypothesis.

The conclusion is **plausible, unverified feasibility**, not permission to implement. The technical documentation resolves whether relevant components exist; it does not resolve whether this team can integrate them reliably within the event deadline.
