# Security, Safety, and System Boundaries

## 1. Scope and threat model

This specification protects human authority, thread isolation, provenance integrity, persistent memory, demonstration safety, and secrets. The MVP uses only fictional data and is not designed for medical, legal, financial, employment, family, identity, or other high-stakes personal decisions.

Relevant threats include unauthorized authority actions, cross-thread context leakage, prompt injection through stored/retrieved content, provenance tampering, cross-project retrieval, secret exposure, accidental use of real personal data, replay/duplicate actions, forged actor attribution, and misleading claims about verification or cognition.

## 2. Trust boundaries

- **Human interface:** collects explicit authority actions; client state alone is not trusted proof.
- **Application server:** validates actor/action, state transition, manifest, and project scope; provider and database credentials stay here.
- **Agent provider:** untrusted for authority and factual correctness; receives only declared context.
- **CockroachDB:** persistent source for application records once implemented; access is server-only and least-privileged.
- **AWS component:** exact boundary is TBD; it must document data, credentials, network exposure, and operational responsibility.
- **External evidence/source:** untrusted content until verified; may contain prompt injection.

An AI instruction found in a memory or evidence artifact is data, not a system instruction.

## 3. Authority controls

- Server-side authorization MUST enforce human-only direction change, transfer, reconstruction approval, and final decision.
- UI hiding is insufficient; direct requests using an agent/system actor must fail.
- Authority actions identify exact project, artifact/version, disposition, and current state.
- Destructive or high-consequence confirmations MUST not be inferred from navigation, timeout, model output, or default selection.
- Retries use idempotency keys to prevent duplicate transfer/final-decision events.
- Stale-version actions fail with a conflict and require human review of the current version.

Authentication design is deferred, but actor identity cannot remain an unvalidated client-supplied string in a deployed system.

## 4. Thread and context isolation

Every agent call is assembled server-side from an allowlisted immutable manifest. The system MUST NOT reuse an opaque provider conversation across independent threads or include global chat/history by convenience. Logs record references/hashes sufficient to audit inputs without leaking secrets. Transfers require item-level authorization before inclusion.

Tests use canary content placed only in the Builder Thread; the Critic/Specialist output and recorded manifest must show it was absent unless explicitly transferred. Provider-side retention and conversation behavior must be reviewed when a provider is selected.

## 5. Prompt-injection defenses

Retrieved memories, agent outputs, and evidence are delimited and labeled as untrusted content. The application separates system instructions from data, restricts tool access by role, validates structured outputs, and ignores embedded requests to change authority, reveal secrets, broaden retrieval, or transfer hidden context. A detected injection attempt creates a warning/event and remains inert unless a human independently chooses a permitted action.

No content item—human or AI-authored—can grant itself authority or expand its own access.

## 6. Provenance and data integrity

- Versions/events are append-only in the normal path and content-addressed or hashed.
- Referential and project-scope constraints prevent orphan and cross-project lineage.
- Authority event plus state change should be transactional.
- Server timestamps and actor classification override untrusted client fields.
- Corrections append; they do not erase the original record.
- Backups, recovery objectives, tamper-evidence level, and administrative access policy are TBD before production.

Hashes provide integrity checking, not non-repudiation. Stronger signing/audit infrastructure requires a separate decision.

## 7. Memory and retrieval controls

Relational permission/disposition filters execute before or together with similarity search; vector similarity never grants access. Retrieval defaults to the current project, excludes secrets and rejected content from generative context, and records both candidates and used records. Human-development observations are excluded from normal generation by default. Cross-project retrieval is prohibited for the MVP.

Embedding providers, if external, create another data boundary and require a recorded privacy/security review.

## 8. Data policy

Demonstration inputs MUST be fictional, conspicuously labeled, and reviewed to contain no real names, contact details, credentials, account numbers, private situations, or copied confidential content. The application SHOULD warn users at entry points and provide a fixture reset.

Data classification:

| Class | Examples | Handling |
|---|---|---|
| Public fictional | Demo artifacts | May be shown in public demo |
| Internal protocol | Prompts, manifests, test fixtures | Repository-safe unless containing secrets |
| Sensitive configuration | Endpoints, account metadata, operational logs | Limit access; redact public outputs |
| Secret | API keys, DB URLs with credentials, tokens | Server secret store/environment only; never commit/log/store as memory |

Retention, export, correction, and deletion policies must be decided before accepting non-fixture user data. Append-only provenance creates a deletion tension that cannot be solved by vague promises; production design must define tombstoning/cryptographic erasure or another lawful approach if applicable.

## 9. Secret and logging controls

- Use ignored, server-only environment configuration; never `NEXT_PUBLIC_` for secrets.
- Commit a placeholder/example file only with non-secret names and safe values.
- Redact authorization headers, cookies, database URLs, prompts containing restricted data, and provider responses where necessary.
- Do not place secrets in client bundles, errors, analytics, screenshots, fixtures, or provenance.
- Scan the working tree and Git history before publication and rotate any exposed credential; deleting the file alone is insufficient.

## 10. AI-output and verification safety

Agent output is untrusted proposed content. The UI distinguishes fact, hypothesis, recommendation, and human decision; shows uncertainty and evidence status; and never labels generation as verification. Final review surfaces failed/inconclusive checks and unresolved criticism. The human can reject and correct all AI output.

The system MUST not describe bounded behavior indicators as diagnosis or scientific fact.

## 11. Operational failures

Timeouts, partial writes, duplicate delivery, unavailable database/provider, retrieval failure, and malformed model output have explicit states. The application fails closed for authority and transfer: uncertainty never becomes approval. Recovery resumes from the last valid persisted event and creates a new attempt rather than overwriting prior output.

## 12. Out of scope for the documentation phase

No application, dependency, configuration, database, AWS, deployment, authentication, or secret-management change is authorized by this specification. Before deployment, complete a concrete threat model for the chosen architecture, abuse-case tests, dependency review, access-control design, retention plan, incident/rotation procedure, and AWS/CockroachDB/provider configuration review.
