# Data handling during discovery

Accepted setup boundary: synthetic examples only. Do not collect, commit or paste real household medical information, precise beneficiary locations, phone numbers, call recordings or consent records into public tooling. No real operational data processing is authorized.

Store credentials/account configuration outside Git. `.env.example` intentionally contains no selected variables. Ignore rules are convenience, not proof of sanitization; inspect staged files, history and attachments before publication. If a secret is exposed, stop propagation and arrange revocation with the owner rather than treating deletion as sufficient.

For later design, resolve who can see and approve each record, minimum necessary data, purpose/consent for audio and location, retention/deletion, export, audit access, prompt injection and malicious reports. Separate reported facts from model proposals and approved events. These are design questions, not implemented controls or a compliance claim.

No clinical protocol, production security assessment or privacy/legal clearance has been completed. Future security reviews must use authorized assets and synthetic data; no active tests against third-party systems.

Build-week rules (from 12 Oct):
- Seed and fixture data use invented names, no real phone numbers, and generic landmarks (L1–L3, D1).
- No service-account key files anywhere. Cloud Run uses its own service identity; Gemini is called only server-side.
- The Google Maps key is restricted by HTTP referrer and API.
- Resident status links use random tokens (128-bit), carry no personal data, expire, and can only read their own status.
- Only the coordinator role can read call transcripts; team leaders see counts and pickup points only.
- Exact household points (D25) are synthetic: invented house numbers on real streets, or public buildings (schools, condos by name). Never a real person's home. The exact point is readable only by the coordinator and the team that took the job (Firestore rules test), and leaves shared views when the job closes.
- Pinpoint and Google Places are called only server-side, with keys in Secret Manager. Only synthetic addresses are sent to them.
