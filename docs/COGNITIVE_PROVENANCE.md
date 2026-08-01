# Cognitive Provenance Specification

## 1. Purpose

Cognitive provenance is the inspectable chain by which direction, candidate material, criticism, transfer, memory, reconstruction, verification, and human decision produced a version. It protects authorship and authority; it is not decorative metadata or a claim to reveal unrecorded mental processes.

## 2. Required event vocabulary

Every meaningful event uses one of these minimum types:

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

Implementations MAY add subtypes (for example `VERIFICATION_RESULT`), but MUST NOT collapse a human authority action into `SYSTEM_EVENT` or an AI output into a human type.

The following critique-disposition subtypes are required for the MVP:

- `CRITIQUE_DEFERRED` under `HUMAN_CRITIQUE` records disposition `DEFERRED`, the exact critique item, human actor, time, and reason. It carries an explicit empty transferred-content set and creates no `TRANSFERS` or `INCLUDED_IN_CONTEXT` relation.
- `CRITIQUE_DISPOSITION_REVERSED` under `HUMAN_CRITIQUE` references the immediately previous disposition record, records the reason, and reopens the item for review. It preserves all prior events and transfer records, carries an explicit empty transferred-content set, and does not authorize transfer.

`HUMAN_TRANSFER` is reserved for an actual validated-human authorization of exact non-empty content to a declared destination. For criticism, only `acceptCritiqueForTransfer` and `partiallyAcceptCritiqueForTransfer` create it. `HUMAN_REJECTION` records `rejectCritique` and other explicit human rejections.

## 3. Event envelope

Each event MUST contain:

| Field | Requirement |
|---|---|
| `eventId` | Globally unique, stable identifier |
| `projectId` | Owning project |
| `threadId` | Originating thread or explicit human/system workspace thread |
| `actorId`, `actorType` | Identified actor and `HUMAN`, `AGENT`, or `SYSTEM` classification |
| `eventType` | Controlled vocabulary value |
| `eventSubtype` | Controlled subtype when required; otherwise explicit absence |
| `occurredAt`, `recordedAt` | UTC timestamps; preserve distinction if offline/delayed |
| `sourceVersionIds` | Zero or more immutable inputs |
| `targetVersionId` | Output version, when applicable |
| `contentRef` | Immutable artifact/item reference plus content hash |
| `reason` | Required by the relevant authority rule |
| `correlationId`, `causationEventId` | Workflow action and immediate cause |
| `schemaVersion` | Interpretation version |

`HUMAN_TRANSFER` additionally carries exact non-empty selected/transferred item references, source, destination, snapshot/hash, and `ACCEPTED` or `PARTIALLY_ACCEPTED` disposition. `HUMAN_REJECTION` carries the exact rejected references. Critique-disposition subtypes carry the critique item, previous disposition reference when applicable, resulting disposition, and explicit empty transfer/context sets. Retrieval and reconstruction carry candidate and used memory references. Absence is an empty explicit set, not an unknown implicit context.

## 4. Artifact granularity and lineage

Meaningful elements require stable item identities, not just message-level authorship. A criticism list, for example, contains separately addressable criticism items. Selection stores an immutable snapshot/hash so later rendering cannot change what was authorized.

Lineage edges SHOULD use explicit relations such as `DERIVED_FROM`, `CRITIQUES`, `RESPONDS_TO`, `TRANSFERS`, `RETRIEVED_FROM`, `INCLUDED_IN_CONTEXT`, `VERIFIES`, `REJECTS`, `SUPERSEDES`, and `DECIDES_ON`. A final paragraph may have multiple origins; the interface MUST show all supported origins rather than selecting a convenient single author.

## 5. Append-only integrity rules

- Events and versions are never edited or deleted in the normal protocol path.
- A correction appends a correcting event that points to the corrected event and explains the change.
- Timestamps, IDs, actor types, content hashes, and authority decisions are server-recorded where possible.
- Ordered display uses a deterministic order such as `(occurredAt, recordedAt, eventId)` while retaining both timestamps.
- A transaction SHOULD atomically persist an authority action, its disposition, and the corresponding provenance event.
- Orphan references, impossible forward lineage, mismatched hashes, and cross-project references are integrity failures.

Cryptographic signing is not required for the MVP. Hashes detect unintended content mismatch; they do not by themselves prove actor identity.

## 6. Thread input manifests

Every agent run has an immutable input manifest listing exact direction/version, artifacts, selected item ranges, memory records, system instructions by version, model/provider metadata when available, and explicit exclusions. “Conversation so far” is not an acceptable manifest. Critic independence is evidenced by its manifest, not its label.

Prompt templates and system instructions may be stored by reference if the referenced version is immutable and inspectable by an authorized reviewer. Secrets MUST be redacted without hiding substantive instructions that affect behavior.

## 7. Deferral, rejection, reversal, and later transfer

Deferral and rejection are separate first-class provenance:

- Deferral appends `HUMAN_CRITIQUE` / `CRITIQUE_DEFERRED`; it is not a transfer or rejection.
- Rejection appends `HUMAN_REJECTION` with `REJECTS` and a reason.
- Both remain visible and excluded from downstream manifests.

`reverseCritiqueDisposition` appends `HUMAN_CRITIQUE` / `CRITIQUE_DISPOSITION_REVERSED`, references the immediately previous disposition, requires a reason, retains all prior records, and projects the critique item back to open review. Reversal creates no `HUMAN_TRANSFER`, `TransferDecision`, `TRANSFERS`, or `INCLUDED_IN_CONTEXT` relation. If the human later wants the reopened criticism transferred, the human must separately call `acceptCritiqueForTransfer` or `partiallyAcceptCritiqueForTransfer`; only that later command creates the transfer authorization and `HUMAN_TRANSFER` event. Previously frozen manifests remain unchanged.

## 8. Inspectable views

The application MUST be able to render:

- an ordered timeline with actor, type, thread, and artifact;
- a thread-separated view showing input manifests and outputs;
- a version lineage graph or equivalent source list;
- an element-level origin view for reconstructed content;
- transfer, critique-disposition, reversal, and rejection ledgers;
- a retrieval-to-reconstruction evidence view;
- a decision chain from direction to final decision.

Filters may simplify a view but MUST clearly disclose hidden events and provide access to the complete chain.

## 9. Provenance queries required for the MVP

The system must answer, from records rather than narrative:

1. Who introduced this element, in which thread, and when?
2. What exact inputs did this agent receive?
3. Which critic items did the human accept, partially accept, defer, reject, or reopen by reversal, and which exact later actions actually authorized transfer?
4. Which memories were retrieved, selected, and actually supplied to reconstruction?
5. Why did the final differ from V1?
6. Which human action authorized each authority-bearing transition?
7. What unresolved criticism or failed verification remained at final decision?

## 10. Privacy boundary

Provenance records only application-visible actions and declared relationships. It MUST NOT claim hidden intent, mental authorship, or psychological state. Sensitive prompt/log material follows the retention and access rules in [SECURITY_AND_BOUNDARIES.md](./SECURITY_AND_BOUNDARIES.md).
