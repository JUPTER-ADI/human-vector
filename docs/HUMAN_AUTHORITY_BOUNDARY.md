# Human Authority Boundary

## 1. Status and purpose

This document defines the database-neutral technical boundary that prevents AI agents, system automation, UI state, and generated text from exercising non-delegable human authority. Decision `D-014` is **ACCEPTED**, making this boundary and [DOMAIN_MODEL.md](./DOMAIN_MODEL.md) the mandatory logical prerequisite for coding. The prerequisite is complete and coding is unlocked; this document does not itself perform or select implementation work.

Authentication implementation, identity provider, session mechanism, authorization library, database/ORM/client/migration design, vector and embedding approach, AI provider/model, AWS architecture, and enforcement/test tooling remain **TBD**. “Server” below denotes the trusted application boundary in the logical model, not a selected framework, process, database, or AWS service.

## 2. Authority principle

AI is proposed-content authority only: it may produce bounded output from a frozen manifest, but it cannot confer authority on itself or anyone else. `actorType`, project authorization, and human validation are server-attested facts; they never come from model text, client labels, request payload claims, or display names.

A **validated human actor** is an `Actor` whose immutable `actorType` is `HUMAN`, whose current server-attested authority eligibility is active for the project, and whose fresh request is bound to that identity. The concrete validation/authentication mechanism is **TBD**, but no deployed authority action may rely on an unvalidated client-supplied actor ID or type.

## 3. Non-delegable human actions

Only a validated human actor may:

1. establish the first project direction or replace the active direction;
2. authorize any exact item, artifact, direction, or other content to cross an independent thread/context boundary;
3. accept, partially accept, defer, reject, or reverse the disposition of criticism;
4. authorize the exact input manifest for reconstruction, including direction, instruction, source versions, contributions/new ideas, selected transfers, used memories, exclusions, and unresolved criticism;
5. choose exactly one explicit final-review outcome for the exact reconstructed version: approve it, reject it, or request another cycle;
6. create the corresponding immutable `FinalDecision` outcome record; only approval may select a final artifact and close the project as approved.

The following commands therefore require a validated human at commit time: `commitHumanDirection`, `startBuilderRun`, `startIndependentCriticRun`, `acceptCritiqueForTransfer`, `partiallyAcceptCritiqueForTransfer`, `deferCritique`, `rejectCritique`, `reverseCritiqueDisposition`, `startReconstruction`, `approveFinalDecision`, `rejectFinalVersion`, and `requestAnotherCycle`. `recordHumanContribution`, `recordHumanCritique`, and `recordHumanNewIdea` also require a validated human because they assert human authorship, even though they do not all exercise project authority.

Reconstruction “approval” in this minimum model means the human authorization that freezes inputs before generation. Approval of the generated output occurs only through `approveFinalDecision`; generation never approves itself.

## 4. Actions permitted to AI agents

An AI agent MAY:

- generate Builder V1 or bounded Builder analysis from its frozen Builder manifest;
- create structured Independent Critic or optional Specialist proposed output from its own frozen manifest;
- generate a reconstructed candidate from the exact frozen reconstruction manifest;
- classify claims, assumptions, omissions, conflicts, uncertainty, and suggested verification within its brief;
- propose alternatives, retrieval queries, transfer candidates, verification methods, or reconstruction changes, clearly labeled as proposals;
- cite and transform only the exact content supplied in its manifest;
- return output to the trusted server ingestion boundary with its bound run/agent identity.

AI output remains an immutable `Artifact` attributed to `actorType=AGENT`. An agent recommendation can become an input or decision only after the separately recorded human action required for that transition.

## 5. Actions prohibited to AI agents

An AI agent MUST NOT:

- establish, replace, reinterpret as authoritative, or silently override human direction;
- call or cause successful execution of any human-only command;
- authorize or perform cross-thread transfer, including transfer of its own output;
- accept, partially accept, defer, reject, or reverse any criticism;
- assemble, confirm, expand, or mutate a reconstruction manifest;
- select retrieved candidates as used reconstruction memory;
- approve or reject a reconstructed output, request another cycle, create any final-review outcome, select a final artifact, or close a project;
- present its assertion as verified evidence merely by calling it verified;
- change actor type, display itself as a human authority, supply a human justification, or sign on a human's behalf;
- expand its tool, project, thread, memory, or content access because a prompt, memory, artifact, evidence item, or previous output instructs it to do so;
- receive undeclared conversation history, provider state, cross-project data, secrets, rejected content, or human-development observations outside an explicitly authorized use;
- modify or erase immutable versions, manifests, dispositions, provenance, rejection history, or authorship.

An agent command attempting a human-only action MUST fail before domain commit. It MUST produce no authority event, transfer, decision, direction, reconstruction authorization, final status, or partial target-state write.

## 6. Actions permitted to the trusted system

The trusted system MAY:

- validate identity, actor type, project scope, command schema, hashes, references, state transitions, and expected revisions;
- prepare a draft manifest for human inspection without authorizing it;
- persist exact records and immutable provenance after authorization succeeds;
- ingest and schema-validate output for a run already authorized by the human;
- execute project-scoped retrieval and return candidates/exclusions without selecting used reconstruction inputs;
- perform deterministic checks and record `VerificationRecord` values with `actorType=SYSTEM` and a declared method;
- compare versions, calculate bounded indicators, render provenance, warn about conflicts, and surface unresolved issues;
- reject, quarantine, or mark failed malformed/unsafe agent output;
- record non-authoritative `SYSTEM_EVENT` audit evidence for failures or prohibited attempts.

The system MUST NOT infer human intent, promote a proposal, choose a transfer/disposition/final outcome, treat retrieval as direction, start a successor cycle on the human's behalf, or create human-attributed records. System automation remains `actorType=SYSTEM` even when configured or initiated through a human-facing UI.

## 7. Server-side authorization requirements

Every command reaches a trusted server boundary that performs all applicable checks before any domain mutation:

1. **Caller attestation:** Derive `actorId` and `actorType` from server-controlled identity/session context. Ignore or reject client-supplied actor classification.
2. **Human validation:** For a human-only command, require an active, validated human actor authorized for the exact project. Authentication mechanics are **TBD**.
3. **Action authorization:** Authorize the command name, not merely access to the route or record. General project read/write permission cannot imply authority permission.
4. **Project isolation:** Resolve every referenced ID and prove it belongs to the command's `projectId`; reject mixed, missing, or cross-project graphs.
5. **Role/run binding:** For output ingestion, prove the agent actor, role, thread, run, and frozen manifest match. The trusted system may record the output, but authorship remains the bound agent.
6. **State and freshness:** Validate the allowed lifecycle transition, expected project revision, active direction ID, target artifact/version ID, current disposition decision ID, and manifest hash as applicable.
7. **Exact-content authorization:** Validate stable item IDs, snapshots/ranges, content hashes, target purpose/thread, exclusions, and used memory IDs. No enclosing message or thread is implicitly included.
8. **Disposition and eligibility:** Exclude rejected/deferred/unselected, superseded, unauthorized, sensitive, cross-project, or otherwise ineligible content. A reversal must reference the current human decision and include the required reason.
9. **Fresh human intent:** Require a distinct request/confirmation for each authority-bearing action. A previous login, broad consent, generated suggestion, or earlier stage confirmation is insufficient.
10. **Atomic commit:** Persist the domain change, idempotency record, current-state projection, and required provenance event(s) as one logical atomic outcome. Physical transaction design is **TBD**.

Client-side hiding, disabled controls, optimistic UI, route middleware, model instructions, or database constraints alone are insufficient. Enforcement MUST exist at the trusted command boundary and be testable through direct requests that bypass the UI.

## 8. Cross-thread and context enforcement

- Each Builder, Independent Critic, Reconstruction Agent, and optional Specialist uses a distinct `Thread` identity and a separately identified `ThreadRun`.
- Every call is assembled from an allowlisted immutable manifest. Opaque “conversation so far,” provider conversation reuse across roles, global chat history, and undeclared retrieval fallback are prohibited.
- A start command that supplies project direction or artifacts to another thread is human-only and records exact `HUMAN_TRANSFER` authorization before the target run can access them.
- `HUMAN_TRANSFER`, `TransferDecision`, and `TRANSFERS` are reserved for actual non-empty content authorized to a declared destination; review-only disposition actions cannot create them.
- The Critic manifest identifies the exact V1 and any selected human contributions; it does not inherit Builder conversation history.
- Reconstruction uses only current accepted/partial transfers, separately included human contributions/new ideas, and used memories selected by the human in the frozen manifest.
- Unselected surrounding content remains absent even when it shared a source message or artifact with selected content.
- Canary/isolation evidence MUST be possible from recorded manifests and outputs.

These rules enforce the invariant: **no silent cross-thread context sharing and no transfer without an explicit human authorization record**.

## 9. Criticism, rejection, and reversal enforcement

- Each criticism has a stable `critiqueItemId`, immutable snapshot/hash, origin actor/thread, and current disposition projected from immutable critique-disposition, rejection, transfer, and reversal events.
- Initial disposition is selected through exactly one semantically distinct validated-human command: `acceptCritiqueForTransfer`, `partiallyAcceptCritiqueForTransfer`, `deferCritique`, or `rejectCritique`.
- Only `reverseCritiqueDisposition`, called by a validated human with the current disposition event ID and a reason, can reopen an existing disposition. It returns the item to `OPEN`; it does not select a new disposition or authorize transfer.
- `REJECTED` and `DEFERRED` items are excluded from all new reconstruction manifests. Reversal alone does not make them transferable; after reversal, a separate human `acceptCritiqueForTransfer` or `partiallyAcceptCritiqueForTransfer` command is required.
- A human reversal appends `HUMAN_CRITIQUE` / `CRITIQUE_DISPOSITION_REVERSED`, references the current disposition and any transfer record, preserves every prior event, and carries no selected content, destination, `HUMAN_TRANSFER`, `TransferDecision`, `TRANSFERS`, or `INCLUDED_IN_CONTEXT` edge.
- Deferral is not rejection or transfer: `deferCritique` appends `HUMAN_CRITIQUE` / `CRITIQUE_DEFERRED`, uses disposition `DEFERRED`, and creates no `HUMAN_REJECTION`, `HUMAN_TRANSFER`, `TransferDecision`, `REJECTS`, transfer, or context-inclusion edge. Rejection uses `HUMAN_REJECTION` and `REJECTS` but also creates no transfer.
- Full and partial acceptance are distinct; partial acceptance transfers only the exact selected snapshot/range and excludes surrounding content.
- A disposition change cannot mutate a previously frozen manifest or rewrite a completed reconstruction. It applies only to a newly authorized manifest/run.
- No ranking score, model confidence, UI suggestion, retrieval similarity, or repeated recommendation can reverse a rejection.

These rules enforce the invariant: **no deferred or rejected item may influence reconstruction unless a later human reversal reopens it and a still-later explicit human acceptance command authorizes the exact transfer**.

## 10. Reconstruction and memory authority

Retrieval and reconstruction are separate authority steps:

1. `retrieveMemory` records the query, boundary, policy/configuration, ordered candidates, and exclusions. Candidate status conveys neither truth nor authority.
2. The human reviews the active direction, sources, transfer dispositions, candidates, conflicts, exclusions, and unresolved issues.
3. `startReconstruction` names the exact used subset and freezes the manifest. Only then are pre-generation `INCLUDED_IN_CONTEXT` relations created.
4. The Reconstruction Agent receives only that manifest. It cannot add candidates, full chat, hidden memories, rejected items, or a newer direction by itself.
5. A manifest change, stale direction, changed disposition, retry, or different used-memory set requires a new human authorization and a new attempt.

Memory retrieval MUST NOT alter `Project.activeDirectionVersionId`, a transfer disposition, actor authority, reconstruction approval, final status, or any prior manifest. Conflicts with active human direction are surfaced; similarity or recency cannot silently resolve them. Human-development observations are excluded from generative retrieval unless the human explicitly authorizes a declared use.

Every reconstruction MUST identify its human direction, human instruction, selected transfers, contributions/new ideas, retrieved-and-used memories, source versions, exclusions, unresolved criticism, agent, thread, and run.

## 11. Final authority enforcement

After verification reaches `READY_FOR_FINAL_REVIEW`, exactly one of three mutually exclusive validated-human commands may create the candidate's immutable final-review outcome:

| Command | Required human meaning | Event | Candidate/cycle result | Project result |
|---|---|---|---|---|
| `approveFinalDecision` | Accept this exact reviewed version as final | `HUMAN_FINAL_DECISION` | Artifact `FINAL_SELECTED`, reconstruction `FINAL_APPROVED`, cycle `APPROVED` | Project closes as approved |
| `rejectFinalVersion` | Reject this exact candidate and state why | `HUMAN_REJECTION` | Artifact/reconstruction `FINAL_REJECTED`, cycle `REJECTED`; all remain immutable and traceable | No approved final decision; project is not closed as approved |
| `requestAnotherCycle` | Refuse finalization and explicitly create a successor cycle | `HUMAN_DIRECTION` with another-cycle subtype | Prior artifact `CYCLE_SOURCE`, reconstruction `ANOTHER_CYCLE_REQUESTED`, prior cycle `ANOTHER_CYCLE`; new cycle `IN_PROGRESS` with source lineage | Project remains active; no approved final decision |

For every outcome, the server requires:

- a validated human caller with project authority;
- the exact expected project revision, cycle ID, active direction version, reconstruction version, and output artifact;
- reconstruction state `READY_FOR_FINAL_REVIEW`;
- visible current verification outcomes and unresolved criticism;
- an explicit reason and explicit acknowledgment of any `FAIL`, `INCONCLUSIVE`, `NOT_RUN`, or other unresolved issue as required by the chosen outcome;
- a fresh idempotency key and confirmation bound to the canonical request fingerprint.

`requestAnotherCycle` additionally requires the retained direction version, requested corrections, and exact reviewed source version. The server creates a new cycle identity/number and a human-authored cycle-seed artifact derived from that source. The outcome, seed, new cycle, and lineage are committed atomically with the human event; the previous candidate is never mutated. `rejectFinalVersion` creates no `HUMAN_FINAL_DECISION`, final selection, or approved-project closure.

No final-review outcome may be inferred from timeout, inactivity, navigation away, page refresh, successful generation, successful verification, model wording, system recommendation, default selection, or prior approval of reconstruction inputs. Continuation is never passive: without `requestAnotherCycle`, no successor cycle exists.

## 12. Stale-version and concurrency handling

Authority commands use optimistic concurrency at the logical boundary:

- The request carries `expectedProjectRevision` and every relevant exact ID: active direction, source/output version, current transfer decision, retrieval result, and manifest hash.
- The server resolves current state and compares every expectation immediately before commit.
- Any mismatch returns a conflict, exposes the current authoritative references for human review, and writes no requested domain transition or human authority event.
- The server never rebases, refreshes, merges, substitutes “latest,” or silently retries an authority decision on the human's behalf.
- Concurrent direction replacements: at most one request commits against a revision; the other conflicts.
- Concurrent critique dispositions: at most one becomes current for the expected prior decision; the other requires review and an explicit reversal/new decision.
- Concurrent final-review outcomes: at most one of approval, rejection, or another-cycle may commit for the candidate. Every competing or stale request conflicts; the server never converts one outcome into another.
- Once a manifest is frozen, later direction, transfer, memory, or content changes cannot alter it. A new reconstruction/run identity is required.

Non-authority output ingestion also checks the run state and manifest hash. A second different output for the same run conflicts; it does not overwrite the first.

## 13. Replay and duplicate-request protection

- Every state-changing command requires an `idempotencyKey` scoped to caller, project, and command, plus a server-calculated canonical request fingerprint.
- First successful execution records the key, fingerprint, result identities, and provenance event identities atomically.
- An exact replay returns the original result and creates no duplicate artifact, disposition, version, final-review outcome, successor cycle, or provenance event.
- Reuse of a key with a different fingerprint fails as a conflict/security event.
- An in-flight duplicate cannot race a second commit; only one logical result is visible.
- Retries after an explicit failed run use a new key and create a new attempt/run ID. Network uncertainty alone replays the original key first.
- Idempotency protection MUST last at least as long as the related project/provenance record remains authoritative. Physical retention implementation is **TBD**.
- Provider request IDs, browser state, or client-generated timestamps are supplementary evidence, not substitutes for server idempotency.

## 14. Audit and provenance requirements

Every successful meaningful state change creates an immutable `ProvenanceEvent` using the fixed vocabulary and full event envelope from [COGNITIVE_PROVENANCE.md](./COGNITIVE_PROVENANCE.md). At minimum, audit evidence MUST allow a reviewer to determine:

- the server-attested actor ID/type and project authority used;
- the command, correlation, cause, occurred/recorded time, and schema version;
- exact source and target versions, items, snapshots/hashes, threads, runs, and manifests;
- accepted, partial, rejected, deferred, and reversed dispositions with reasons;
- retrieval candidates/exclusions versus memories actually included before generation;
- verification targets, methods, evidence, results, and verifier type;
- the exact human event authorizing every authority-bearing transition;
- the exact approval, rejection, or another-cycle command/event and unresolved criticism or failed/inconclusive/not-run checks visible at that outcome.

Authority event plus state transition MUST be atomic. Corrections append. Deterministic ordering preserves `(occurredAt, recordedAt, eventId)`. Orphan references, cycles, hash mismatches, actor-type mismatches, impossible lineage, and cross-project references fail integrity checks.

Security-relevant rejected attempts SHOULD produce a non-authoritative `SYSTEM_EVENT` without copying secrets or unsafe content. Such an audit event MUST clearly record that authorization failed and MUST NOT be used as evidence that the requested human action occurred.

## 15. Failure behavior

- **Fail closed for authority:** Missing, ambiguous, stale, unvalidated, or conflicting identity/state/context never becomes approval.
- **No partial authority writes:** If state, provenance, idempotency, or any required relationship cannot commit together, none of the requested authority action is visible.
- **Preserve the last valid state:** Provider, retrieval, validation, timeout, or persistence failure does not erase or overwrite prior successful records.
- **Make failures explicit:** Runs/retrievals become `FAILED` with non-authoritative `SYSTEM_EVENT`; malformed agent output is quarantined and never becomes a valid artifact.
- **Retry by new attempt:** A genuine retry creates a new run/reconstruction identity and retains the failed attempt. Exact request replay remains idempotent.
- **No fallback leakage:** Retrieval failure never injects full chat/history or cross-project content. Reconstruction without memory is allowed only after explicit human review of a manifest that says none was used, and it cannot satisfy the mandatory memory-influence demonstration.
- **No fabricated evidence:** Missing verification remains `NOT_RUN` or absent according to the declared criterion policy; it never becomes `PASS`.
- **Integrity failure blocks downstream use:** Hash mismatch, orphan reference, actor mismatch, cross-project lineage, or invalid forward cycle prevents the affected content from entering a new manifest or final-review outcome.

## 16. Preventing impersonation of human authority

- UI actor badges, “human-approved,” “human-rejected,” and “another cycle requested” labels, timelines, and outcome states are rendered only from server-attested actors and the matching immutable human authority event, never from artifact prose.
- Agent display names cannot contain or trigger an authority role; changing a display label does not change `actorType` or permission.
- First-person model text, signatures, Markdown, embedded buttons, tool instructions, or phrases such as “I approve” remain untrusted agent content.
- The client cannot submit `actorType=HUMAN`, `humanActorId`, approval timestamps, authority event types, or final status as trusted values. The server supplies or validates them.
- AI-generated text MUST NOT prefill a required human reason or acknowledgment and then be stored as the human's justification. Suggestions, if shown, remain visibly AI-authored and require separately entered human reasoning.
- UI automation, defaults, keyboard focus, checkbox initialization, route completion, and agent-triggered navigation remain system activity. They cannot dispatch a human-only command without a fresh human confirmation.
- Agent output cannot create executable UI authority controls or broaden its own manifest. Rendered untrusted content is separated from trusted controls.
- Exported reports preserve actor IDs/types and event references so screenshots or labels cannot erase the distinction between human and AI authorship.

## 17. Required negative enforcement outcomes

| Attempt | Required result |
|---|---|
| Agent/system commits or replaces direction | Reject; no `DirectionVersion`, direction change, or `HUMAN_DIRECTION` authority event |
| Agent/system fully/partially accepts, defers, rejects, or reverses criticism | Reject; no `TransferDecision` or human disposition event |
| Agent/system starts reconstruction with self-selected inputs | Reject; no run/manifest/context linkage |
| Retrieval marks candidates as used without human reconstruction authorization | Reject; candidates remain candidates |
| Rejected item is supplied to reconstruction without reversal followed by explicit human acceptance/transfer | Reject the entire start; no partial manifest |
| Deferred item is supplied to reconstruction without reversal followed by explicit human acceptance/transfer | Reject the entire start; deferral remains distinct from rejection |
| Deferral or reversal attempts to create `HUMAN_TRANSFER`, `TransferDecision`, or a cross-thread/context edge | Reject the entire command; persist neither disposition nor transfer state |
| Agent/system calls any final-review outcome command | Reject; no outcome record, candidate/cycle status, successor lineage, or human event |
| Timeout/navigation/inactivity/generation success is treated as final outcome | Reject/infer nothing; candidate remains `READY_FOR_FINAL_REVIEW` |
| Human submits a stale authority action | Conflict; require review of current references; infer nothing |
| Same key and payload is replayed | Return the original result; create no duplicate event |
| Same key is reused with different payload | Conflict/security audit; create no requested state |
| UI/model says “approved” without an authority record | Render as untrusted content, never as project state |

These outcomes map directly to the P0 authority, transfer, reconstruction, provenance, memory, and security behaviors in [ACCEPTANCE_TESTS.md](./ACCEPTANCE_TESTS.md).

## 18. Accepted authority prerequisite and TBD choices

`D-014` is **ACCEPTED**. The human explicitly approved this boundary together with [DOMAIN_MODEL.md](./DOMAIN_MODEL.md) as the mandatory logical prerequisite for coding. That approval includes the five separate critique-disposition commands; the rule that, among critique-disposition commands, only full/partial acceptance creates `HUMAN_TRANSFER`; the non-transfer `CRITIQUE_DEFERRED` and `CRITIQUE_DISPOSITION_REVERSED` mappings; the three separate final-review outcome commands; immutable disposition/rejection history; and successor-cycle lineage rules. The logical prerequisite is complete and application coding is unlocked; all implementation must enforce these authorization and failure semantics.

The database and physical persistence mapping, ORM/query tooling, CockroachDB client and connection strategy, migration tooling, vector/index/retrieval/embedding implementation, authentication and session implementation, AI provider/model/prompts/structured-output method, AWS service/deployment architecture, and test harness remain **TBD** and require later decisions. No choice in those categories is implied here.
