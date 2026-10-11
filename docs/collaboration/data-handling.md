# Data handling during discovery

Accepted setup boundary: synthetic examples only. Do not collect, commit or paste real household medical information, precise beneficiary locations, phone numbers, call recordings or consent records into public tooling. No real operational data processing is authorized.

Store credentials/account configuration outside Git. `.env.example` intentionally contains no selected variables. Ignore rules are convenience, not proof of sanitization; inspect staged files, history and attachments before publication. If a secret is exposed, stop propagation and arrange revocation with the owner rather than treating deletion as sufficient.

For later design, resolve who can see and approve each record, minimum necessary data, purpose/consent for audio and location, retention/deletion, export, audit access, prompt injection and malicious reports. Separate reported facts from model proposals and approved events. These are design questions, not implemented controls or a compliance claim.

No clinical protocol, production security assessment or privacy/legal clearance has been completed. Future security reviews must use authorized assets and synthetic data; no active tests against third-party systems.
