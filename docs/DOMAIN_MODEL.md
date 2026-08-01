# Database-Neutral Domain Model

## 1. Status and scope

This document defines the smallest logical domain and command boundary required for the mandatory HUMAN VECTOR MVP. Decision `D-014` is **ACCEPTED**, making this model and [HUMAN_AUTHORITY_BOUNDARY.md](./HUMAN_AUTHORITY_BOUNDARY.md) the mandatory logical prerequisite for coding. The prerequisite is complete and coding is unlocked; this document does not itself perform or select implementation work.

The model is database-neutral. Database product and topology, ORM or query layer, CockroachDB client and connection strategy, schema and migration tooling, vector representation/index/query method, embedding method, authentication implementation, AI provider/model, AWS service/architecture, and test tooling are all **TBD**. The existing project intent to prove later CockroachDB and AWS behavior does not select any of those implementation choices here.

This model is normative at the logical boundary: an implementation may split or combine physical records, but it MUST preserve the identities, immutability, relationships, authority checks, states, transitions, and provenance defined here.

## 2. Shared conventions

### 2.1 Identity, time, content, and concurrency

- Every identity is an opaque, stable identifier. Its physical format is **TBD**.
- All records belong to exactly one `projectId` unless they are actor records. Cross-project references are invalid.
- All recorded times are UTC. `occurredAt` and `recordedAt` remain distinct where an action was delayed.
- Immutable content is stored directly or by an immutable `contentRef` plus `contentHash`. Storage and hashing choices are **TBD**.
- `schemaVersion` is required on every durable record.
- Mutable workflow projections carry a monotonic `revision`. Authority-bearing commands supply the expected revision and exact expected version identifiers.
- “Mutable” below means mutable only through an allowed command and a corresponding immutable provenance event. Corrections append a successor; they do not rewrite historical content.
- `idempotencyKey` and a canonical request fingerprint are required for every state-changing command. Their physical storage is **TBD**.
- Each protocol cycle has a stable project-scoped `cycleId`. Cycle-scoped records carry it directly or inherit it through an immutable parent. `requestAnotherCycle` creates a new `cycleId` and an explicit lineage from the reviewed source version; it never reuses or rewrites the previous cycle.

### 2.2 Fixed provenance vocabulary

`ProvenanceEvent.eventType` MUST be one of the vocabulary values fixed in [COGNITIVE_PROVENANCE.md](./COGNITIVE_PROVENANCE.md):

- `HUMAN_DIRECTION`
- `HUMAN_CONTRIBUTION`
- `HUMAN_CRITIQUE`
- `HUMAN_NEW_IDEA`
- `BUILDER_OUTPUT`
- `CRITIC_OUTPUT`
- `SPECIALIST_OUTPUT`
- `MEMORY_RETRIEVAL`
- `HUMAN_TRANSFER`
- `HUMAN_REJECTION`
- `RECONSTRUCTED_VERSION`
- `HUMAN_FINAL_DECISION`
- `SYSTEM_EVENT`

An event subtype may refine a vocabulary value but never replace it. In particular, reconstruction-input authorization uses `HUMAN_DIRECTION` with a reconstruction-authorization subtype; verification uses `SYSTEM_EVENT` with a verification-result subtype and retains the actual verifier in `actorId` and `actorType`; critique deferral and disposition reversal use `HUMAN_CRITIQUE` with the required `CRITIQUE_DEFERRED` and `CRITIQUE_DISPOSITION_REVERSED` subtypes. A human authority action MUST NOT be represented as `SYSTEM_EVENT`.

Lineage relations use only the established minimum relations: `DERIVED_FROM`, `CRITIQUES`, `RESPONDS_TO`, `TRANSFERS`, `RETRIEVED_FROM`, `INCLUDED_IN_CONTEXT`, `VERIFIES`, `REJECTS`, `SUPERSEDES`, and `DECIDES_ON`.

### 2.3 Fixed logical classifications

- Actor type: `HUMAN`, `AGENT`, `SYSTEM`.
- Agent role: `BUILDER`, `INDEPENDENT_CRITIC`, `RECONSTRUCTION_AGENT`, or optional `SPECIALIST`.
- Thread role: `HUMAN_WORKSPACE`, `BUILDER`, `INDEPENDENT_CRITIC`, `RECONSTRUCTION`, optional `SPECIALIST`, or `SYSTEM`.
- Critique classification: factual claim, assumption, omission, internal contradiction, direction/constraint conflict, uncertainty, suggested verification, or alternative.
- Critique disposition: `OPEN`, `ACCEPTED`, `PARTIALLY_ACCEPTED`, `REJECTED`, `DEFERRED`. Reversal is an explicit action that appends a provenance event and returns the current projection to `OPEN`; it is not itself a transfer or a disposition value.
- Verification result: `PASS`, `FAIL`, `INCONCLUSIVE`, `NOT_RUN`.
- Cycle state: `DIRECTION_REQUIRED`, `IN_PROGRESS`, `READY_FOR_FINAL_REVIEW`, `APPROVED`, `REJECTED`, `ANOTHER_CYCLE`.
- Final-review outcome: `APPROVED`, `REJECTED`, `ANOTHER_CYCLE`.
- Memory category: direction, contribution, critique, transfer, decision, version, evidence, or human-development observation.

### 2.4 Mandatory invariants

1. No agent run receives content not enumerated in its immutable input manifest.
2. No content crosses independent thread boundaries without an exact, validated-human authorization record created before inclusion.
3. A transfer snapshot/hash, not surrounding message or thread content, defines what was authorized.
4. A deferred or rejected item is ineligible for reconstruction until a validated-human reversal references the current disposition and reopens it, followed by a separate validated-human full/partial acceptance that creates a new transfer authorization. Reversal alone is insufficient.
5. A retrieved candidate is not a used memory. Only a memory identified in a human-authorized frozen reconstruction manifest, with a pre-generation `INCLUDED_IN_CONTEXT` relation, may be described as influential.
6. Reconstruction identifies the committed human direction, human instruction, source versions, contributions/new ideas, selected transfer decisions, used memories, exclusions, unresolved criticism, agent role, thread, and run.
7. Human and AI authorship are never inferred from content or display labels; they come from server-attested actor identity and the immutable event envelope.
8. Every successful meaningful state change atomically produces its required immutable provenance event or events.
9. A final-review outcome exists only after exactly one fresh, explicit validated-human command concerning an exact reconstructed version. Approval, rejection, and another-cycle outcomes are distinct and mutually exclusive for that review.
10. Only `APPROVED` creates an approved final decision or selects a final artifact. `REJECTED` preserves the rejected candidate, and `ANOTHER_CYCLE` creates successor lineage while preserving the prior candidate.
11. Timeout, navigation, inactivity, UI default, retrieval, generation success, model output, or system automation cannot create direction, transfer authority, reconstruction-input authority, critique disposition, or a final-review outcome.
12. Only a validated-human authorization of exact non-empty content to a declared destination may create a `TransferDecision`, `HUMAN_TRANSFER`, or `TRANSFERS` relation. Deferral, rejection, and disposition reversal create none of them.

## 3. Minimum entities

### 3.1 Project

- **Purpose:** Owns one isolated protocol lifecycle and its current workflow projection.
- **Required fields:** `projectId`, human-readable `title`, `createdByActorId`, `createdAt`, `state`, `activeDirectionVersionId` (nullable only while direction is required), `currentCycleId`, `currentCycleNumber`, `currentCycleState`, `revision`, `schemaVersion`.
- **Identity:** `projectId`; never reused.
- **Relationships:** Has actors through project authorization, threads, runs, direction versions, artifacts, critique and transfer records, memories, reconstructions, verifications, observations, provenance events, multiple immutable cycle outcomes, and at most one approved final decision.
- **Immutable fields:** `projectId`, `title`, `createdByActorId`, `createdAt` in the minimum MVP.
- **Mutable fields:** `state`, `activeDirectionVersionId`, current-cycle projection, and `revision`, only through allowed commands.
- **Lifecycle state:** `DIRECTION_REQUIRED`, `ACTIVE`, `CLOSED`.
- **Provenance requirements:** Creation produces `SYSTEM_EVENT`; direction activation/replacement and another-cycle creation are evidenced by `HUMAN_DIRECTION`; approved project closure is evidenced only by `HUMAN_FINAL_DECISION`; a rejected candidate is evidenced by `HUMAN_REJECTION` without closing the project as approved.

### 3.2 Actor

- **Purpose:** Separates identity, actor type, role, and authority eligibility from authored content.
- **Required fields:** `actorId`, `actorType`, `displayLabel`, `role`, `state`, `createdAt`, `authorityEligibility`, `validationRef` when human authority is eligible, `schemaVersion`.
- **Identity:** `actorId`; an invocation-specific agent identity MUST remain traceable to its role/run even when a reusable logical agent actor is used.
- **Relationships:** Authors events and records; agents are bound to runs; humans are authorized for projects by a server-validated relationship whose implementation is **TBD**.
- **Immutable fields:** `actorId`, `actorType`, `createdAt`. An `AGENT` or `SYSTEM` actor can never become `HUMAN`.
- **Mutable fields:** `displayLabel`, role metadata, `state`, and server-attested authority eligibility. Display changes never change actor type or authority.
- **Lifecycle state:** `ACTIVE`, `SUSPENDED`, `RETIRED`.
- **Provenance requirements:** Actor/authority creation, suspension, reactivation, or retirement produces `SYSTEM_EVENT`. Authentication, session, and credential choices remain **TBD**.

### 3.3 Thread

- **Purpose:** Defines an isolated context boundary for human workspace, builder, critic, reconstruction, optional specialist, or system work.
- **Required fields:** `threadId`, `projectId`, `role`, `createdByActorId`, `createdAt`, `state`, `schemaVersion`.
- **Identity:** `threadId`; Builder and Independent Critic MUST never share a thread identity.
- **Relationships:** Belongs to one project; has zero or more `ThreadRun` records and artifacts; is referenced by provenance events and transfer destinations.
- **Immutable fields:** `threadId`, `projectId`, `role`, `createdByActorId`, `createdAt`.
- **Mutable fields:** `state` only.
- **Lifecycle state:** `OPEN`, `SEALED`.
- **Provenance requirements:** Creation and sealing produce `SYSTEM_EVENT`. Sealing does not erase runs or context manifests.

### 3.4 ThreadRun

- **Purpose:** Records one separately identifiable agent or retrieval execution attempt against a frozen input manifest.
- **Required fields:** `runId`, `projectId`, `cycleId`, `threadId`, `runKind`, `attemptNumber`, `agentActorId` when agent-backed, `requestedByActorId`, `inputManifest`, `manifestHash`, `startedAt`, `state`, `idempotencyKey`, `schemaVersion`; `completedAt`, `outputArtifactIds`, or `failureRef` as the state requires.
- **Identity:** `runId`; a retry is a new run/attempt identity unless it is a replay of the same idempotency key.
- **Relationships:** Belongs to one thread/project; binds one manifest; may create artifacts, critique items, a retrieval, or a reconstruction output; references the initiating provenance event.
- **Immutable fields:** Identity, ownership, kind, attempt number, actors, entire manifest, manifest hash, start time, and idempotency key.
- **Mutable fields:** State and write-once completion/failure references.
- **Lifecycle state:** `RUNNING`, `SUCCEEDED`, `FAILED`.
- **Provenance requirements:** Start produces `SYSTEM_EVENT` plus any required `HUMAN_TRANSFER` authorizations; success produces the output-specific vocabulary event; failure produces `SYSTEM_EVENT`. A retry never overwrites the failed attempt.

The minimum immutable input manifest contains `manifestId`, `projectId`, `cycleId`, `threadId`, `runId`, committed `directionVersionId`, exact included artifact/item references and hashes, included memory IDs if any, instruction/system-instruction references and versions, prior-cycle outcome/source-version/cycle-seed references when applicable, explicit exclusions, agent role, creation/freeze time, authorizing actor/event references, and `schemaVersion`. Empty sets are explicit. “Conversation so far” is invalid.

### 3.5 DirectionVersion

- **Purpose:** Captures one immutable human commitment of project scope, desired result, constraints, success criteria, and exclusions.
- **Required fields:** `directionVersionId`, `projectId`, `versionNumber`, `scope`, `desiredResult`, `constraints`, `successCriteria`, `exclusions`, `reason`, `committedByHumanActorId`, `committedAt`, `supersedesDirectionVersionId` when replacing direction, `contentHash`, `schemaVersion`.
- **Identity:** `directionVersionId`; version number is project-scoped and not the primary identity.
- **Relationships:** Exactly one may be active for a project; manifests, reconstructions, verification criteria, and final decisions reference an exact version.
- **Immutable fields:** All fields.
- **Mutable fields:** None. “Active” is a project projection.
- **Lifecycle state:** `COMMITTED_ACTIVE`, `SUPERSEDED`.
- **Provenance requirements:** Creation/commit produces `HUMAN_DIRECTION` by the validated human. Replacement appends a new version/event with `SUPERSEDES`; the old version remains inspectable.

### 3.6 Artifact

- **Purpose:** Stores an immutable, attributable unit of meaningful content or version output without choosing a storage format.
- **Required fields:** `artifactId`, `projectId`, `cycleId`, `threadId`, `runId` when run-produced, `artifactKind`, `authorActorId`, `actorType`, immutable `content` or `contentRef`, `contentHash`, `createdAt`, `sourceArtifactIds`, `supersedesArtifactId` when correcting/replacing the same lineage, `schemaVersion`.
- **Identity:** `artifactId`; stable child item identifiers are required when content contains separately selectable elements.
- **Relationships:** May be a Builder output/V1, critic output envelope, human content, another-cycle request/lineage seed, evidence, or reconstructed output; may be linked by contributions, critique items, transfers, memories, reconstruction lineage, verification, and final decision.
- **Immutable fields:** All content, identity, attribution, origin, hash, and source fields.
- **Mutable fields:** No stored content fields. Current lifecycle is a projection from successor/final-decision records.
- **Lifecycle state:** `RECORDED`, `SUPERSEDED`, `FINAL_SELECTED`, `FINAL_REJECTED`, `CYCLE_SOURCE`. Derivation alone does not supersede V1; only an explicit same-lineage successor does.
- **Provenance requirements:** Creation uses the vocabulary event matching the artifact's true origin. Supersession creates a successor and relation; final selection is evidenced only by `HUMAN_FINAL_DECISION`; final rejection uses `HUMAN_REJECTION`; another-cycle source status uses `HUMAN_DIRECTION` and preserves content.

### 3.7 Contribution

- **Purpose:** Keeps a human contribution or human new idea distinct from V1 and agent material.
- **Required fields:** `contributionId`, `projectId`, `cycleId`, `threadId`, `artifactId`, `contributionKind` (`CONTRIBUTION` or `NEW_IDEA`), `humanActorId`, `createdAt`, declared `sourceRefs`, provenance-relative novelty metadata for a new idea, `schemaVersion`.
- **Identity:** `contributionId`; the linked artifact supplies immutable content identity.
- **Relationships:** Belongs to a human-workspace thread; may respond to an artifact/critique and may be explicitly included in critic or reconstruction manifests.
- **Immutable fields:** All fields.
- **Mutable fields:** None; correction creates a successor contribution/artifact.
- **Lifecycle state:** `RECORDED`, with optional `SUPERSEDED` projection after correction.
- **Provenance requirements:** `CONTRIBUTION` produces `HUMAN_CONTRIBUTION`; `NEW_IDEA` produces `HUMAN_NEW_IDEA`. AI-supplied text cannot be relabeled by an agent command as human-authored.

### 3.8 CritiqueItem

- **Purpose:** Makes each human or critic challenge independently addressable, reviewable, transferable, rejectable, and verifiable.
- **Required fields:** `critiqueItemId`, `projectId`, `cycleId`, `originArtifactId` or human critique artifact reference, `originThreadId`, `authorActorId`, `actorType`, `classification`, `targetRefs`, immutable `contentSnapshot`, `contentHash`, evidence/status fields, `createdAt`, `currentDisposition`, `schemaVersion`.
- **Identity:** `critiqueItemId`; item identity survives all later dispositions.
- **Relationships:** Critiques exact artifacts/items/direction criteria; has an ordered chain of immutable human disposition provenance events and zero or more actual `TransferDecision` records; may be verified and included/excluded by a reconstruction manifest.
- **Immutable fields:** Identity, origin, attribution, classification, targets, content snapshot/hash, and creation time.
- **Mutable fields:** `currentDisposition` only as a projection of immutable critique-disposition, rejection, transfer, and reversal events.
- **Lifecycle state:** `OPEN`, `DEFERRED`, `ACCEPTED_FOR_TRANSFER`, `PARTIALLY_ACCEPTED`, `REJECTED`.
- **Provenance requirements:** Human origin produces `HUMAN_CRITIQUE`; agent origin is referenced by `CRITIC_OUTPUT` or `SPECIALIST_OUTPUT`. Full/partial acceptance produces `HUMAN_TRANSFER`; deferral produces `HUMAN_CRITIQUE` / `CRITIQUE_DEFERRED`; rejection produces `HUMAN_REJECTION`; reversal produces `HUMAN_CRITIQUE` / `CRITIQUE_DISPOSITION_REVERSED` and returns the item to `OPEN` without transfer.

### 3.9 TransferDecision

- **Purpose:** Preserves one actual validated-human authorization of exact content to cross into a declared destination context.
- **Required fields:** `transferDecisionId`, `projectId`, `cycleId`, `sourceThreadId`, exact `sourceRef` (direction version, artifact, contribution, or item), optional `sourceArtifactId` and `critiqueItemId`, exact non-empty selected snapshot/range and `contentHash`, `destinationPurpose`, `destinationThreadId`, `decisionAction`, `resultingDisposition` (`ACCEPTED` or `PARTIALLY_ACCEPTED` only), `humanActorId`, `reason` where required, `decidedAt`, `schemaVersion`.
- **Identity:** `transferDecisionId`; duplicate decisions are not merged.
- **Relationships:** Points to the source content, target purpose/thread, human actor, provenance event, and any reconstruction manifest that later uses it; a later reversal event may reference it without modifying it.
- **Immutable fields:** All fields.
- **Mutable fields:** None. Current eligibility for future manifests is projected from the later critique-disposition event chain.
- **Lifecycle state:** `AUTHORIZED_CURRENT`, `AUTHORIZED_HISTORICAL`.
- **Provenance requirements:** Creation always produces `HUMAN_TRANSFER` with exact non-empty selected content, destination, snapshot/hash, and `TRANSFERS` relation. Deferral, rejection, and reversal never create a `TransferDecision` or `HUMAN_TRANSFER`. A later reversal preserves the transfer record and projects it as historical for future manifests; previously frozen manifests remain unchanged.

### 3.10 MemoryRecord

- **Purpose:** Makes persistent project knowledge retrievable without changing its origin, disposition, or authority.
- **Required fields:** `memoryId`, `projectId`, `category`, `originEventId`, `sourceThreadId`, source artifact/version/item references, immutable content or `contentRef`, `contentHash`, `createdAt`, `lifecycleState`, sensitivity labels, eligibility labels, disposition/verification references, `schemaVersion`.
- **Identity:** `memoryId`; a superseding record receives a new identity.
- **Relationships:** Derived from an existing artifact/event; may supersede another memory; appears as a candidate/exclusion in retrievals and as used input only through a frozen reconstruction manifest.
- **Immutable fields:** Identity, ownership, origin, content, hash, labels at creation, and creation time.
- **Mutable fields:** No historical fields. Current eligibility is a policy projection from immutable labels, source disposition, verification, and supersession.
- **Lifecycle state:** `ACTIVE`, `SUPERSEDED`. Eligibility is separately `ELIGIBLE` or `INELIGIBLE` for a particular retrieval purpose.
- **Provenance requirements:** The origin event proves authorship. Later materialization, supersession, eligibility correction, or indexing failure produces `SYSTEM_EVENT`. Vector/embedding/index fields and tooling remain **TBD**.

### 3.11 MemoryRetrieval

- **Purpose:** Separates a retrieval attempt, its candidates, exclusions, and recommendations from memories actually authorized for generation.
- **Required fields:** `retrievalId`, `projectId`, `cycleId`, `requestedByActorId`, `requestingStage`, exact query or query reference/hash, eligible categories, project/thread boundary, filters, policy version, retrieval mechanism/configuration reference, `startedAt`, `state`, `schemaVersion`; ordered candidates, exclusion records/reasons, and `completedAt` or failure details as applicable.
- **Identity:** `retrievalId`; a new attempt has a new identity unless the same idempotency key is replayed.
- **Relationships:** References memory candidates/exclusions; may be referenced by a reconstruction manifest, which separately identifies the used subset.
- **Immutable fields:** Request, scope, filters, policy, mechanism reference, and start metadata; result sets become immutable on completion.
- **Mutable fields:** State and write-once results/failure/completion fields.
- **Lifecycle state:** `RUNNING`, `COMPLETED`, `FAILED`.
- **Provenance requirements:** Start/completion or explicit failure is recorded with `MEMORY_RETRIEVAL`; used records later receive pre-generation `INCLUDED_IN_CONTEXT` relations through reconstruction authorization. Retrieval technology remains **TBD**.

### 3.12 ReconstructionVersion

- **Purpose:** Binds one human-authorized frozen reconstruction manifest, one generation attempt, its immutable output, verification readiness, and any final decision.
- **Required fields:** `reconstructionVersionId`, `projectId`, `cycleId`, `threadId`, `threadRunId`, active `directionVersionId`, immutable human instruction/ref/hash, source artifact/version IDs, `predecessorReconstructionVersionId` and prior-cycle outcome reference when applicable, included contribution/new-idea IDs, accepted transfer decision IDs and exact snapshots, `memoryRetrievalIds`, used `memoryIds`, explicit exclusions, unresolved `critiqueItemIds`, `authorizedByHumanActorId`, `authorizedAt`, `manifestHash`, `state`, `schemaVersion`; `outputArtifactId` and `producedAt` once output is recorded.
- **Identity:** `reconstructionVersionId`; any manifest change or retry creates a new identity.
- **Relationships:** Belongs to one reconstruction thread/run and cycle; derives from exact source versions and manifest inputs; may derive from a prior cycle's immutable candidate; has verification records; may have exactly one immutable final-review outcome.
- **Immutable fields:** The entire manifest, ownership, authorizer, authorization time, and manifest hash; output content is immutable after recording.
- **Mutable fields:** State and a write-once output reference/time.
- **Lifecycle state:** `RUNNING`, `FAILED`, `VERSION_RECORDED`, `VERIFICATION_IN_PROGRESS`, `READY_FOR_FINAL_REVIEW`, `FINAL_APPROVED`, `FINAL_REJECTED`, `ANOTHER_CYCLE_REQUESTED`.
- **Provenance requirements:** Human input authorization produces `HUMAN_DIRECTION` with exact manifest reference; output produces `RECONSTRUCTED_VERSION`; failure/readiness projections produce `SYSTEM_EVENT`; approval produces `HUMAN_FINAL_DECISION`; rejection produces `HUMAN_REJECTION`; another-cycle creation produces `HUMAN_DIRECTION` with explicit successor lineage.

### 3.13 VerificationRecord

- **Purpose:** Records an explicit check against an exact claim, criterion, artifact, or reconstruction version without converting an AI assertion into proof.
- **Required fields:** `verificationRecordId`, `projectId`, `cycleId`, `reconstructionVersionId`, target claim/criterion reference, `result`, method, evidence references, `verifierActorId`, `actorType`, `verifiedAt`, limitations/notes, `supersedesVerificationRecordId` when corrected, `schemaVersion`.
- **Identity:** `verificationRecordId`.
- **Relationships:** Verifies an exact target and reconstruction version; may cite evidence artifacts/memories and is surfaced in final review and comparison.
- **Immutable fields:** All fields.
- **Mutable fields:** None. The current result is the latest valid record for the same target/method.
- **Lifecycle state:** `RECORDED_CURRENT`, `RECORDED_SUPERSEDED`.
- **Provenance requirements:** Recording/correction produces `SYSTEM_EVENT` with verification-result subtype, actual verifier attribution, and a `VERIFIES` relation. Agent prose alone is never a sufficient evidence reference.

### 3.14 FinalDecision

- **Purpose:** Records exactly one non-inferred, non-delegable human final-review outcome for an exact reconstructed candidate. The entity name does not imply approval; only outcome `APPROVED` is an approved final decision.
- **Required fields:** `finalDecisionId`, `projectId`, `cycleId`, `reconstructionVersionId`, exact `outputArtifactId`, active `directionVersionId`, `outcome` (`APPROVED`, `REJECTED`, or `ANOTHER_CYCLE`), `humanActorId`, `reason`, unresolved issue acknowledgments, `decidedAt`, `idempotencyKey`, `schemaVersion`; `retainedDirectionVersionId`, requested corrections, exact source version, `nextCycleId`, `nextCycleNumber`, and human-authored `nextCycleSeedArtifactId` are additionally required for `ANOTHER_CYCLE`.
- **Identity:** `finalDecisionId`; one reconstruction candidate has at most one final-review outcome, a project may have multiple rejected/another-cycle outcomes across cycles, and a project has at most one approved final decision.
- **Relationships:** Decides on one reconstruction/output/direction/cycle combination; approval closes the project; rejection closes only the candidate/cycle as rejected; another-cycle points to the retained direction, reviewed source, immutable corrections, human-authored successor lineage seed, and successor cycle. Every outcome links visible verification and unresolved critique state.
- **Immutable fields:** All fields.
- **Mutable fields:** None.
- **Lifecycle state:** `RECORDED_APPROVED`, `RECORDED_REJECTED`, or `RECORDED_ANOTHER_CYCLE`, each terminal. Before an explicit command, the entity is absent; generation never creates a pending or implicit outcome.
- **Provenance requirements:** `APPROVED` produces `HUMAN_FINAL_DECISION` with `DECIDES_ON`; `REJECTED` produces `HUMAN_REJECTION` with `REJECTS`; `ANOTHER_CYCLE` produces `HUMAN_DIRECTION` with another-cycle subtype plus `DERIVED_FROM` references to the prior candidate and source version. Only approval closes the project as approved.

### 3.15 ProvenanceEvent

- **Purpose:** Provides the immutable operational decision chain and the audit source for every meaningful state change.
- **Required fields:** `eventId`, `projectId`, `cycleId` when cycle-scoped, `threadId`, `actorId`, `actorType`, fixed `eventType`, `eventSubtype` with explicit absence when none, `occurredAt`, `recordedAt`, explicit `sourceVersionIds`, optional `targetVersionId`, immutable `contentRef` plus `contentHash`, reason as required, `correlationId`, optional `causationEventId`, explicit selected/rejected/transferred item refs, explicit candidate/used memory refs where applicable, lineage relations, `schemaVersion`.
- **Identity:** Globally stable `eventId`.
- **Relationships:** References the actor, project, thread, command correlation, content, versions, items, memories, decisions, and immediate cause.
- **Immutable fields:** All fields.
- **Mutable fields:** None.
- **Lifecycle state:** `RECORDED`, terminal. Correction creates another event with `SUPERSEDES` or a correction relation while retaining the original.
- **Provenance requirements:** The record is itself the provenance evidence. Orphans, cycles, hash mismatches, impossible forward lineage, and cross-project references are integrity failures.

### 3.16 HumanProcessObservation

- **Purpose:** Stores bounded human-process evidence while keeping observed events, calculated indicators, and interpretations distinguishable.
- **Required fields:** `observationId`, `projectId`, `cycleId` or declared multi-cycle window, `subjectHumanActorId` or pseudonymous local participant reference, `layer`, assessment window start/end event IDs, `createdAt`, source record/event IDs, `supersedesObservationId` when correcting, `schemaVersion`; layer-specific fields below.
- **Identity:** `observationId`.
- **Relationships:** References raw provenance events; calculated indicators reference only declared observations/inputs; bounded interpretations reference indicators and observations. It may become human-development observation memory but is excluded from generation by default.
- **Immutable fields:** All fields.
- **Mutable fields:** None; correction appends a successor.
- **Lifecycle state:** `RECORDED_CURRENT`, `RECORDED_SUPERSEDED`.
- **Provenance requirements:** Creation/calculation/correction produces `SYSTEM_EVENT`. The event records the actual system or human actor and calculation/policy version.

The required `layer` values and fields are deliberately separate:

- `OBSERVED_EVENT`: observation kind, source event IDs, declared observation rule, and clock policy where relevant.
- `CALCULATED_INDICATOR`: input observation IDs, calculation version, numerator/denominator or complete inputs, window, result, uncertainty, and limitations.
- `BOUNDED_INTERPRETATION`: source observation/indicator IDs, cautious statement, limitations, and confounds. It can never be stored or rendered as a raw observation.

## 4. Explicit lifecycle transitions

Unlisted transitions are rejected. A transition never mutates the immutable event or content that justified an earlier state.

### 4.1 Project

| From | To | Cause |
|---|---|---|
| absent | `DIRECTION_REQUIRED` | `createProject`; initial cycle is `DIRECTION_REQUIRED` |
| `DIRECTION_REQUIRED` | `ACTIVE` | first `commitHumanDirection`; initial cycle becomes `IN_PROGRESS` |
| `ACTIVE` | `ACTIVE` | replacement direction; new version/event, no history overwrite |
| `ACTIVE` | `CLOSED` | atomic `approveFinalDecision`; current cycle becomes `APPROVED` |
| `ACTIVE` | `ACTIVE` | `rejectFinalVersion`; current cycle/candidate becomes `REJECTED`, with no approved final |
| `ACTIVE` | `ACTIVE` | `requestAnotherCycle`; previous cycle becomes `ANOTHER_CYCLE`, and a new `IN_PROGRESS` cycle identity/lineage becomes current |

`CLOSED` is terminal in the minimum MVP. A rejected cycle does not close the project as approved, but it is terminal for that candidate; the human chooses `requestAnotherCycle` instead of rejection when continuation is desired. Reopening an approved or rejected cycle requires a future human-authority command and decision not defined here.

### 4.2 Thread run

| From | To | Cause |
|---|---|---|
| absent | `RUNNING` | authorized start command freezes the manifest |
| `RUNNING` | `SUCCEEDED` | exactly one valid output/result is recorded |
| `RUNNING` | `FAILED` | explicit provider, validation, timeout, or retrieval failure |

`SUCCEEDED` and `FAILED` are terminal. A genuine retry creates a new run ID and attempt number.

### 4.3 Artifact/version

| From | To | Cause |
|---|---|---|
| absent | `RECORDED` | a valid attributed output/content command |
| `RECORDED` | `SUPERSEDED` | a separately identified same-lineage correction/replacement |
| `RECORDED` | `FINAL_SELECTED` | `approveFinalDecision` points to the exact reconstruction output |
| `RECORDED` | `FINAL_REJECTED` | `rejectFinalVersion` rejects the exact candidate while retaining it |
| `RECORDED` | `CYCLE_SOURCE` | `requestAnotherCycle` identifies it as the immutable source for successor lineage |

These projections never change content. `FINAL_REJECTED` remains traceable and excluded from approved-final status. Derivation into a reconstruction does not by itself supersede V1.

### 4.4 Critique item

| From | To | Cause |
|---|---|---|
| absent | `OPEN` | human/critic output records the item |
| `OPEN` | `ACCEPTED_FOR_TRANSFER` | validated-human `acceptCritiqueForTransfer` with the full exact item |
| `OPEN` | `PARTIALLY_ACCEPTED` | validated-human `partiallyAcceptCritiqueForTransfer` with the exact selected range |
| `OPEN` | `DEFERRED` | validated-human `deferCritique`; no content is transferred |
| `OPEN` | `REJECTED` | validated-human `rejectCritique` with reason |
| any decided state | `OPEN` | validated-human `reverseCritiqueDisposition` references the current disposition, records a reason, and reopens review without transfer |

Only `reverseCritiqueDisposition` may reopen an existing disposition. It appends a reversal event and preserves the previous disposition and any transfer record. Reversal itself cannot select a new disposition or transfer content; a later explicit accept/partial-accept command is required. An exact replay is idempotent only with the same key/fingerprint; otherwise it is rejected as a no-op/conflict, never silently overwritten.

### 4.5 Transfer decision

| From | To | Cause |
|---|---|---|
| absent | `AUTHORIZED_CURRENT` | actual human-authorized full or partial transfer |
| `AUTHORIZED_CURRENT` | `AUTHORIZED_HISTORICAL` | later `CRITIQUE_DISPOSITION_REVERSED` reopens the item for future review without changing prior manifests |

The transfer record remains immutable and visible. A later acceptance after reversal creates a new `TransferDecision`; it does not overwrite or reactivate the old one.

### 4.6 Reconstruction

| From | To | Cause |
|---|---|---|
| absent | `RUNNING` | `startReconstruction` validates and freezes the human-authorized manifest |
| `RUNNING` | `FAILED` | explicit generation/validation failure |
| `RUNNING` | `VERSION_RECORDED` | `recordReconstructedVersion` |
| `VERSION_RECORDED` | `VERIFICATION_IN_PROGRESS` | first `recordVerification` |
| `VERIFICATION_IN_PROGRESS` | `VERIFICATION_IN_PROGRESS` | another required check is recorded |
| `VERSION_RECORDED` / `VERIFICATION_IN_PROGRESS` | `READY_FOR_FINAL_REVIEW` | every declared mandatory criterion has a current visible result, including `FAIL`, `INCONCLUSIVE`, or `NOT_RUN` |
| `READY_FOR_FINAL_REVIEW` | `FINAL_APPROVED` | atomic `approveFinalDecision` |
| `READY_FOR_FINAL_REVIEW` | `FINAL_REJECTED` | atomic `rejectFinalVersion` |
| `READY_FOR_FINAL_REVIEW` | `ANOTHER_CYCLE_REQUESTED` | atomic `requestAnotherCycle`; successor cycle/version lineage is created |

`FAILED`, `FINAL_APPROVED`, `FINAL_REJECTED`, and `ANOTHER_CYCLE_REQUESTED` are terminal for that candidate. A manifest change or retry creates a new reconstruction/run identity. Readiness does not imply quality or any final-review outcome.

### 4.7 Final decision

| From | To | Cause |
|---|---|---|
| absent | `RECORDED_APPROVED` | validated-human `approveFinalDecision` after exact-version review |
| absent | `RECORDED_REJECTED` | validated-human `rejectFinalVersion` after exact-version review |
| absent | `RECORDED_ANOTHER_CYCLE` | validated-human `requestAnotherCycle` after exact-version review |

The three outcomes are distinct, mutually exclusive for a candidate, and terminal. There is no inferred, pending, timed-out, generated, passive-continuation, or system-created human outcome.

## 5. Minimum command model

Every command is validated server-side. “Validated human” means a server-attested human principal authorized for the project; the authentication mechanism remains **TBD**. A command rejected before commit creates no domain state or human authority event, though a security-relevant failure MAY append a non-authoritative `SYSTEM_EVENT` audit record.

### `createProject`

- **Permitted actor:** Validated human.
- **Preconditions:** Valid human identity; no conflicting idempotency key/fingerprint.
- **Resulting transition:** Project absent → `DIRECTION_REQUIRED`; creates initial cycle identity/number and isolated human workspace/thread boundary. The cycle cannot run until direction is committed.
- **Required provenance:** `SYSTEM_EVENT` attributing the request to the human without implying direction exists.
- **Reject when:** Caller is agent/unvalidated; identity or scope is invalid; duplicate key has different payload.
- **Idempotency:** Required; exact replay returns the original project/event.

### `commitHumanDirection`

- **Permitted actor:** Validated human only.
- **Preconditions:** Project is `DIRECTION_REQUIRED` or `ACTIVE`; request supplies complete scope/result/constraints/criteria/exclusions, reason, expected project revision, and current direction ID when replacing.
- **Resulting transition:** First commit moves project to `ACTIVE` and initial cycle to `IN_PROGRESS`; replacement keeps project/cycle active, creates a new active version, and projects the previous version as `SUPERSEDED`.
- **Required provenance:** `HUMAN_DIRECTION` with exact content hash and `SUPERSEDES` relation when applicable.
- **Reject when:** Non-human caller; stale revision/version; closed/wrong project; missing required direction/reason; cross-project reference; hash/integrity failure.
- **Idempotency:** Required; exact replay returns the original direction version. Same key/different content conflicts.

### `startBuilderRun`

- **Permitted actor:** Validated human only, because the command authorizes direction/content to cross into the Builder Thread.
- **Preconditions:** Active project with current cycle `IN_PROGRESS`; exact active committed direction; distinct open Builder Thread; explicit frozen manifest with no undeclared context; expected revision.
- **Resulting transition:** ThreadRun absent → `RUNNING`; one exact TransferDecision per actual cross-thread input absent → `AUTHORIZED_CURRENT`.
- **Required provenance:** `HUMAN_TRANSFER` for each exact cross-thread input plus `SYSTEM_EVENT` for run creation.
- **Reject when:** Non-human caller; stale/superseded direction; reused Critic thread/provider conversation; hidden/full-history input; unauthorized/project-mismatched content; run already terminal with conflicting output.
- **Idempotency:** Required; retry after failure uses a new key/run, while replay returns the existing run.

### `recordBuilderOutput`

- **Permitted actor:** Trusted server output-ingestion path for the Builder run; content author is the bound `AGENT`, never `SYSTEM` or `HUMAN`.
- **Preconditions:** Matching `RUNNING` Builder run, manifest hash, agent/run binding, valid item-addressable output and content hash.
- **Resulting transition:** Run `RUNNING` → `SUCCEEDED`; Artifact absent → `RECORDED` as V1.
- **Required provenance:** `BUILDER_OUTPUT` with agent attribution and source direction.
- **Reject when:** Caller/run binding invalid; wrong state/role/project; malformed output; manifest/hash mismatch; second different output.
- **Idempotency:** Required; identical replay returns the recorded artifact; different replay conflicts.

### `recordHumanContribution`

- **Permitted actor:** Validated human only.
- **Preconditions:** Active project; human workspace thread; immutable content and declared source references; expected revision.
- **Resulting transition:** Contribution/Artifact absent → `RECORDED`.
- **Required provenance:** `HUMAN_CONTRIBUTION`.
- **Reject when:** Agent/system attempts human authorship; stale/closed/wrong project; content is presented as independently human while declared source metadata contradicts that claim; invalid reference/hash.
- **Idempotency:** Required.

### `recordHumanCritique`

- **Permitted actor:** Validated human only.
- **Preconditions:** Active project; exact target artifact/version; itemized critique with classification and stable target refs; expected revision.
- **Resulting transition:** Human critique Artifact absent → `RECORDED`; CritiqueItem absent → `OPEN`.
- **Required provenance:** `HUMAN_CRITIQUE` with `CRITIQUES` relation.
- **Reject when:** Non-human caller; stale/missing/cross-project target; non-itemized or mutable target content; attribution forgery.
- **Idempotency:** Required.

### `startIndependentCriticRun`

- **Permitted actor:** Validated human only, because the command authorizes the exact V1/direction/contributions entering another independent thread.
- **Preconditions:** Active project with current cycle `IN_PROGRESS`; successful Builder V1 in that cycle; distinct open Critic Thread; exact direction/V1 and any selected human contributions; no Builder conversation/history; human critique exists first when the canonical assessment requires pre-critic critique; expected revision.
- **Resulting transition:** Critic ThreadRun absent → `RUNNING`; one exact TransferDecision per actual cross-thread input absent → `AUTHORIZED_CURRENT`.
- **Required provenance:** `HUMAN_TRANSFER` for every cross-thread input plus `SYSTEM_EVENT` for run creation.
- **Reject when:** Caller is not validated human; thread/run IDs overlap Builder; manifest contains undeclared history/canary/cross-project content; source/hash stale; demonstration ordering rule is violated.
- **Idempotency:** Required; a retry is a new attempt unless replaying the same request.

### `recordCriticOutput`

- **Permitted actor:** Trusted server output-ingestion path for the bound Independent Critic agent.
- **Preconditions:** Matching `RUNNING` critic run and manifest; structured, item-addressable critique; valid hashes and classifications.
- **Resulting transition:** Run `RUNNING` → `SUCCEEDED`; critic Artifact absent → `RECORDED`; each CritiqueItem absent → `OPEN`.
- **Required provenance:** `CRITIC_OUTPUT` with agent/thread attribution and `CRITIQUES` relations.
- **Reject when:** Wrong actor/role/run/project; hidden input evidence; malformed or non-addressable output; manifest/hash mismatch; conflicting second output.
- **Idempotency:** Required.

### `recordHumanNewIdea`

- **Permitted actor:** Validated human only.
- **Preconditions:** Active project; separately recorded immutable content; exact visible/source references and timing metadata; expected revision.
- **Resulting transition:** Contribution/Artifact absent → `RECORDED` with kind `NEW_IDEA`.
- **Required provenance:** `HUMAN_NEW_IDEA`.
- **Reject when:** Non-human caller; actor forgery; missing visibility/source declaration; stale/wrong project. Lack of provenance novelty does not erase the record but prevents an “independent” indicator claim.
- **Idempotency:** Required.

### `acceptCritiqueForTransfer`

- **Permitted actor:** Validated human only.
- **Preconditions:** Exact `OPEN` critique item/snapshot; destination purpose/thread; full item selection; expected item decision/revision; reason when accepting a direction conflict or overriding a warning.
- **Resulting transition:** Critique `OPEN` → `ACCEPTED_FOR_TRANSFER`; new TransferDecision → `AUTHORIZED_CURRENT`.
- **Required provenance:** `HUMAN_TRANSFER` with the full exact snapshot, source, destination, `ACCEPTED` disposition, and `TRANSFERS` relation.
- **Reject when:** Non-human caller; current state is not `OPEN`; stale state; source/target project mismatch; frozen target manifest; missing exact snapshot/required reason; selection is partial or includes surrounding content.
- **Idempotency:** Required; exact replay is one decision/event.

### `partiallyAcceptCritiqueForTransfer`

- **Permitted actor:** Validated human only.
- **Preconditions:** Exact `OPEN` critique item/snapshot; exact selected range and its hash; destination purpose/thread; expected item decision/revision; required reason explaining the selection boundary.
- **Resulting transition:** Critique `OPEN` → `PARTIALLY_ACCEPTED`; new TransferDecision → `AUTHORIZED_CURRENT`.
- **Required provenance:** `HUMAN_TRANSFER` with only the selected range/snapshot, source, destination, `PARTIALLY_ACCEPTED` disposition, reason, and `TRANSFERS` relation.
- **Reject when:** Non-human caller; current state is not `OPEN`; stale/missing/cross-project item; selection is empty/full/ambiguous; surrounding content is submitted; target manifest is frozen; reason is missing.
- **Idempotency:** Required.

### `deferCritique`

- **Permitted actor:** Validated human only.
- **Preconditions:** Exact `OPEN` critique item/snapshot; expected item decision/revision; explicit deferral reason.
- **Resulting transition:** Critique `OPEN` → `DEFERRED`; no `TransferDecision` is created and no target context receives content.
- **Required provenance:** `HUMAN_CRITIQUE` with subtype `CRITIQUE_DEFERRED`, disposition `DEFERRED`, exact item/snapshot, reason, explicit empty transferred-content set, and no `TRANSFERS` or `INCLUDED_IN_CONTEXT` relation.
- **Reject when:** Non-human caller; current state is not `OPEN`; stale/missing/cross-project item; reason missing; request contains a destination inclusion or selected transfer content.
- **Idempotency:** Required.

### `rejectCritique`

- **Permitted actor:** Validated human only.
- **Preconditions:** Exact `OPEN` critique item/snapshot; expected item decision/revision; explicit rejection reason.
- **Resulting transition:** Critique `OPEN` → `REJECTED`; no `TransferDecision` is created and no target context receives content.
- **Required provenance:** `HUMAN_REJECTION` with disposition `REJECTED`, reason, and `REJECTS` relation.
- **Reject when:** Non-human caller; current state is not `OPEN`; stale/missing/cross-project item; reason missing; request tries to transfer or include the item.
- **Idempotency:** Required.

### `reverseCritiqueDisposition`

- **Permitted actor:** Validated human only.
- **Preconditions:** Exact critique item/snapshot; current immutable disposition event and any associated transfer decision; expected disposition event ID/revision; required reversal reason.
- **Resulting transition:** Current decided critique state → `OPEN`; no `TransferDecision` is created. Any prior transfer projects as `AUTHORIZED_HISTORICAL` for future manifests; prior disposition/transfer events and previously frozen manifests remain unchanged.
- **Required provenance:** `HUMAN_CRITIQUE` with subtype `CRITIQUE_DISPOSITION_REVERSED`, exact item, previous disposition/event/transfer references, reason, resulting state `OPEN`, explicit empty transferred-content set, and no `TRANSFERS` or `INCLUDED_IN_CONTEXT` relation.
- **Reject when:** Non-human caller; missing/stale/current-disposition mismatch; item already `OPEN`; missing reason; request specifies a destination, selected content, or new accepted/rejected/deferred disposition; cross-project content; request attempts to mutate a frozen or completed reconstruction.
- **Idempotency:** Required.

### `retrieveMemory`

- **Permitted actor:** Validated human or trusted `SYSTEM` workflow, never an AI-provider actor. Retrieval does not authorize context use.
- **Preconditions:** Active project; explicit query, categories, boundary, filters, and policy version; project-scoped eligibility; expected project revision. This command contains no reconstruction-input selection.
- **Resulting transition:** MemoryRetrieval absent → `RUNNING` → `COMPLETED` or explicit `FAILED`; no direction/authority state changes.
- **Required provenance:** `MEMORY_RETRIEVAL` with query/configuration, candidates, exclusions, and outcome.
- **Reject when:** Cross-project or sensitive scope; hidden chat-history fallback; policy/configuration absent; caller tries to mark candidates as authoritative/used; integrity failure.
- **Idempotency:** Required. Same key/fingerprint returns the original attempt; a changed query or genuine retry uses a new key/ID.

### `startReconstruction`

- **Permitted actor:** Validated human only.
- **Preconditions:** Active project with current cycle `IN_PROGRESS` and active direction; exact source versions and any prior-cycle lineage declared; immutable human instruction; current accepted/partial transfer decisions only; exact contributions/new ideas; completed retrievals and eligible used-memory subset; rejected/deferred items excluded; explicit exclusions/unresolved critique; distinct open Reconstruction Thread; expected revision/direction/decision versions.
- **Resulting transition:** ReconstructionVersion and run absent → `RUNNING` with frozen manifest; creates pre-generation `INCLUDED_IN_CONTEXT` relations for used memories and an `AUTHORIZED_CURRENT` TransferDecision for each newly authorized non-empty cross-thread human artifact.
- **Required provenance:** `HUMAN_DIRECTION` with reconstruction-authorization subtype and exact manifest/hash; `HUMAN_TRANSFER` where this command newly authorizes cross-thread human artifacts not already covered.
- **Reject when:** Non-human caller; stale direction/disposition/revision; mutable/missing/cross-project source; rejected or unauthorized item; candidate memory not explicitly selected/eligible; human-development observation used without explicit declared authorization; hidden context; reused independent provider conversation.
- **Idempotency:** Required. Manifest change or retry requires a new key, reconstruction ID, and run.

### `recordReconstructedVersion`

- **Permitted actor:** Trusted server output-ingestion path for the bound Reconstruction Agent.
- **Preconditions:** Matching `RUNNING` reconstruction/run; unchanged manifest hash; valid immutable, item-addressable output and complete source lineage.
- **Resulting transition:** Reconstruction `RUNNING` → `VERSION_RECORDED`; run → `SUCCEEDED`; output Artifact absent → `RECORDED`.
- **Required provenance:** `RECONSTRUCTED_VERSION` with agent attribution, target version, all manifest source references, and lineage.
- **Reject when:** Wrong actor/run/project/state; manifest changed; missing lineage; malformed/hash-mismatched output; second different output; attempt to mark output final.
- **Idempotency:** Required.

### `recordVerification`

- **Permitted actor:** Validated human or trusted deterministic `SYSTEM` verifier. An `AGENT` may propose checks as an artifact but cannot make its assertion verified evidence.
- **Preconditions:** Exact recorded reconstruction/version and target criterion; declared method, evidence, actor, result, and limitations; expected current verification ID when correcting.
- **Resulting transition:** VerificationRecord absent → `RECORDED_CURRENT`; reconstruction `VERSION_RECORDED` → `VERIFICATION_IN_PROGRESS`, or reconstruction/current cycle → `READY_FOR_FINAL_REVIEW` once every mandatory criterion has a visible current result.
- **Required provenance:** `SYSTEM_EVENT` with verification-result subtype, actual verifier attribution, and `VERIFIES` relation.
- **Reject when:** AI assertion is the sole evidence; stale/wrong/cross-project target; invalid result; evidence missing where method requires it; correction attempts overwrite.
- **Idempotency:** Required.

### `approveFinalDecision`

- **Permitted actor:** Validated human only.
- **Preconditions:** Project `ACTIVE`; reconstruction `READY_FOR_FINAL_REVIEW`; exact cycle, output, and active direction versions match expected values; all verification/unresolved critique is visible; unresolved failures/inconclusive/not-run checks are explicitly acknowledged with reason; no final-review outcome exists for the candidate and no approved final decision exists for the project.
- **Resulting transition:** FinalDecision absent → `RECORDED_APPROVED`; reconstruction → `FINAL_APPROVED`; output artifact → `FINAL_SELECTED`; current cycle → `APPROVED`; project → `CLOSED`, atomically.
- **Required provenance:** `HUMAN_FINAL_DECISION` with `DECIDES_ON` links to exact reconstruction/output/direction and unresolved acknowledgments.
- **Reject when:** Non-human caller; stale cycle/version/revision; generation merely succeeded; review is incomplete; required reason/acknowledgment missing; any prior outcome exists for the candidate; conflicting approved decision; timeout/navigation/inactivity/default/model output is offered as intent.
- **Idempotency:** Required; exact replay returns the one final decision/event, while any payload change conflicts.

### `rejectFinalVersion`

- **Permitted actor:** Validated human only.
- **Preconditions:** Project `ACTIVE`; reconstruction `READY_FOR_FINAL_REVIEW`; exact cycle, output, and active direction versions match expected values; verification and unresolved critique are visible; explicit rejection reason; no final-review outcome exists for the candidate.
- **Resulting transition:** FinalDecision absent → `RECORDED_REJECTED`; reconstruction → `FINAL_REJECTED`; output artifact → `FINAL_REJECTED`; current cycle → `REJECTED`; project remains not-approved and does not gain an approved final decision.
- **Required provenance:** `HUMAN_REJECTION` with the reason and `REJECTS` links to the exact reconstruction/output/direction/cycle. No `HUMAN_FINAL_DECISION` is created.
- **Reject when:** Non-human caller; stale cycle/version/revision; review incomplete; reason missing; prior outcome exists; request attempts to mark the artifact selected/final-approved or close the project as approved; timeout/navigation/inactivity/model output is offered as intent.
- **Idempotency:** Required; exact replay returns the immutable rejected outcome, while any payload change conflicts.

### `requestAnotherCycle`

- **Permitted actor:** Validated human only.
- **Preconditions:** Project `ACTIVE`; reconstruction `READY_FOR_FINAL_REVIEW`; exact current cycle, reviewed output/source version, and active direction match expected values; verification and unresolved critique are visible; no final-review outcome exists for the candidate; request supplies reason, retained `directionVersionId`, and immutable requested corrections.
- **Resulting transition:** FinalDecision absent → `RECORDED_ANOTHER_CYCLE`; reviewed reconstruction → `ANOTHER_CYCLE_REQUESTED`; reviewed artifact → `CYCLE_SOURCE`; previous cycle closes as `ANOTHER_CYCLE`; server creates a new cycle identity/number and human-authored cycle-seed Artifact derived from the reviewed source; new successor cycle becomes `IN_PROGRESS`; project remains `ACTIVE`. The prior candidate and direction remain immutable.
- **Required provenance:** `HUMAN_DIRECTION` with another-cycle subtype, reason, retained direction, requested corrections, exact source version, previous/next cycle IDs, cycle-seed artifact, and `DERIVED_FROM` lineage. No `HUMAN_FINAL_DECISION` or approved-final state is created.
- **Reject when:** Non-human caller; stale cycle/direction/source/revision; source is not the exact reviewed candidate; corrections/reason/retained direction missing; prior outcome exists; generated successor identities collide; request mutates the previous candidate or tries to reuse a prior version as the new seed; timeout/navigation/inactivity/generation/model output is offered as intent.
- **Idempotency:** Required; exact replay returns the same successor cycle/outcome/event, while a changed request requires a new reviewed decision and cannot reuse the key.

## 6. Minimum run manifests

- **Builder:** active direction version; exact instruction/system-instruction version; explicit empty sets for prior thread history, transfers, and memories unless the human authorizes enumerated additions; Builder thread/run/agent IDs.
- **Independent Critic:** active direction; exact V1 artifact/items; exact human contributions authorized for review; explicit exclusions; no Builder provider conversation or undeclared history; Critic thread/run/agent IDs.
- **Reconstruction:** all fields required by `ReconstructionVersion`, including exact source versions, human instruction, contributions/new ideas, current accepted transfer snapshots, used memories selected from recorded retrievals, exclusions, unresolved criticism, and pre-generation authorizing human event.

The optional Specialist follows the same isolation and authorization rules but is not required for the smallest MVP.

## 7. Accepted logical prerequisite and deliberate limits

`D-014` is **ACCEPTED**. Together with [HUMAN_AUTHORITY_BOUNDARY.md](./HUMAN_AUTHORITY_BOUNDARY.md), this database-neutral model is now the mandatory logical prerequisite for coding. The human explicitly approved the entity identities, append-only authority/disposition history, exact lifecycle transitions, fixed provenance mapping, frozen manifest contents, and command authorization/idempotency/conflict semantics as that contract.

The accepted minimum command surface has separate human-only commands for full acceptance, partial acceptance, deferral, rejection, and reversal of criticism. It also has separate human-only commands for approving the final decision, rejecting the final candidate, and requesting a successor cycle. The approval includes those distinct semantics, events, terminal candidate states, and lineage rules. The logical approval prerequisite is complete and application coding is unlocked, but every implementation must conform to this accepted model.

No physical schema, database/ORM/client/migration/vector approach, authentication product, AI provider/model, AWS service, or test framework is approved by accepting this document; every such choice remains **TBD**.
