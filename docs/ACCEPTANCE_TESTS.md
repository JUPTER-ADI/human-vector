# Acceptance Tests

## 1. Test strategy

These are implementation-independent behavioral acceptance tests. Framework, test runner, CockroachDB client, migration tool, vector mechanism, AI provider, and AWS service remain TBD. Tests use only fictional fixtures and must inspect persisted state, not rely solely on UI text.

Priority meanings: **P0** blocks protocol conformance; **P1** blocks the MVP demonstration; **P2** is required before public deployment. A test records setup, action, expected UI/API behavior, expected persisted events/artifacts, and cleanup.

## 2. Human authority

| ID | P | Test and expected result |
|---|---:|---|
| AUTH-01 | P0 | Human commits direction; an immutable direction version and `HUMAN_DIRECTION` event identify the human actor. |
| AUTH-02 | P0 | Agent/system attempts to commit or change direction; server rejects it and no authority event/state change is written. |
| AUTH-03 | P0 | Agent/system attempts transfer; request fails even if UI controls are bypassed. |
| AUTH-04 | P0 | Agent/system attempts reconstruction approval, `approveFinalDecision`, `rejectFinalVersion`, or `requestAnotherCycle`; request fails with no human outcome event, outcome state, or successor cycle. |
| AUTH-05 | P0 | Human acts on a stale version; conflict is shown and no decision is inferred. |
| AUTH-06 | P0 | Same authority request is replayed with one idempotency key; exactly one action/event exists. |
| AUTH-07 | P1 | Final review has unresolved failure; human may approve only after explicit acknowledgment/reason, while rejection or another-cycle requires its own explicit reason. The chosen outcome and reasoning remain visible. |

## 3. Thread independence and controlled contradiction

| ID | P | Test and expected result |
|---|---:|---|
| THR-01 | P0 | Builder and critic runs have different thread/run IDs and immutable manifests. |
| THR-02 | P0 | Builder-only canary text is not present in critic manifest/output unless explicitly transferred. |
| THR-03 | P0 | Critic receives only declared snapshots, not an opaque reused Builder/provider conversation. |
| THR-04 | P1 | Optional specialist is similarly isolated and bounded to its brief. |
| CON-01 | P1 | Critic challenges at least one V1 item and can challenge a supplied human contribution. |
| CON-02 | P1 | Criticism separates claim/assumption/omission/evidence or test and has stable item IDs. |
| CON-03 | P0 | Critic output cannot alter direction or disposition; it remains proposed content. |
| CON-04 | P1 | Human can answer criticism with rejection, acceptance, deferral, partial selection, or a new idea. |

## 4. Transfer and rejection

| ID | P | Test and expected result |
|---|---:|---|
| XFER-01 | P0 | Human selects one of several critic items; only its exact snapshot enters the target manifest. |
| XFER-02 | P0 | Unselected surrounding content is absent from the target prompt/context. |
| XFER-03 | P0 | Rejected item remains inspectable with reason and is excluded from reconstruction. |
| XFER-04 | P0 | `reverseCritiqueDisposition` appends `HUMAN_CRITIQUE` / `CRITIQUE_DISPOSITION_REVERSED` with reason, projects the item to `OPEN`, and preserves every prior disposition/transfer. It creates no `HUMAN_TRANSFER`, `TransferDecision`, selected content, destination, or cross-thread/context edge. |
| XFER-05 | P0 | `deferCritique` appends `HUMAN_CRITIQUE` / `CRITIQUE_DEFERRED` with explicit `DEFERRED` disposition and reason. It remains distinct from rejection and creates no `HUMAN_TRANSFER`, `HUMAN_REJECTION`, `TransferDecision`, `TRANSFERS`, `REJECTS`, or `INCLUDED_IN_CONTEXT` relation. |
| XFER-06 | P0 | Cross-project or wrong-target transfer fails without partial persistence. |
| XFER-07 | P0 | Full acceptance, partial acceptance, deferral, and rejection use their separate commands and create `ACCEPTED`, `PARTIALLY_ACCEPTED`, `DEFERRED`, and `REJECTED` respectively with the required distinct event mapping; no command overload silently maps one disposition/event to another. |
| XFER-08 | P0 | Agent/system directly calls any of the five critique-disposition commands; every request fails with no disposition or human event. |
| XFER-09 | P0 | Reconstruction is attempted with deferred or rejected criticism without both a later valid human reversal to `OPEN` and a still-later explicit full/partial acceptance transfer; the entire start fails and no context/manifest is partially written. |
| XFER-10 | P0 | Among critique-disposition commands, only `acceptCritiqueForTransfer` or `partiallyAcceptCritiqueForTransfer` creates `HUMAN_TRANSFER` and `TransferDecision`, and each contains exact non-empty content plus a declared destination. Deferral, rejection, and reversal create neither. |
| XFER-11 | P0 | After multiple disposition, reversal, and later acceptance actions, every prior disposition/event/transfer remains historically traceable in order; current eligibility is a projection and no record is overwritten. |

## 5. Versioning and reconstruction

| ID | P | Test and expected result |
|---|---:|---|
| VER-01 | P0 | V1 is immutable; attempted edit creates a new version or fails. |
| VER-02 | P0 | Reconstruction cannot start without committed direction and human-confirmed frozen manifest. |
| VER-03 | P0 | Manifest change after confirmation creates a new attempt; it cannot mutate the existing run. |
| VER-04 | P0 | Reconstructed version links source versions, human instruction, transfers, contributions/new ideas, and used memories. |
| VER-05 | P1 | Failed/malformed generation creates a failure attempt and preserves last valid state for retry. |
| VER-06 | P0 | Generation or verification success does not set approval, rejection, or another-cycle status; only one explicit validated-human final-review command does. |

## 6. Persistent memory and retrieval

| ID | P | Test and expected result |
|---|---:|---|
| MEM-01 | P0 | Direction, versions, contributions, criticism, dispositions, and decisions survive reload from CockroachDB in completed MVP. |
| MEM-02 | P1 | Retrieval records query, filters/policy, ordered candidates, exclusions, and mechanism metadata. |
| MEM-03 | P0 | Relevant eligible memory can be selected and linked to the manifest before generation. |
| MEM-04 | P0 | Candidate not selected for context is not described as influencing output. |
| MEM-05 | P0 | Rejected, unauthorized, cross-project, or sensitive record cannot enter context despite high similarity. |
| MEM-06 | P1 | Superseded/conflicting memory is labeled and cannot silently override active human direction. |
| MEM-07 | P1 | No-result/index-failure state is explicit; system does not fabricate memory or silently inject chat history. |
| MEM-08 | P1 | Used fictional memory visibly affects reconstruction and has an element- or section-level origin link. |
| MEM-09 | P1 | Human-development observation memory is absent from generative retrieval by default. |
| MEM-10 | P1 | Selected CockroachDB vector query is actually executed and evidenced, not mocked in the competition run. |

## 7. Provenance integrity

| ID | P | Test and expected result |
|---|---:|---|
| PROV-01 | P0 | Every mandatory event type/subtype used in the run has project, thread, actor/type, timestamps, and content/version references. |
| PROV-02 | P0 | Content hash mismatch, orphan reference, forward cycle, or cross-project lineage is rejected/detected. |
| PROV-03 | P0 | Correction appends a correcting event; original remains inspectable. |
| PROV-04 | P1 | Timeline deterministically orders concurrent timestamps and discloses active filters. |
| PROV-05 | P0 | Reviewer can answer origin, exact agent inputs, transfers/dispositions/reversals/rejections, used memories, V1-to-Final reasons, and final authority from records. |
| PROV-06 | P1 | Multi-origin reconstructed content shows all supported origins and does not reattribute it solely to AI. |

## 8. Verification, comparison, and human-process assessment

| ID | P | Test and expected result |
|---|---:|---|
| QA-01 | P1 | Verification supports `PASS`, `FAIL`, `INCONCLUSIVE`, `NOT_RUN` with method, target, actor, and evidence. |
| QA-02 | P0 | An AI assertion alone cannot be recorded as verified evidence. |
| CMP-01 | P1 | V1-versus-Final displays retained/added/removed content, origins, reasons, fixed rubric results, and evidence. |
| CMP-02 | P1 | Demo Final improves the predefined scenario rubric; failures remain visible rather than hidden. |
| DEV-01 | P0 | Raw observed events, calculated indicators, and interpretations are stored/rendered as separate layers. |
| DEV-02 | P1 | Every indicator exposes calculation version, numerator/denominator or inputs, window, and linked events. |
| DEV-03 | P0 | Output avoids diagnosis, scientific proof, or universal cognitive claims. |
| DEV-04 | P1 | Human new idea is recorded before relevant transfer/retrieval exposure and labeled provenance-relative, not mentally proven. |
| DEV-05 | P1 | Seeded incorrect critic claim can be rejected and linked to verification evidence; no reward exists for rejection alone. |

## 9. Final-review outcomes

| ID | P | Test and expected result |
|---|---:|---|
| FIN-01 | P0 | Validated human calls `approveFinalDecision` on the exact ready version; one `HUMAN_FINAL_DECISION` is persisted, the artifact is `FINAL_SELECTED`, the reconstruction/cycle is approved, and the project closes with that exact approved final. |
| FIN-02 | P0 | Validated human calls `rejectFinalVersion` with reason; one `HUMAN_REJECTION` and immutable rejected outcome are persisted, the exact artifact/reconstruction remains traceable as `FINAL_REJECTED`, the cycle is `REJECTED`, and no `HUMAN_FINAL_DECISION`, final selection, or approved closure exists. |
| FIN-03 | P0 | Validated human calls `requestAnotherCycle` with reason, retained direction, requested corrections, and exact source version; one `HUMAN_DIRECTION` another-cycle event, a new cycle ID, and a human-authored successor cycle-seed/version lineage are persisted, while the previous candidate remains byte-for-byte immutable and is not approved. |
| FIN-04 | P0 | Agent or system actor attempts each of the three final-review commands by direct request; all fail with no human event, outcome record/state, project closure, or successor cycle. A `SYSTEM_EVENT` audit record, if written, cannot create or impersonate the outcome. |
| FIN-05 | P0 | Timeout, inactivity, navigation, refresh, generation/verification success, model text, or UI default occurs at final review; the candidate remains `READY_FOR_FINAL_REVIEW` and no outcome is inferred. |
| FIN-06 | P0 | Approval, rejection, and another-cycle requests race for the same expected candidate/revision; at most one distinct outcome commits, stale competitors conflict, and none is converted to another outcome. |
| FIN-07 | P0 | An exact final-outcome request is replayed with the same idempotency key; exactly one outcome/event exists. Reusing the key with another outcome/payload conflicts. |

## 10. Security and boundary tests

| ID | P | Test and expected result |
|---|---:|---|
| SEC-01 | P0 | Prompt injection inside memory/critic text cannot change instructions, retrieve secrets, authorize transfer, or decide. |
| SEC-02 | P0 | Client payload cannot forge `actorType=HUMAN`; server identity/authorization governs. |
| SEC-03 | P0 | Database/provider/AWS credentials are absent from client bundle, repository, logs, fixtures, provenance, and screenshots. |
| SEC-04 | P1 | Structured/model output is schema-validated; malformed content is quarantined as a failed attempt. |
| SEC-05 | P1 | Partial-write simulation leaves either the complete transactional action or none of it. |
| SEC-06 | P2 | Public repository and history secret scan passes; dependency/license review is recorded. |
| SEC-07 | P1 | Demo fixture audit confirms fictional, non-identifying, non-high-stakes content. |

## 11. End-to-end demonstration and deployment

| ID | P | Test and expected result |
|---|---:|---|
| E2E-01 | P0 | From reset, reviewer completes all 14 demo steps and inspects corresponding persisted records. |
| E2E-02 | P1 | Browser reload at each major stage restores the correct CockroachDB-backed state. |
| E2E-03 | P1 | Deterministic fallback fixture, if used, is clearly labeled and tests protocol behavior without being passed off as live AI. |
| DEP-01 | P1 | At least one selected AWS component is genuinely deployed, reachable/observable, and fulfills its documented role. |
| DEP-02 | P1 | Deployed revision, configuration names, health evidence, and reproduction steps are recorded without secrets. |
| COMP-01 | P1 | Official competition requirements are sourced, dated, mapped, and all mandatory items are `EVIDENCED`. |

## 12. MVP exit rule

The MVP cannot be declared conformant while any P0 fails, any mandatory demonstration P1 fails, a required technical selection remains falsely presented as implemented, or evidence exists only as narrative. The canonical demo may exercise approval, but all `FIN-*` branches and negative authority tests must pass. Waivers are not silent: a human records scope, reason, risk, and why the result is not being claimed as full conformance.
