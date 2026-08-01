# Fictional Demonstration Design

## 1. Scenario

The demonstration uses a fictional civic design task with no real personal data:

> Design a seven-day “Night Museum Trail” for the imaginary city of Lumen Bay. The final plan must serve three fictional museums, use a fixed fictional budget of 120 credits, provide a low-sensory option, avoid collecting visitor identities, and include measurable success criteria.

All places, people, evidence, budgets, and constraints are fixtures marked fictional. This scenario is neither medical, legal, financial, family, nor personally identifying.

## 2. Preloaded persistent memory

Before the run, the project contains inspectable fictional memories:

- `M-DIR-01`: an earlier human decision that no visitor account or identity tracking is allowed;
- `M-EVID-01`: a verified fictional venue note that Harbor Museum's quiet room is unavailable on day 6;
- `M-DEC-01`: a prior human decision to measure completion with anonymous stamp cards and aggregate manual counts;
- `M-IRREL-01`: an irrelevant daytime café promotion;
- `M-REJ-01`: a rejected AI suggestion to use facial recognition for queue estimates.

Only eligible, relevant records may enter reconstruction. The rejected facial-recognition suggestion remains traceable but excluded.

## 3. Scripted protocol run

### 3.1 Human direction

The human records the scenario constraints and defines success as a feasible schedule, constraint coverage, transparent budget, accessible choice, and privacy-preserving measurement. Evidence: committed direction version and `HUMAN_DIRECTION` event.

### 3.2 Builder V1

The Builder Thread receives only the committed direction. V1 proposes a schedule and budget but omits a low-sensory route, allocates 130 credits, and confidently schedules the Harbor quiet room on day 6. It also suggests an optional registration form. These are deliberate evaluation weaknesses, not hidden production behavior. Evidence: Builder input manifest, output artifact, immutable V1, `BUILDER_OUTPUT` event.

### 3.3 Human contribution

Before critic output is shown, the human proposes staggered entry windows and a portable “quiet kit” shared across venues. Evidence: separate `HUMAN_CONTRIBUTION` records, not edits to V1.

### 3.4 Human critique

The human identifies the budget excess and the missing low-sensory route, and questions registration against the privacy constraint. Evidence: itemized `HUMAN_CRITIQUE` linked to V1.

### 3.5 Independent critic

The Critic Thread receives V1, the committed direction, and selected human contribution artifacts through a declared snapshot—not Builder conversation history. It challenges the budget, accessibility omission, privacy conflict, and unsupported day-6 room assumption. It also makes one intentionally incorrect claim: that staggered entry necessarily costs 20 credits. Evidence: independent manifest and itemized `CRITIC_OUTPUT`.

### 3.6 Controlled contradiction and new human idea

The human compares the critique with the fictional evidence, rejects the unsupported 20-credit claim, accepts the room-availability challenge, and creates a new idea not proposed by either AI: pair the portable quiet kit with a color-coded, self-selected low-sensory route that requires no identity collection. Evidence: response dispositions, verification link, and `HUMAN_NEW_IDEA` created before transfer/reconstruction.

### 3.7 Selective transfer

The human transfers only the budget, accessibility, privacy, and room-availability criticism into reconstruction; rejects the cost claim with reason; and leaves an optional marketing suggestion deferred. Exact item snapshots and destination are recorded. Evidence: `HUMAN_TRANSFER` and `HUMAN_REJECTION` events and transfer ledger.

### 3.8 Persistent memory retrieval

The human authorizes a retrieval query for prior privacy decisions, venue constraints, and measurement methods. The system returns candidates, excludes irrelevant/rejected records, and the human confirms `M-DIR-01`, `M-EVID-01`, and `M-DEC-01` for the reconstruction manifest. Evidence: query, candidate list, exclusions, selected set, and `INCLUDED_IN_CONTEXT` links created before generation.

### 3.9 Human-directed reconstruction

The human instructs reconstruction to preserve useful V1 structure, apply selected criticism, incorporate the new route idea, stay at or below 120 credits, and use retrieved privacy-safe measurement. The reconstructed version uses the day-6 constraint, replaces registration, adds the route/quiet kit, and balances the budget. Evidence: frozen manifest, agent run, immutable reconstructed version, element origins.

### 3.10 Verification

The human checks the arithmetic, all direction constraints, the day-6 venue note, privacy method, and schedule consistency. Results include pass/fail/inconclusive states. The seeded false critic claim is explicitly marked unsupported. Evidence: verification records and linked fixture evidence.

### 3.11 Final decision

After viewing unresolved issues, the human accepts the identified reconstructed version and gives a reason. The system cannot perform this action. Evidence: `HUMAN_FINAL_DECISION`.

## 4. Required application-state views

The demo is valid only if a reviewer can inspect persisted records for all 14 visible steps:

| Step | Visible proof |
|---|---|
| Initial direction | Committed direction artifact and human event |
| Builder V1 | Builder-only manifest, version, output attribution |
| Human contribution | Separate human artifacts |
| Human criticism | Itemized critiques linked to V1 |
| Independent critic | Different thread and manifest |
| New human idea | Human origin, creation time, novelty-relative evidence |
| Selective transfer | Accepted/rejected/deferred item ledger |
| Retrieved memory | Query, candidates, exclusions, used records |
| Reconstructed version | Frozen manifest and source lineage |
| Human verification | Check records and evidence |
| Final decision | Explicit human event on exact version |
| Provenance timeline | Ordered, filterable complete chain |
| V1-versus-Final | Changes, origins, reasons, criteria results |
| Human process difference | Raw events, calculated indicators, bounded interpretation |

Refresh/reload MUST preserve the state once CockroachDB persistence is implemented.

## 5. V1-versus-Final comparison rubric

Compare fixed criteria: budget correctness, schedule feasibility, low-sensory access, privacy constraint, evidence support, measurement clarity, and retained useful structure. Each result links to changed content and verification evidence. A simple text diff may supplement but cannot replace the criterion view.

Expected improvement is scenario-specific: V1 fails or is unsupported on multiple criteria; Final satisfies the declared criteria after verification. The comparison MUST also reveal the origins of improvements—human critique, critic transfer, human new idea, and retrieved memory—without attributing all change to the reconstruction agent.

## 6. Human-process assessment

The view reports, without universal claims: time to first weak point under the declared clock policy; two pre-critic human contributions; human detection of defined V1 weaknesses; rejection of one verified-invalid AI claim; one provenance-distinct new human idea; verification actions before final decision; and decision justifications. It then offers a bounded interpretation consistent with [HUMAN_DEVELOPMENT_MODEL.md](./HUMAN_DEVELOPMENT_MODEL.md).

## 7. Demo reset and reproducibility

The fixture has stable IDs or deterministic aliases, declared expected facts, no network dependency for ground truth, and a reset that affects only fictional demonstration data. Agent prose may vary, so acceptance depends on protocol records and seeded facts rather than exact wording. A guided fallback fixture MAY provide deterministic agent outputs for judging system behavior, clearly labeled as fixture output.
