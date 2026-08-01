# Persistent Memory Architecture

## 1. Definition and scope

Persistent memory is structured, inspectable project knowledge that can be retrieved and demonstrably supplied to later work. It is not synonymous with chat history, a vector index, or an opaque model context.

CockroachDB is the intended later persistence system for relational records, versions, provenance, and vector retrieval. The database client, migration method, embedding provider/model, vector type/index/query implementation, dimensions, and competition-required tooling remain **TBD** until explicitly selected and validated. This document specifies behavior, not those premature choices.

## 2. Memory categories

| Category | Contains | Typical eligibility |
|---|---|---|
| Direction memory | Active and superseded human direction, constraints, success criteria | High priority; active version by default |
| Contribution memory | Human-authored additions and new ideas | When relevant to current reconstruction |
| Critique memory | Human and agent criticism, kept separately by origin | Only with disposition visible |
| Transfer memory | Accepted, rejected, deferred, partial, and reversed transfers | Accepted content may enter context; rejection informs exclusions |
| Decision memory | Human decisions and reasons | Used to avoid contradicting settled choices unless explicitly reopened |
| Version memory | Immutable V1 and reconstructed versions with lineage | Comparison and reconstruction source |
| Evidence memory | Sources, verification methods, outcomes, confidence/status | Used to support or challenge claims |
| Human-development observation memory | Raw process events and bounded indicators | Assessment only; not general agent personalization by default |

Categories do not change authorship. A critic output stored as critique memory remains `CRITIC_OUTPUT`.

## 3. Logical record contract

Each memory record requires `memoryId`, project, category, actor/origin event, source thread, source artifact/version, immutable content or content reference, created timestamp, lifecycle status, sensitivity/eligibility labels, content hash, and schema version. Retrieval-capable records additionally carry embedding status and embedding metadata when selected. Supersession creates a new record and relationship; it does not overwrite history.

Human-development observation memory MUST be isolated from normal generative retrieval unless the human explicitly authorizes a declared use. This prevents behavioral metrics from becoming covert personalization.

## 4. Write path

1. A protocol action creates an immutable artifact and provenance event.
2. A deterministic policy identifies eligible memory units and category.
3. The system preserves source attribution, dispositions, and sensitivity.
4. If semantic retrieval is enabled, an asynchronous or transactional process creates an embedding with recorded model/version and status.
5. Failed indexing is visible and retryable; it does not invalidate the source record.

Agent-produced text is not automatically trustworthy memory. It retains uncertainty and verification status. Rejected content may be stored for traceability but MUST be excluded from generative context unless explicitly reopened by the human.

## 5. Retrieval protocol

Every retrieval run records:

- retrieval ID, project, requesting stage, actor, and time;
- exact query text or immutable query reference;
- eligible categories, thread/project boundary, filters, and policy version;
- retrieval mechanism and configuration (keyword, relational, vector, hybrid, once selected);
- ordered candidates with scores/reasons;
- records excluded by authority, sensitivity, disposition, staleness, or duplication;
- records selected for context and the selecting actor/policy;
- the frozen reconstruction manifest that used them.

Candidate retrieval and actual use are different facts. Only records with an `INCLUDED_IN_CONTEXT` linkage created before reconstruction may be described as influencing that reconstruction.

## 6. Relevance, precedence, and conflict

Retrieval SHOULD combine hard relational filters with relevance ranking. Active human direction and explicit decisions take precedence over semantically similar superseded or AI-authored material. Conflicts are not silently resolved: the context marks the conflict, origin, status, and current human disposition. The human may exclude a candidate, choose between conflicting memories, or request another retrieval.

The application MUST guard against near-duplicate memories overwhelming results. Ranking and thresholds must be versioned and testable against a small fictional evaluation set. Scores are retrieval signals, not truth or authority.

## 7. Visible influence

For each reconstructed element that relies on memory, the interface SHOULD expose the memory reference and relationship. At minimum, the version-level view shows all used memories and where feasible highlights affected sections. A memory badge without a pre-generation context record fails the requirement.

The demonstration must include at least one relevant prior memory omitted from immediate thread text, retrieved from persistence, placed into the frozen manifest, reflected in the reconstruction, and linked from the resulting content.

## 8. Isolation and access boundaries

- Retrieval is project-scoped by default.
- Cross-project retrieval is forbidden unless a future explicit human-authorized policy defines purpose, scope, and provenance.
- Independent agent threads receive only memory records listed in their manifests.
- Vector similarity MUST NOT bypass permissions, disposition, or category restrictions.
- Deleted/expired data behavior and retention are policy decisions; normal provenance corrections do not erase history.
- Raw credentials, secrets, and identifying data are never eligible memory content.

## 9. Failure and recovery

No-result, low-relevance, stale-index, embedding-failure, timeout, and partial-result states are explicit. The system MUST NOT fabricate memory or silently fall back to full chat history. Reconstruction can proceed without memory only if the human is informed, the manifest says none was used, and the run is not presented as satisfying the memory-influence demonstration requirement.

## 10. Minimum evaluation

A fictional retrieval fixture SHOULD contain relevant, irrelevant, conflicting, superseded, rejected, and unauthorized records. Tests verify that relevant eligible records can be found, ineligible records never enter context, used records are linked pre-generation, and the reconstruction visibly reflects at least one used record without obscuring its origin.
