# HUMAN VECTOR — Human-Directed Agentic Memory

## Fixed Project Identity

HUMAN VECTOR is a human-directed protocol and application. The human preserves direction, authority, selection, and final decision. AI is an instrument that can create information pressure, contrast, alternatives, and cognitive resistance; it is not an authority.

The protocol does not claim that AI alone educates or develops the human. It requires the human to transform AI-created pressure into criticism, comparison, independent ideas, justification, verification, selection, and decision.

The system must produce two distinct, measurable outcomes:

1. a stronger solution, supported by verification and a V1-versus-Final comparison; and
2. a stronger and more autonomous human process, assessed only through bounded, observable application evidence.

Observed events, calculated indicators, and interpretive claims must remain separate. A limited demonstration must never be presented as psychological diagnosis, scientific proof, or a universal claim about human cognition.

## Fixed Operational Cycle

Human Direction  
→ Builder Agent creates V1  
→ Human Contribution  
→ Human Critique  
→ Independent Critic Agent  
→ Controlled Contradiction  
→ Human-Controlled Transfer  
→ Persistent Memory Retrieval  
→ Human-Directed Reconstruction  
→ Verification  
→ Human Final Decision  
→ Provenance  
→ V1-versus-Final comparison  
→ Human development assessment

Stages may repeat, but they must never erase authorship, rejection, version history, memory use, or the human action authorizing a transition.

## Human Authority and Thread Model

Only the human may establish or change project direction, authorize transfer between independent threads, accept or reject criticism, approve reconstruction, and make the final decision. The application may assist, recommend, compare, retrieve, and warn, but must not represent an automated or AI action as human authority.

Builder, Independent Critic, and optional Specialist work must use distinct, traceable thread identities and inspectable input manifests. Threads must not silently share full context. Every cross-thread transfer must be explicit, selective, human-authorized, and recorded. Rejected suggestions remain visible and excluded unless a later human action reverses the disposition with a reason.

## Protocol Specification Set

The initial context and plan are supported by ten expanded protocol documents:

1. [PROTOCOL_CORE.md](./PROTOCOL_CORE.md) — normative authority rules, operational stages, state transitions, contradiction, transfer, reconstruction, verification, and conformance.
2. [HUMAN_DEVELOPMENT_MODEL.md](./HUMAN_DEVELOPMENT_MODEL.md) — bounded observations, reproducible indicators, interpretation limits, and anti-gaming safeguards.
3. [COGNITIVE_PROVENANCE.md](./COGNITIVE_PROVENANCE.md) — required event vocabulary, event envelopes, element-level lineage, rejection history, and inspectable decision chains.
4. [MEMORY_ARCHITECTURE.md](./MEMORY_ARCHITECTURE.md) — persistent-memory categories, logical records, retrieval behavior, eligibility, and proof of influence on reconstruction.
5. [DEMONSTRATION_DESIGN.md](./DEMONSTRATION_DESIGN.md) — the fictional Lumen Bay demonstration and the persisted evidence required for all 14 stages.
6. [ORIGINALITY_AND_POSITIONING.md](./ORIGINALITY_AND_POSITIONING.md) — the combined differentiating structure, adjacent-category contrasts, and calibrated public claims.
7. [COMPETITION_REQUIREMENTS.md](./COMPETITION_REQUIREMENTS.md) — requirement-source register, evidence matrix, readiness gates, and unresolved competition inputs.
8. [SECURITY_AND_BOUNDARIES.md](./SECURITY_AND_BOUNDARIES.md) — authority, context, prompt-injection, provenance, memory, secret, and operational boundaries.
9. [ACCEPTANCE_TESTS.md](./ACCEPTANCE_TESTS.md) — implementation-independent P0/P1/P2 behavioral acceptance tests and the MVP exit rule.
10. [DECISION_LOG.md](./DECISION_LOG.md) — accepted foundational decisions and explicitly unresolved technical decisions.

These documents are a single specification set. `PROTOCOL_CORE.md` defines normative behavior; `ACCEPTANCE_TESTS.md` defines conformance evidence; `DECISION_LOG.md` records accepted and open choices. If implementation convenience conflicts with human authority, traceability, or a normative invariant, the protocol takes precedence.

## Persistent Memory and Provenance

Persistent memory must do more than store chat history. It must preserve direction, immutable versions, human contributions, criticism, transfer dispositions, decisions, evidence, and human-development observations in distinct categories. Retrieval candidates and records actually used in generation are different facts. Memory may be described as influencing reconstruction only when the exact record was linked into a frozen reconstruction manifest before generation and its effect remains inspectable.

Every meaningful element must retain its actor, event type, project, thread, timestamps, source and target versions, disposition, selected/transferred content, memory use, and required justification. Provenance is an operational decision chain, not a decorative label.

## Demonstration Boundary

The canonical demonstration is the fictional Lumen Bay Night Museum Trail defined in `DEMONSTRATION_DESIGN.md`. It must show all protocol stages through persisted application state and records, including a false critic claim rejected by the human, a provenance-distinct human new idea, selective transfer, relevant persistent-memory use, verification, final human decision, V1-versus-Final improvement, and a bounded human-process assessment.

No real personal, medical, legal, financial, family, confidential, or identifying data may be used.

## Technical Baseline and Open Selections

The repository currently provides a minimal Next.js 16.2.12, React 19.2.4, TypeScript 5, and Tailwind CSS 4 scaffold. Application implementation must follow the version-specific Next.js documentation in `node_modules/next/dist/docs/` as required by `AGENTS.md`.

The intended completed MVP uses CockroachDB for persistent memory, provenance, versions, relational records, and vector retrieval, and deploys at least one meaningful component on AWS. The following remain explicitly **TBD** until separately selected and recorded:

- CockroachDB client and connection strategy;
- schema and migration method;
- vector type, indexing, retrieval, and embedding approach;
- AI provider, models, prompt boundary, and structured-output method;
- AWS service and deployment architecture;
- test harness;
- authentication and actor-identity design;
- retention, deletion, export, and administrative-access policy;
- target competition and official requirements;
- public repository license and publication plan.

No document should imply that a TBD technology has already been selected or implemented.

## MVP Outcome

Using fictional data, a reviewer must be able to complete the entire human-directed lifecycle, reload persisted state, inspect independent thread manifests and selective transfers, trace every meaningful element and rejection, prove which memories entered reconstruction, verify the final result, see the explicit human final decision, compare V1 with Final, and inspect the bounded evidence of human-process change. A completed MVP additionally requires genuine CockroachDB persistence/vector behavior and at least one evidenced AWS-deployed component.
