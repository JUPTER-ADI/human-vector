# Decision Log

## 1. Use of this log

This is an append-oriented Architecture/Protocol Decision Record index. Accepted decisions are not silently rewritten. If a decision changes, add a new entry that references and supersedes the old one. Status values are `PROPOSED`, `ACCEPTED`, `SUPERSEDED`, `REJECTED`, and `TBD`.

Each future entry should include ID/date/status/deciders, context, decision, rationale, alternatives, consequences, validation/evidence, and supersession link. Dates use ISO 8601. A documentation date does not imply an implementation exists.

## 2. Accepted foundational decisions

### D-001 — Fixed project identity

- **Date:** 2026-08-01
- **Status:** ACCEPTED
- **Decision:** The project is **HUMAN VECTOR — Human-Directed Agentic Memory**. The human preserves direction, authority, selection, and final decision; AI is an instrument, not an authority.
- **Consequences:** No agent or system process may be represented as exercising human authority. Authority enforcement is a P0 acceptance condition.

### D-002 — Dual required outcomes

- **Date:** 2026-08-01
- **Status:** ACCEPTED
- **Decision:** The protocol must demonstrate both a stronger solution and a stronger/more autonomous human process.
- **Consequences:** Solution criteria and human-process indicators are evaluated separately. Neither substitutes for the other.

### D-003 — Bounded human-development claims

- **Date:** 2026-08-01
- **Status:** ACCEPTED
- **Decision:** Assess only observable application events and reproducible indicators; separate them from interpretation. Do not claim diagnosis, scientific proof, universal cognitive change, or that AI alone educates the human.
- **Consequences:** Public and UI language follows `HUMAN_DEVELOPMENT_MODEL.md` and `ORIGINALITY_AND_POSITIONING.md`.

### D-004 — Independent traceable work threads

- **Date:** 2026-08-01
- **Status:** ACCEPTED
- **Decision:** Builder, Independent Critic, and optional Specialist use distinct thread/run identities and explicit input manifests. Threads do not silently share full context.
- **Consequences:** Provider conversation reuse across roles is prohibited; independence is evidenced by manifests and isolation tests.

### D-005 — Human-controlled transfer

- **Date:** 2026-08-01
- **Status:** ACCEPTED
- **Decision:** Cross-thread information transfer is item-level, explicit, selective, human-authorized, and recorded. Rejected and deferred content remains traceable and excluded until a later human disposition.
- **Consequences:** Automatic critic-to-builder merging is a protocol violation.

### D-006 — Controlled contradiction

- **Date:** 2026-08-01
- **Status:** ACCEPTED
- **Decision:** Criticism is a designed stage that tests assumptions, omissions, certainty, facts/hypotheses/decisions, and provokes a human response without overriding direction.
- **Consequences:** Both automatic agreement and automatic AI replacement of human direction fail conformance.

### D-007 — Immutable versions and append-only provenance

- **Date:** 2026-08-01
- **Status:** ACCEPTED
- **Decision:** Meaningful elements, versions, dispositions, memory use, and decisions have traceable origin/history. Normal corrections and reversals append records instead of overwriting history.
- **Consequences:** Current state is a projection of the event chain; element-level identity and lineage are required.

### D-008 — Memory influence must be evidenced

- **Date:** 2026-08-01
- **Status:** ACCEPTED
- **Decision:** Persistent memory is more than chat storage. Candidate retrieval and actual use are distinct; only a pre-generation context linkage supports a claim of influence.
- **Consequences:** Post hoc retrieval displays do not satisfy the protocol. Rejected or unauthorized memory cannot enter generation because of similarity.

### D-009 — Human-confirmed reconstruction manifest

- **Date:** 2026-08-01
- **Status:** ACCEPTED
- **Decision:** Reconstruction is generated from an inspectable frozen manifest containing active direction, human instruction, source versions, transfers, human material, and used memories.
- **Consequences:** Manifest changes require a new attempt; generated output is not final without a human decision.

### D-010 — Fictional demonstration scenario

- **Date:** 2026-08-01
- **Status:** ACCEPTED
- **Decision:** Use the fictional Lumen Bay Night Museum Trail scenario defined in `DEMONSTRATION_DESIGN.md`, with no real personal or high-stakes data.
- **Consequences:** Ground truth, deliberate weaknesses, and expected records are fixture-defined; demo claims remain scenario-bounded.

### D-011 — CockroachDB persistence target

- **Date:** 2026-08-01
- **Status:** ACCEPTED
- **Decision:** CockroachDB will later hold persistent memory, provenance, immutable versions, relational records, and vector retrieval evidence for the completed MVP.
- **Consequences:** An in-memory substitute cannot satisfy completed-MVP persistence or vector requirements. Specific tooling is not selected by this decision.

### D-012 — Real AWS component required later

- **Date:** 2026-08-01
- **Status:** ACCEPTED
- **Decision:** At least one meaningful application component must later be genuinely deployed on AWS.
- **Consequences:** Branding, diagrams, or empty configuration do not count. Service selection remains TBD.

### D-013 — Documentation-only scope for this phase

- **Date:** 2026-08-01
- **Status:** ACCEPTED
- **Decision:** This phase changes documentation only. It does not modify application code, dependencies, configuration, database, AWS resources, or deployment.
- **Consequences:** All technical designs in these documents are logical contracts until separately authorized and implemented.

## 3. Accepted database-neutral boundary

### D-014 — Database-neutral domain and human-authority boundary

- **Date:** 2026-08-01
- **Status:** ACCEPTED
- **Decider:** Human
- **Approval:** On 2026-08-01, the human explicitly approved the database-neutral domain model, human-authority boundary, lifecycle and provenance contract, five critique dispositions, and three distinct final human outcomes.
- **Context:** Application coding requires one stable logical contract for minimum entities, immutable lineage, lifecycle transitions, command authorization, stale-state handling, replay protection, and non-delegable human actions without prematurely selecting implementation tooling.
- **Decision:** Adopt [DOMAIN_MODEL.md](./DOMAIN_MODEL.md) and [HUMAN_AUTHORITY_BOUNDARY.md](./HUMAN_AUTHORITY_BOUNDARY.md) as the mandatory MVP's database-neutral domain and server-side authority boundary. The contract uses the provenance vocabulary/subtypes in [COGNITIVE_PROVENANCE.md](./COGNITIVE_PROVENANCE.md), exact frozen manifests, append-only dispositions/reversals, explicit human transfer and reconstruction-input authorization, five separate human-only critique-disposition commands, and three separate human-only final-review outcomes (`APPROVED`, `REJECTED`, `ANOTHER_CYCLE`). Among critique-disposition commands, only full or partial acceptance of exact non-empty content to a declared destination creates `TransferDecision`, `HUMAN_TRANSFER`, or `TRANSFERS`; deferral uses `HUMAN_CRITIQUE` / `CRITIQUE_DEFERRED`, rejection uses `HUMAN_REJECTION`, and reversal uses `HUMAN_CRITIQUE` / `CRITIQUE_DISPOSITION_REVERSED` to reopen review without transfer. More generally, `HUMAN_TRANSFER` is reserved for an actual validated-human authorization of exact non-empty content to a declared destination. The contract also preserves immutable rejected candidates, disposition history, successor-cycle/version lineage, optimistic concurrency, and command idempotency.
- **Rationale:** The boundary is the smallest logical model that maps the fixed protocol to enforceable records and negative authorization behavior while keeping implementation choices open.
- **Alternatives:** Begin coding from narrative stages alone; choose persistence/auth/provider infrastructure first; infer authority from UI workflow. Each alternative risks encoding silent context sharing, ambiguous authorship, mutable history, or non-human authority before the invariants are settled.
- **Consequences:** This accepted contract is now the mandatory logical prerequisite for application coding. Its explicit human acceptance completes that prerequisite and unlocks coding, but neither performs implementation work nor selects implementation tooling. The accepted contract includes the distinct commands, the rule that only an actual validated-human transfer creates `HUMAN_TRANSFER`, the critique-specific non-transfer deferral/reversal subtypes, the three final outcomes, rejection/disposition preservation, and another-cycle lineage. Database/ORM, CockroachDB client, migration, vector/embedding, authentication, AI-provider, AWS, and test-tooling choices remain `TBD` and require later decisions.
- **Validation/evidence:** Explicit human approval following review of both documents and their mapping to the P0 tests in [ACCEPTANCE_TESTS.md](./ACCEPTANCE_TESTS.md), especially `AUTH-*`, `THR-*`, `XFER-*`, `VER-*`, `MEM-*`, `PROV-*`, `FIN-*`, `QA-02`, `DEV-01`, and `SEC-*`.
- **Supersession:** None.

## 4. Accepted technical architecture decision

### D-015 — Minimum competition technical architecture

- **Date:** 2026-08-02
- **Status:** ACCEPTED
- **Decider:** Human
- **Approval:** On 2026-08-02, the human explicitly approved `D-015` after reviewing the complete [TECHNICAL_ARCHITECTURE_PROPOSAL.md](./TECHNICAL_ARCHITECTURE_PROPOSAL.md); the four-document change set comprising that proposal, [DECISION_LOG.md](./DECISION_LOG.md), [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md), and [COMPETITION_REQUIREMENTS.md](./COMPETITION_REQUIREMENTS.md); and the architecture boundaries, risks, rejected and deferred alternatives, approval gates, and exact six-part compatibility-spike scope.
- **Context:** The options analysis and adversarial audit identified a deadline-oriented architecture that can satisfy the official CockroachDB × AWS Hackathon integration requirements while preserving `D-014`. The complete candidate, evidence boundary, risks, deferred alternatives, approval gates, and proposed compatibility spike are recorded in [TECHNICAL_ARCHITECTURE_PROPOSAL.md](./TECHNICAL_ARCHITECTURE_PROPOSAL.md).
- **Decision:** Accept the minimum technical architecture documented in [TECHNICAL_ARCHITECTURE_PROPOSAL.md](./TECHNICAL_ARCHITECTURE_PROPOSAL.md): retain the existing Next.js 16 full-stack application; use a single-instance AWS Elastic Beanstalk Node.js 22 environment in `eu-central-1`; CockroachDB Cloud Basic on AWS Frankfurt; Node.js `pg` with verify-full TLS and whole-transaction SQLSTATE `40001` retry handling; numbered reviewable SQL migrations; transactional append-only provenance and server-enforced `D-014` commands; `VECTOR(1024)` with a `project_id`-prefixed `vector_cosine_ops` Distributed Vector Index; Amazon Bedrock Titan Text Embeddings V2 explicitly producing 1,024 dimensions; Amazon Nova 2 Lite through a suitable EU geographic inference profile subject to live verification; and separate Builder, Independent Critic, and Reconstruction executions. The two selected CockroachDB competition tools are Distributed Vector Indexing and an immutable-pinned, reviewed `cockroachdb-sql` Agent Skill used by a non-authoritative Retrieval Safety Agent. Cognito is deferred until the complete local workflow passes but is mandatory before public deployment or remote human-authority actions. Managed MCP is excluded from the minimum and may be reconsidered only as an optional read-only post-final Evidence Agent.
- **Rationale:** This architecture removes the ECS/Fargate/load-balancer and runtime-MCP complexity challenged by the audit while retaining a genuine full-stack AWS deployment, Bedrock model/embedding use, CockroachDB transactional/vector memory, and two judge-visible CockroachDB tools. Its agent boundaries preserve human direction, selective transfer, reconstruction authorization, and final decision.
- **Alternatives:** ECS Express Mode/Fargate was rejected for the minimum because of container, load-balancer, IAM, logging, and networking surface. Managed MCP was deferred because a development-only use would not be meaningful and a runtime use would add an unnecessary data-access boundary. `ccloud` agent administration was rejected for the minimum because its control-plane authority and cost/destructive risk do not strengthen the core workflow. Cognito-first sequencing was deferred until local protocol completion, never beyond the public-deployment gate.
- **Consequences:** The documented minimum architecture is selected, resolving the architecture choices tracked by `D-101` through `D-105`, while their required compatibility, live-account, operational, and deployment evidence remains open. `D-106` through `D-110` remain `TBD`; `D-107` retains the accepted authentication sequencing constraint but not an accepted identity/session implementation. CockroachDB Basic audit limitations, single-instance availability, model/region/account access, Agent Skill supply-chain safety, authentication, cost, retention, and publication remain explicit gates. Acceptance does not represent any component as implemented.
- **Authorization boundary:** Acceptance of `D-015` does **not** authorize or execute the six-part compatibility spike and does not authorize application implementation. The spike remains separately blocked pending explicit human authorization; successful spike evidence and subsequent explicit implementation authorization remain required.
- **Validation/evidence:** Human review and explicit approval establish the architecture decision. The bounded six-part compatibility spike has not been authorized or executed. Repository and official-source facts remain separated from live-account and compatibility assumptions in the accepted proposal.
- **Supersession:** None. `D-015` does not alter or supersede `D-014`; `D-014` remains the controlling domain and human-authority contract.

## 5. Accepted choices with open validation and remaining decisions

### D-101 — CockroachDB client and connection strategy

- **Status:** ACCEPTED
- **Resolved by:** `D-015`
- **Decision:** Use Node.js `pg`, a small bounded pool, verify-full TLS, whole-transaction SQLSTATE `40001` retry handling, and the server boundary defined by `D-014`.
- **Open validation:** Node.js 22/Next.js compatibility, live TLS connectivity, retry/failure behavior, secret handling, pooling limits, and operational constraints remain unverified. The relevant compatibility-spike checks are not authorized.

### D-102 — Schema migration method

- **Status:** ACCEPTED
- **Resolved by:** `D-015`
- **Decision:** Use numbered, immutable-after-application, reviewable forward SQL migrations with a separate least-privilege migration principal; corrections use later numbered migrations and ordinary application startup does not run migrations automatically.
- **Open validation:** Physical schema mapping, reproducibility, forward-fix procedure, CI/deployment fit, and migration privileges remain to be designed and evidenced before implementation.

### D-103 — Vector and embedding implementation

- **Status:** ACCEPTED
- **Resolved by:** `D-015`
- **Decision:** Use CockroachDB `VECTOR(1024)`, a `project_id`-prefixed `vector_cosine_ops` Distributed Vector Index, cosine retrieval, and Amazon Bedrock Titan Text Embeddings V2 explicitly requested and validated at exactly 1,024 dimensions, with relational eligibility filters and human-controlled context selection.
- **Open validation:** Live Basic-cluster capability, actual index creation/use, optimizer plan, Titan account/region access and exact output, fictional relevance behavior, indexing lifecycle, cost, and privacy remain open. The relevant compatibility-spike checks are not authorized.

### D-104 — Agent provider and model boundary

- **Status:** ACCEPTED
- **Resolved by:** `D-015`
- **Decision:** Use Amazon Nova 2 Lite through the suitable EU geographic inference profile for separate Builder, Independent Critic, Reconstruction, and Retrieval Safety executions, with immutable manifests, versioned instructions, application-side output validation, and no human-authority tool capability.
- **Open validation:** Live account/model access, source/destination region behavior, quotas, terms, latency, output-validation/retry behavior, retention, server-only secret handling, and malformed-output recovery remain open. The relevant compatibility-spike check is not authorized.

### D-105 — AWS service and deployment architecture

- **Status:** ACCEPTED
- **Resolved by:** `D-015`
- **Decision:** Use a single-instance AWS Elastic Beanstalk Node.js 22 environment in `eu-central-1` for the existing full-stack Next.js application, with Amazon Bedrock providing the selected model and embedding services.
- **Open validation:** Live account availability, current platform version, unchanged Next.js server packaging, instance/network/TLS/secret/log behavior, CockroachDB allowlisting, health evidence, cost, cleanup, and reproducible deployment remain open. The relevant compatibility-spike check is not authorized and no deployment is authorized.

### D-106 — Test harness

- **Status:** TBD
- **Decision needed:** Select the minimum test tools for domain invariants, persistence/integration, and end-to-end behavior.
- **Evidence required:** Ability to execute P0/P1 tests in `ACCEPTANCE_TESTS.md` without replacing real competition-run infrastructure with mocks.

### D-107 — Authentication and actor identity

- **Status:** TBD
- **Accepted constraint from `D-015`:** Cognito may be deferred until the complete local fictional workflow passes, but Cognito or a separately accepted equivalent is mandatory before public deployment or remotely reachable human-authority actions.
- **Decision needed:** Select the exact identity provider and define human identity, session/authentication, authorization, demo access, and server-side actor attestation.
- **Evidence required:** Forgery and cross-project authorization tests; privacy/retention implications.

### D-108 — Retention, deletion, export, and administrative access

- **Status:** TBD
- **Decision needed:** Define lifecycle policies before accepting anything beyond fictional fixtures, including the tension between append-only provenance and deletion obligations.
- **Evidence required:** Threat/privacy review, backup/recovery rules, documented user/admin behavior.

### D-109 — Competition eligibility and submission compliance

- **Status:** TBD
- **Decision needed:** The CockroachDB × AWS Hackathon and its published technical requirements/deadline are now identified. Verify participant/team eligibility, applicable legal terms, licenses, submission ownership/timeline, judging disclosures, and any rule changes before submission.
- **Evidence required:** Dated official source register, human eligibility confirmation, and every mandatory requirement mapped and evidenced in `COMPETITION_REQUIREMENTS.md`.

### D-110 — Public repository license and publication plan

- **Status:** TBD
- **Decision needed:** Choose license, third-party attribution process, history/secret review, release tag, and judge access method.
- **Evidence required:** License and notices, clean scans, exact deployed revision.

## 6. Decision discipline

An open choice MUST remain visibly TBD in plans, UI copy, and competition claims. Implementation convenience is not implicit acceptance. Any selected option must document tradeoffs against protocol invariants—especially human authority, thread isolation, provenance integrity, memory evidence, security, and reproducibility.
