# Proposed operator and business case

13 Oct 2026. This is a pilot and funding hypothesis, not adoption evidence. No partner, payer, spend cap or operational deployment is confirmed.

## Who runs it, and how it fits

A **volunteer rescue foundation or provincial disaster office** could own the coordinator desk, train team leaders, review uncertain reports and maintain response status. These are operator types, not named partners. Families benefit from a request and status link; teams use their own phones, with no new hardware.

Proposed channel handoff: 1669/1784 call-takers and LINE admins paste reports into the desk intake, or dictate through browser `/call`; the public can also use `/call` directly. This is manual entry, not a hotline or LINE integration. Existing channels keep taking reports; the operator must agree on consent, duplicate review and responsibility for updates before a real pilot.

## First pilot: a tabletop drill

Proposed scope: **one coordinator, two teams, synthetic households**, one quiet segment and one boat failure. Compare the same scenarios with the existing manual workflow; record errors as well as elapsed time. No responder drill has happened.

| Proposed measure | How to record it |
|---|---|
| Time to first review | Receipt timestamp to first coordinator review; median and slowest cases |
| Duplicates caught | Correctly linked repeats / labelled repeats; also count different families wrongly linked |
| Unchecked segments | Segments still unchecked or partly checked at drill end; never treat silence as safety |
| Wrong ETAs withdrawn | Invalidated windows removed from all role views / affected windows; time from reviewed failure |

The operator would own training, connectivity fallback and next-update responsibility. Better drill results would justify a responder-led trial, not a claim of lives saved or city-wide capacity.

## Cost estimate (USD; ASSUMPTIONS, not a quote)

Use `N` requests per month and `X = 10–50%` voice requests, each a **3-minute call**. Budget conservatively for 3 input audio minutes **and** 3 output audio minutes per call. Actual speaking time, context, retries and token usage must be metered. A 30-day always-on month is `S = 30 × 24 × 3,600 = 2,592,000 seconds`.

| Component | ASSUMPTIONS and checkable formula | Estimate per 1,000 requests | Monthly estimate |
|---|---|---:|---:|
| Gemini Live audio | Approx. $0.005/min input, $0.018/min output; `N × X × 3 × (0.005 + 0.018)` | $7–35 | `(N / 1,000) × $7–35` |
| Flash-Lite text, including voice tool turns | Assume aggregate 10,000 input and 2,000 output tokens/request. **See Vertex pricing; TO VERIFY placeholders:** `p_in = $0.10`, `p_out = $0.40` per million tokens. `N × (10,000 × p_in + 2,000 × p_out) / 1,000,000` | About $2 | `(N / 1,000) × about $2` |
| Cloud Run, fixed hosting | 1 vCPU / 1 GiB, min-instances 1, always-on. `vCPU-seconds × r_cpu + GiB-seconds × r_mem = S × (r_cpu + r_mem)`. **TO VERIFY** region/billing rates: illustrative `$0.000018–0.000024` and `$0.000002–0.0000025` per second | Allocate monthly cost across batches; not a marginal request cost | About $52–69 |
| Maps JS loads | Assume one Dynamic Maps load/request. Gross formula `N × $7 / 1,000`, before free usage caps | About $7 | `(N / 1,000) × about $7` |
| Secret Manager | Small key set and low access volume; assumed negligible, not measured | Under $1 allowance | Under $1 allowance |
| Other usage allowance | **Estimate:** extra agent/briefing tokens, retries, logs and network; replace with metering | $5–15 | `(N / 1,000) × $5–15` |

**Estimated variable cloud cost: roughly $20–60 per 1,000 requests.** Including fixed hosting, **1,000 requests/month: roughly $70–130/month**; **10,000/month: roughly $250–700/month**, before credits, tax and discounts. These are planning ranges, not measured bills or capacity tests; repeated map loads, longer calls or larger prompts can exceed them. Pinpoint pricing is unverified and excluded, as are staff time, telecom charges, build/artifact storage and future durable storage.

Pricing checked 2026-10-13: [Google Vertex pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing) lists audio by token; the per-minute figures above are supplied October 2026 planning approximations, not verified minute SKUs. [Cloud Run pricing](https://cloud.google.com/run/pricing) supports CPU/memory billing; verify Singapore instance-based rates before spending. [Maps pricing](https://developers.google.com/maps/billing-and-pricing/pricing) lists Dynamic Maps at $7/1,000 in the first paid tier, with a 10,000 monthly free usage cap; gross estimates above do not assume unused account allowances. See [source limits](../research/sources.md#judge-documentation-verification--2026-10-13).

## Sustainability and limits

Proposed: free use for foundations, with operating costs covered by **disaster-preparedness budgets, cloud credits or CSR funding**. These are options, not secured funding; a payer and spend cap need human agreement before paid use.

Validation is synthetic only; no responder drill, adoption or willingness-to-pay evidence exists. Connectivity is required, Thai voice accuracy is unmeasured, and the current in-memory demo loses changes on restart. Durable storage, sign-in, location privacy and retention must be resolved before real household use.
