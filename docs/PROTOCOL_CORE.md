# HUMAN VECTOR Protocol Core

## 1. Status and purpose

This document is the normative protocol specification for **HUMAN VECTOR — Human-Directed Agentic Memory**. The words **MUST**, **MUST NOT**, **SHOULD**, and **MAY** describe requirements, recommendations, and options. If another project document conflicts with the fixed identity or authority rules here, the fixed identity and human-authority rules prevail.

The protocol has two required outcomes:

1. a stronger solution, demonstrated by an inspectable V1-versus-Final comparison and verification evidence; and
2. a stronger, more autonomous human process, assessed only through bounded, observable interaction evidence.

AI is an instrument that creates information pressure, contrast, alternatives, and cognitive resistance. It is not an authority and is not claimed to educate or develop a person by itself. The human must transform the pressure into criticism, comparison, independent ideas, justification, verification, selection, and decision.

## 2. Non-negotiable invariants

- Only a human actor may establish or change project direction, authorize transfer between independent threads, accept or reject criticism, approve a reconstruction, or make the final decision.
- Builder, critic, and optional specialist work MUST have distinct thread identities and declared input manifests.
- Threads MUST NOT silently inherit one another's full context.
- Cross-thread transfer MUST be explicit, item-level, human-authorized, and recorded before the item is available in the target context.
- Rejection MUST remain visible and MUST prevent the rejected item from entering reconstruction unless a later, separate human action reverses that disposition with a reason.
- Versions and provenance events MUST be immutable. Corrections are new events or versions, never silent edits.
- Reconstruction MUST identify every direction, contribution, transferred item, and memory record supplied to it.
- Retrieval displayed after generation is not evidence of memory influence. Influence requires a pre-generation context linkage.
- AI output MUST never be labeled or rendered as a human decision.
- Completion requires an explicit human final decision; generation success alone is insufficient.

## 3. Actors and authority

| Actor | Permitted role | Prohibited authority |
|---|---|---|
| Human | Direction, original contribution, critique, transfer, verification, approval, rejection, final decision | None within the controlled project workflow |
| Builder Agent | Produce V1 or requested builder analysis from its manifest | Change direction, transfer content, approve or decide |
| Independent Critic Agent | Challenge builder output and human contribution; classify weaknesses | Silently receive builder history, transfer its own criticism, override direction |
| Specialist Agent (optional) | Provide bounded domain analysis from an explicit brief | Broaden its brief, decide, or transfer output |
| System | Validate, persist, retrieve, compare, warn, and enforce transitions | Impersonate human intent or infer approval from inactivity |

Actor identity and actor type are separate. A model invocation is always an AI actor even when it writes in first person. A user-interface automation remains a system actor unless a human explicitly confirms the resulting authority-bearing action.

## 4. Canonical operational cycle

1. **Human Direction** — the human records scope, desired result, constraints, and success criteria.
2. **Builder V1** — a new Builder Thread receives only its declared manifest and produces an immutable V1.
3. **Human Contribution** — the human adds material separately from V1.
4. **Human Critique** — the human identifies weaknesses before seeing or independently of adopting critic output.
5. **Independent Critic** — a distinct Critic Thread receives an explicit snapshot and challenges both V1 and the human contribution where supplied.
6. **Controlled Contradiction** — criticism is decomposed into claims, assumptions, omissions, conflicts, and proposed tests; it requires a human response.
7. **Human-Controlled Transfer** — the human selects, rejects, or defers each transferable item, with justification where required.
8. **Persistent Memory Retrieval** — retrieval runs against an explicit query and eligible categories; candidates and used records are distinguished.
9. **Human-Directed Reconstruction** — the human sets the reconstruction instruction and approves its input manifest; the system creates a new immutable version.
10. **Verification** — claims and requirements are checked, and results are recorded as evidence.
11. **Human Final Decision** — only the human accepts, rejects, or requests another cycle.
12. **Provenance** — the complete decision chain is inspectable throughout, not produced only at the end.
13. **V1-versus-Final comparison** — the application shows additions, removals, retained content, provenance, and verification consequences.
14. **Human development assessment** — observed events, calculated indicators, and cautious interpretations are displayed separately.

Stages MAY repeat, but the recorded lineage MUST remain acyclic: every new version points to earlier source versions, never the reverse.

## 5. Protocol state model

Recommended states are `DIRECTION_DRAFT`, `DIRECTION_COMMITTED`, `V1_PENDING`, `V1_READY`, `HUMAN_INPUT_READY`, `CRITIQUE_PENDING`, `CRITIQUE_READY`, `TRANSFER_REVIEW`, `RETRIEVAL_READY`, `RECONSTRUCTION_PENDING`, `RECONSTRUCTION_READY`, `VERIFICATION`, `FINAL_REVIEW`, and `CLOSED`.

A state is a workflow projection, not the audit record. Provenance events remain the source of the decision chain. Failed AI calls or retrievals create failure events and leave the last valid state recoverable. Retries MUST use an idempotency key and create a separately identifiable attempt; they MUST NOT overwrite a prior result.

Authority-bearing transitions require fresh, explicit human intent:

| Transition | Required human action |
|---|---|
| Commit/change direction | Confirm direction version and reason for change |
| Transfer critic/specialist content | Select exact content, target, and disposition |
| Start reconstruction | Confirm instruction and input manifest |
| Approve reconstructed version | Confirm the identified version after review |
| Close project | Record final decision and justification |

## 6. Controlled contradiction contract

Contradiction is a designed stage, not a personality style. The critic input MUST identify the artifacts under review and MUST NOT include undisclosed thread history. Critic output SHOULD separate:

- factual claim and evidence status;
- assumption;
- omission;
- internal contradiction;
- conflict with direction or constraint;
- uncertainty;
- suggested verification;
- alternative, labeled as an option rather than a decision.

Each material criticism receives a stable item identifier. The human can accept for transfer, reject, defer, partially select, or answer with a new idea. The application MUST preserve the response and must allow the human to challenge an incorrect critic. Automatic agreement with the human and automatic replacement of human direction are both protocol failures.

## 7. Transfer contract

A valid transfer record contains source thread, source artifact/version, exact selected content or stable content range, destination purpose/thread, human actor, timestamp, disposition, and reason when accepting a direction conflict, partially selecting, reversing a rejection, or overriding a warning.

Transfer is copy-by-reference with a preserved snapshot/hash, not a destructive move. Unselected surrounding text MUST NOT enter the destination prompt merely because it shared a message with selected text. Bulk “transfer all” MAY exist only if every item remains enumerated and the human explicitly confirms the set.

## 8. Reconstruction contract

Before generation, the application MUST display or make inspectable a frozen reconstruction manifest containing:

- active human direction version;
- human reconstruction instruction;
- source version(s);
- human contributions and new ideas included;
- accepted transfer identifiers;
- memory records actually included;
- exclusions and unresolved contradictions;
- agent role and run/thread identity.

The reconstructed version MUST link to that manifest. A manifest change requires a new attempt. The output may recommend changes, but only the human may approve it or designate it final.

## 9. Verification and completion

Verification records distinguish `PASS`, `FAIL`, `INCONCLUSIVE`, and `NOT_RUN`; include method, target claim/criterion, evidence reference, verifier actor, and timestamp; and never turn an AI assertion into proof merely by labeling it verification. Failed or inconclusive checks remain visible during final review.

A protocol run is complete only when all mandatory stages have evidence, provenance integrity checks pass, the final version has a human decision, and both outcome views can be rendered. A human may knowingly finalize with unresolved issues, but the interface MUST surface them and require a justification.

## 10. Conformance

Conformance is behavioral, not cosmetic. A product does not conform if it merely displays thread labels, memory badges, or approval buttons while contexts are silently merged, retrieval is post hoc, authority actions are automated, or origins disappear during reconstruction. Detailed conformance tests are defined in [ACCEPTANCE_TESTS.md](./ACCEPTANCE_TESTS.md).
