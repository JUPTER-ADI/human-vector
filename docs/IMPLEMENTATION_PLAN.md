# HUMAN VECTOR Implementation Plan

## 1. Purpose and implementation rule

Implement the smallest end-to-end fictional project that conforms to the complete protocol specification before generalizing the product. The implementation must preserve the fixed human-led identity: the human directs, selects, authorizes transfer, approves reconstruction, verifies, and makes the final decision; AI proposes and challenges but never exercises that authority.

Before changing Next.js code, read the relevant version-specific guides in `node_modules/next/dist/docs/`, as required by `AGENTS.md`. No technical choice marked **TBD** in this plan may be treated as implicitly selected through coding convenience.

**Current authorization status:** Decision `D-015` and [TECHNICAL_ARCHITECTURE_PROPOSAL.md](./TECHNICAL_ARCHITECTURE_PROPOSAL.md) record the accepted minimum technical architecture. Decision `D-016` separately authorizes only the exact six-part compatibility spike in section H of that document. The spike has not been executed in this documentation task. Application implementation remains blocked pending review of the required compatibility evidence and separate explicit human authorization.

## 2. Repository baseline

The repository is a minimal `create-next-app` scaffold:

- Next.js 16.2.12 using the App Router;
- React 19.2.4 and TypeScript 5 with strict type checking;
- Tailwind CSS 4 through `@tailwindcss/postcss`;
- one starter route, root layout, global styles, and static starter assets;
- ESLint 9 with the Next.js configuration and standard npm scripts;
- no application domain model, persistence layer, AI integration, test harness, authentication, or deployment configuration.

The protocol specification consists of `PROJECT_CONTEXT.md` plus the ten documents indexed there. `PROTOCOL_CORE.md`, `COGNITIVE_PROVENANCE.md`, `MEMORY_ARCHITECTURE.md`, `SECURITY_AND_BOUNDARIES.md`, and `ACCEPTANCE_TESTS.md` define implementation invariants and evidence, not optional guidance.

## 3. D-014, D-015, and D-016 accepted — application implementation still blocked

The **database-neutral protocol domain model and authority boundary** are specified in [DOMAIN_MODEL.md](./DOMAIN_MODEL.md) and [HUMAN_AUTHORITY_BOUNDARY.md](./HUMAN_AUTHORITY_BOUNDARY.md), and recorded as accepted decision `D-014` in [DECISION_LOG.md](./DECISION_LOG.md).

- [x] The human explicitly approved `D-014` and its complete logical contract.
- [x] The mandatory logical prerequisite for coding is complete.
- [x] `D-014` no longer blocks coding on logical-domain or authority-contract grounds.
- [x] The human explicitly approved `D-015` and the complete minimum technical architecture, boundaries, risks, alternatives, gates, and spike scope.
- [x] The human explicitly authorized only the exact six-part compatibility spike through accepted decision `D-016`.
- [ ] The authorized compatibility spike has not been executed and has produced no evidence.
- [ ] Application implementation remains blocked pending required compatibility evidence and separate, explicit human authorization.

The accepted contract—not a database-library selection—includes:

- project, actor, thread, run, immutable artifact/item, direction, version, and reconstruction-manifest identities;
- all mandatory provenance event types and lineage relations;
- accepted, partially accepted, deferred, rejected, and reversed critique dispositions through separate human-only commands;
- memory records, retrieval candidates, selected/used records, and pre-generation context linkage;
- verification records and the three exact-version human outcomes: approve final, reject candidate, or create another cycle with explicit lineage;
- observed events, calculated-indicator inputs, and interpretation separation;
- permitted state transitions and human-only command authorization;
- idempotency, stale-version conflict, retry, correction, and failure semantics.

The `D-014` approval evidence is the human's explicit acceptance after review of the two domain/authority documents and their mapping to the P0 tests in `ACCEPTANCE_TESTS.md`, including the separate critique-disposition and `FIN-*` branches. The `D-015` approval evidence is the human's explicit acceptance after reviewing the complete technical proposal and all four documentation changes, including its boundaries, risks, rejected/deferred alternatives, approval gates, and exact six-part spike. `D-016` separately authorizes only that exact spike. It does not modify, supersede, or reinterpret `D-014` or `D-015`, and it does not authorize application implementation.

The spike must use fictional data and may make no production claim. It authorizes no permanent architecture expansion, full domain mapping, public deployment, authentication implementation, or irreversible or production resource. Any external resource, account configuration, credential entry, paid action, or package installation not already safely available must be separately reported before execution. A failed prerequisite stops the affected check and must be reported honestly rather than bypassed.

## 4. Mandatory MVP implementation sequence

### Phase 1 — Define and test protocol invariants

1. Implement the accepted database-neutral model and command/result contracts in [DOMAIN_MODEL.md](./DOMAIN_MODEL.md) without changing their authority semantics.
2. Implement the immutable input manifests and enforcement boundary in [HUMAN_AUTHORITY_BOUNDARY.md](./HUMAN_AUTHORITY_BOUNDARY.md) for Builder, Independent Critic, optional Specialist, retrieval, and reconstruction runs.
3. Select the smallest test harness (**TBD decision**) capable of exercising domain, persistence, and end-to-end tests.
4. Implement initial invariant tests for human-only direction/transfer/final outcomes, separate critique dispositions, thread isolation, append-only history, exact-item transfer, rejection preservation, successor-cycle lineage, frozen manifests, and idempotent authority actions.

**Exit evidence:** the accepted domain decision and passing applicable P0 tests without a persistence-specific dependency in the domain rules.

### Phase 2 — Select and prove persistence

1. Validate the `D-015`-accepted `pg`, TLS-verification, bounded-pool, and whole-transaction retry strategy against the actual Node.js 22 and CockroachDB boundary.
2. Design the physical mapping for the `D-015`-accepted numbered, reviewable, forward SQL migration method without weakening append-only history or least privilege.
3. Validate the `D-015`-accepted Titan Text Embeddings V2 output at exactly 1,024 dimensions and project-filtered cosine Distributed Vector Index against the actual services.
4. Under the bounded authorization in `D-016`, run only the exact six-part compatibility spike in [TECHNICAL_ARCHITECTURE_PROPOSAL.md](./TECHNICAL_ARCHITECTURE_PROPOSAL.md) after all required prerequisites have been safely established or separately reported. This plan records no execution or evidence.
5. Map logical records to a schema that preserves immutable versions, append-only provenance, item-level dispositions, manifests, retrieval evidence, and transactional authority actions.

**Exit evidence:** recorded decisions, reproducible migrations, server-only secret boundary, persistence/reload proof, executed vector query against fictional fixtures, and applicable `MEM-*`/`PROV-*` tests.

### Phase 3 — Create project and commit human direction

1. Replace the starter experience with the smallest fictional-project workflow.
2. Create a project and record a draft then committed human direction with constraints and success criteria.
3. Enforce human-only direction creation/change server-side and append immutable provenance.
4. Reload the project from CockroachDB and show the current direction plus its history.

**Exit evidence:** `AUTH-01`, `AUTH-02`, `AUTH-05`, `MEM-01`, and relevant provenance tests pass.

### Phase 4 — Generate attributed Builder V1

1. Apply the `D-015`-accepted Nova 2 Lite EU geographic inference-profile boundary only after its live access and output-validation spike succeeds and implementation is separately authorized.
2. Create a distinct Builder Thread with a frozen, inspectable input manifest.
3. Generate and persist an item-addressable, immutable V1 with agent attribution, attempts, and failures.
4. Ensure generation success cannot change direction or create any final-review outcome.

**Exit evidence:** Builder input/output and V1 are persisted, versioned, and traceable; malformed output and retry behavior are tested.

### Phase 5 — Capture independent human work and criticism

1. Record human contributions separately from V1.
2. Require or guide human critique before revealing the independent critic when the demonstration measures independent detection.
3. Preserve `HUMAN_CONTRIBUTION`, `HUMAN_CRITIQUE`, and `HUMAN_NEW_IDEA` as distinct, item-level artifacts.
4. Create a separate Critic Thread whose declared inputs allow it to challenge V1 and supplied human contributions without receiving hidden Builder history.
5. Produce structured contradiction items that distinguish claims, assumptions, omissions, conflicts, uncertainty, and suggested verification.

**Exit evidence:** thread-canary isolation passes; manifests prove separation; human and AI artifacts remain distinguishable.

### Phase 6 — Enforce human-controlled transfer

1. Expose separate human-only commands to fully accept, partially accept, defer, reject, or reverse each critic/specialist item.
2. Persist exact snapshots, source/target, actor, time, disposition, required reason, and the prior decision when reversing.
3. Include only human-authorized content in the target context.
4. Preserve rejection and make reversal a new reasoned human event.

**Exit evidence:** all P0 `XFER-*` tests pass, including direct non-human and cross-project attempts.

### Phase 7 — Retrieve persistent memory with visible influence

1. Store the required direction, contribution, critique, transfer, decision, version, evidence, and human-development observation categories.
2. Load the fictional Lumen Bay retrieval fixture with relevant, irrelevant, conflicting, superseded, rejected, and ineligible records.
3. Run the selected CockroachDB vector/hybrid retrieval with relational eligibility filters.
4. Persist the query, policy/configuration, ordered candidates, exclusions, and selected records.
5. Link records actually used into the reconstruction manifest before generation and keep candidates distinct from used memories.

**Exit evidence:** rejected/cross-project/sensitive records cannot enter context, no-result behavior is honest, and at least one prior eligible memory visibly affects reconstruction.

### Phase 8 — Reconstruct under human direction

1. Show the human the active direction, reconstruction instruction, sources, selected transfers, human new ideas, used memories, exclusions, and unresolved contradictions.
2. Require the human to confirm the frozen reconstruction manifest.
3. Generate a new immutable version; a manifest change or retry creates a new attempt.
4. Preserve element- or section-level origins where feasible and version-level complete lineage at minimum.

**Exit evidence:** `VER-02` through `VER-06`, `MEM-03`/`MEM-04`/`MEM-08`, and multi-origin provenance tests pass.

### Phase 9 — Verify and record the human final-review outcome

1. Provide explicit checks with `PASS`, `FAIL`, `INCONCLUSIVE`, and `NOT_RUN` states, methods, evidence, actors, and target criteria.
2. Prevent AI assertions from being treated as verified evidence.
3. Surface unresolved criticism and failed/inconclusive checks in final review.
4. Allow only the human to call exactly one explicit outcome for the exact reviewed version: `approveFinalDecision`, `rejectFinalVersion`, or `requestAnotherCycle`; require the applicable reason and acknowledgment of knowingly unresolved issues.
5. Preserve rejected candidates without creating an approved final decision, and make another-cycle requests create a new cycle/version lineage with retained direction, requested corrections, and exact source version.

**Exit evidence:** All P0 authority, verification, and `FIN-*` tests pass; approval, rejection, and another-cycle are distinct explicit human events/states and are never generation or navigation side effects.

### Phase 10 — Expose provenance, comparison, and bounded assessment

1. Render the ordered timeline, thread manifests, element origins, version lineage, transfer/rejection ledger, retrieval-to-reconstruction chain, and direction-to-decision chain.
2. Compare V1 and Final using the predefined Lumen Bay rubric plus retained/added/removed content, origins, reasons, and verification consequences.
3. Display observed human-process events, reproducible indicators, and bounded interpretation as separate layers with calculation inputs and limitations.
4. Ensure filters disclose hidden events and the complete chain remains accessible.

**Exit evidence:** `PROV-*`, `CMP-*`, and `DEV-*` acceptance tests pass from persisted records.

### Phase 11 — Complete security, deployment, and competition evidence

1. Select and record authentication/actor identity and retention/administrative policies (**TBD**) before accepting non-fixture use.
2. Deploy the `D-015`-accepted single-instance Elastic Beanstalk Node.js 22 architecture in `eu-central-1` only after its packaging/live-account compatibility evidence passes and deployment is separately authorized.
3. Maintain the dated official CockroachDB × AWS Hackathon requirement mapping and resolve participant eligibility, legal terms, license, and submission ownership still marked `UNKNOWN` or `TBD`.
4. Complete secret/history scans, dependency/license review, fictional-data audit, prompt-injection tests, operational failure tests, and safe public setup documentation.
5. Run the canonical demonstration from reset and collect the evidence required by `COMPETITION_REQUIREMENTS.md`.

**Exit evidence:** all P0 and mandatory P1 tests pass; CockroachDB and AWS behavior are genuine and reproducible; competition gates A–E are evidenced.

## 5. Mandatory MVP scope

- Complete fixed operational cycle using fictional data.
- Server-enforced human-only direction, transfer, reconstruction approval, critique dispositions, and final-review outcomes.
- Distinct Builder and Independent Critic threads with exact input manifests; optional Specialist only if needed.
- Immutable V1 and reconstructed versions with item-level origins and complete version lineage.
- Separate human contribution, critique, and new-idea records.
- Structured controlled contradiction and human response dispositions.
- Explicit, selective transfers through separate full-accept, partial-accept, defer, reject, and reverse commands; preserved disposition history.
- CockroachDB persistence for projects, threads, versions, provenance, memory, retrieval, verification, decisions, and assessment evidence.
- Actual selected CockroachDB vector retrieval with eligibility filtering and recorded configuration.
- Pre-generation proof of which memories entered reconstruction and visible evidence of their effect.
- Human verification with evidence states and unresolved-issue visibility.
- Three explicit human-only final-review outcomes on an exact version: approve, reject, or create another cycle with immutable predecessor lineage.
- Inspectable provenance/decision chain and V1-versus-Final comparison.
- Separate observed events, calculated indicators, and bounded human-process interpretation.
- Complete fictional Lumen Bay demonstration surviving reload/reset as specified.
- At least one meaningful, genuinely deployed AWS component.
- Server-only secrets, safe ignored environment setup, security boundary tests, and no real identifying/high-stakes data.
- Official competition requirements mapped and evidenced before submission.

## 6. Optional work after mandatory conformance

Defer until the mandatory lifecycle works end to end:

- multiple visual presentation modes for timelines, comparison, or lineage;
- advanced project/provenance filtering and search;
- optional Specialist Thread and specialist-role library;
- streaming agent output;
- collaborative multi-user workflows;
- authentication features beyond the controlled demonstration's selected requirement;
- rich editing, comments, exports, notifications, analytics, or dashboards;
- retrieval tuning beyond the fixture-backed minimum;
- composite human-development scores;
- cross-project memory (prohibited for MVP unless separately designed and authorized);
- UI animation and nonessential visual polish;
- generalized scenario/template creation beyond the canonical fictional demo.

Optional work must not weaken authority, isolation, provenance, memory eligibility, or claims boundaries.

## 7. Accepted technical selections and remaining open decisions

| Decision | Status after `D-015` acceptance | Required open validation or decision |
|---|---|---|
| CockroachDB client/connection (`D-101`) | Accepted: `pg`, bounded pool, verify-full TLS, transaction retries | Node.js/Next.js compatibility, pooling/failure, secrets; spike authorized by `D-016`, not executed |
| Schema/migration method (`D-102`) | Accepted: numbered reviewable forward SQL migrations | Physical mapping, reproducibility, forward-fix and deployment procedure |
| Vector/embedding implementation (`D-103`) | Accepted: `VECTOR(1024)`, prefixed cosine DVI, Titan V2 at 1,024 | Actual Basic/index/model compatibility, query plan, fixture relevance, privacy; spike authorized by `D-016`, not executed |
| AI provider/model boundary (`D-104`) | Accepted: Nova 2 Lite via suitable EU geographic inference profile | Live access/region, retention, retry, schema validation, secrets; spike authorized by `D-016`, not executed |
| AWS service/architecture (`D-105`) | Accepted: single-instance Elastic Beanstalk Node.js 22 in `eu-central-1` plus Bedrock | Packaging, runtime/network fit, observability, cost, cleanup; bounded disposable spike authorized by `D-016`, not executed; public/production deployment unauthorized |
| Test harness (`D-106`) | `TBD` | Select domain, integration, and end-to-end coverage tooling |
| Authentication/actor identity (`D-107`) | `TBD`; sequencing constraint accepted | Select Cognito or equivalent and define server attestation before public authority actions |
| Retention/deletion/export/admin access (`D-108`) | `TBD` | Privacy, backup/recovery, and append-only tension |
| Competition eligibility/legal mapping (`D-109`) | `TBD` | Participant eligibility, legal terms, owner, and sponsor evidence |
| Public license/publication plan (`D-110`) | `TBD` | Attribution, secret/history scan, exact release/deployed revision |

`D-014` remains the accepted logical prerequisite and controlling human-authority boundary. `D-015` accepts the documented minimum architecture and resolves the selections tracked by `D-101` through `D-105`, but not their compatibility evidence. `D-016` authorizes only the exact six-part compatibility spike and records no result. `D-106` through `D-110` remain open as shown. Cognito or a separately accepted equivalent may follow proof of the complete local fictional workflow, but it is mandatory before public deployment or remotely reachable human-authority actions. No row in this table authorizes application implementation.

## 8. Cross-cutting risks and required controls

- **Authority leakage:** enforce actor/action rules server-side and test direct calls, replay, and stale versions.
- **Thread contamination:** build calls from allowlisted manifests; use canary isolation tests; never reuse opaque conversations across roles.
- **Provenance gaps:** use immutable artifacts and append-only events, stable item identities, referential integrity, and transactional authority writes.
- **Decorative memory:** distinguish candidates from used records and link context before generation.
- **Prompt injection:** treat all retrieved/agent/evidence content as untrusted data; never allow it to broaden authority or access.
- **False verification:** keep agent claims separate from methods/evidence and surface inconclusive/failed results.
- **Human-development overclaim:** retain raw event links, transparent calculations, confounds, and scenario-bounded language.
- **Vector incompatibility or weak relevance:** validate official CockroachDB capabilities before schema commitment and test against the fictional evaluation set.
- **Long-running calls and partial failure:** use explicit attempts, idempotency, recoverable states, and no overwrite of prior outputs.
- **Secret or personal-data exposure:** server-only configuration, logging redaction, scans, fictional fixture audit, and no non-fixture use before policy decisions.
- **Framework drift:** consult the repository's local Next.js 16.2.12 documentation before each framework-specific implementation choice.
- **Competition mismatch:** treat official, dated rules—not assumptions—as the requirement source.

## 9. MVP completion gate

The MVP is complete only when a reviewer can run the fictional Lumen Bay project through all 14 stages, reload persisted state, inspect independent manifests and exact transfers, trace accepted and rejected origins, prove memory use before reconstruction, verify the result, make the canonical approval as the human, exercise the rejected/another-cycle branches in acceptance tests, compare V1 with Final, and inspect the bounded human-process evidence.

All P0 and mandatory P1 tests in `ACCEPTANCE_TESTS.md` must pass. CockroachDB persistence/vector behavior and the AWS component must be genuine and evidenced. No unresolved technical selection may be represented as implemented, and narrative or screenshots alone cannot substitute for application state and records.
