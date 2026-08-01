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

## 4. Open decisions

### D-101 — CockroachDB client and connection strategy

- **Status:** TBD
- **Decision needed:** Select a Next.js-runtime-compatible client, pooling/connection approach, and server boundary after reviewing the repository's version-specific Next.js documentation and CockroachDB requirements.
- **Evidence required:** Compatibility spike, failure behavior, secret handling, and operational constraints.

### D-102 — Schema migration method

- **Status:** TBD
- **Decision needed:** Choose migration/schema tooling that supports immutable/event relations and CockroachDB deployment workflow.
- **Evidence required:** Reproducible migrations, rollback/forward-fix policy, CI/deployment fit.

### D-103 — Vector and embedding implementation

- **Status:** TBD
- **Decision needed:** Choose CockroachDB vector type/index/query method, embedding provider/model/dimensions, hybrid ranking, and indexing lifecycle.
- **Evidence required:** Official compatibility, executed query, fictional relevance fixture, eligibility filtering, cost/privacy review.

### D-104 — Agent provider and model boundary

- **Status:** TBD
- **Decision needed:** Select provider/model(s), structured-output approach, prompt/version storage, conversation isolation, retries, retention, and safety boundary.
- **Evidence required:** Separate manifests, provider behavior review, server-only secrets, malformed-output recovery.

### D-105 — AWS service and deployment architecture

- **Status:** TBD
- **Decision needed:** Select the smallest meaningful AWS component consistent with runtime, database networking, cost, observability, and competition rules.
- **Evidence required:** Deployed role, live/health proof, reproducible configuration, cost and cleanup notes.

### D-106 — Test harness

- **Status:** TBD
- **Decision needed:** Select the minimum test tools for domain invariants, persistence/integration, and end-to-end behavior.
- **Evidence required:** Ability to execute P0/P1 tests in `ACCEPTANCE_TESTS.md` without replacing real competition-run infrastructure with mocks.

### D-107 — Authentication and actor identity

- **Status:** TBD
- **Decision needed:** Define human identity, session/authentication, authorization, demo access, and server-side actor attestation.
- **Evidence required:** Forgery and cross-project authorization tests; privacy/retention implications.

### D-108 — Retention, deletion, export, and administrative access

- **Status:** TBD
- **Decision needed:** Define lifecycle policies before accepting anything beyond fictional fixtures, including the tension between append-only provenance and deletion obligations.
- **Evidence required:** Threat/privacy review, backup/recovery rules, documented user/admin behavior.

### D-109 — Target competition and official requirements

- **Status:** TBD
- **Decision needed:** Identify official competition, rules version, sponsor/tool requirements, eligibility, deadlines, licenses, judging rubric, and disclosures.
- **Evidence required:** Completed source register and all mandatory requirements mapped in `COMPETITION_REQUIREMENTS.md`.

### D-110 — Public repository license and publication plan

- **Status:** TBD
- **Decision needed:** Choose license, third-party attribution process, history/secret review, release tag, and judge access method.
- **Evidence required:** License and notices, clean scans, exact deployed revision.

## 5. Decision discipline

An open choice MUST remain visibly TBD in plans, UI copy, and competition claims. Implementation convenience is not implicit acceptance. Any selected option must document tradeoffs against protocol invariants—especially human authority, thread isolation, provenance integrity, memory evidence, security, and reproducibility.
