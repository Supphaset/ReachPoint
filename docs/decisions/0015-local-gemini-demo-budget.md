# 0015 — Local chat and voice test budget

Date: 2026-10-15. Status: **Accepted by the user** in this chat: “just input 20 dollars”, answering the request for a Gemini spend cap and payer before enabling the local demo.

Approve a **USD 20 total budget** for local Gemini chat and voice testing, using the existing configured Google Cloud billing project and its current payer. Keep the existing credentials and billing arrangement; no new billing account, purchase, deployment or additional service is authorized by this change.

Enable the existing chat and browser-voice modes and verify them with a small number of synthetic requests. Preserve local SQLite data when restarting the demo. This records the operating budget; an automatic billing cutoff is not configured. The wider deployment budget remains a separate decision.

Affected documents: [decision index](README.md), [local setup](../../README.md).

## Amendment — background caller review, 16 Oct 2026

The user explicitly requested enabling Gemini for the desk's address/location, transport, emergency recommendation and optional volunteer notes workflow. Enable the existing background review runtime for the local demo and review pending synthetic callers, within the same USD 20 total local Gemini budget and existing payer. This does not increase the cap or enable another paid service. Location extraction uses the Maps link resolver; full Google Maps address geocoding remains dependent on its separately configured API access. Human approval remains required under [0016](0016-automatic-desk-review-and-human-approval.md).
