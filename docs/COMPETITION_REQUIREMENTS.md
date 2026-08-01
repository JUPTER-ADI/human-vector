# Competition Requirements and Evidence Matrix

## 1. Purpose

This document is a readiness framework, not a claim that any unnamed competition requirement is already satisfied. The target competition, official rules, submission deadline, judging rubric, required CockroachDB tools/features, AWS requirements, repository/publication terms, licenses, and disclosure obligations are **TBD** until official sources are selected and recorded.

No implementation choice should be inferred from this checklist. CockroachDB client/migrations/vector implementation, AI provider/model, and AWS service remain undecided.

## 2. Requirement source register

For every official requirement, record:

| Field | Meaning |
|---|---|
| Requirement ID | Stable local identifier |
| Exact source | Official URL/document and section |
| Source version/date accessed | Protection against rule changes |
| Requirement summary | Faithful, concise interpretation |
| Mandatory/optional | Submission consequence |
| Owner | Person responsible |
| Planned evidence | Artifact that proves compliance |
| Status | `UNKNOWN`, `NOT_STARTED`, `IN_PROGRESS`, `EVIDENCED`, `BLOCKED`, `NOT_APPLICABLE` |
| Evidence location/date | Inspectable proof |
| Notes/risks | Ambiguity or follow-up |

Only an official rule source can close an `UNKNOWN`. Marketing summaries are not authoritative where official rules differ.

## 3. Current known project commitments

These are project requirements from the current context, not verified competition rules:

- public GitHub repository later;
- CockroachDB-backed persistent memory, provenance, versions, relational records, and vector retrieval;
- at least one genuinely deployed AWS component;
- fictional demonstration data only;
- no committed secrets or credentials;
- a complete human-directed lifecycle with independent threads, selective transfer, memory influence, final human decision, provenance, and V1-versus-Final comparison.

Whether these satisfy eligibility or sponsor criteria remains to be checked against official rules.

## 4. Product evidence matrix

| Capability | Minimum inspectable evidence | Failure condition |
|---|---|---|
| Human authority | Human-only authorization records and negative authorization tests | Agent/system can transfer or finalize |
| Independent threads | Distinct IDs and immutable input manifests | Hidden shared conversation/context |
| Controlled contradiction | Itemized critic output and human responses | Generic disagreement with no response stage |
| Human new idea | Separate human event and provenance-relative novelty check | Reattributed AI proposal |
| Selective transfer | Accepted/rejected/deferred ledger and exact snapshots | Entire thread silently included |
| Persistent memory | Database records survive reload | In-memory/demo-only state |
| Vector retrieval | Recorded query/config/results from the selected CockroachDB mechanism | “Vector” asserted without executed evidence |
| Visible memory influence | Pre-generation context link and resulting content lineage | Post-generation retrieval badge |
| Provenance | Complete timeline and queryable decision chain | Decorative labels or missing rejections |
| Solution improvement | Predefined V1/Final rubric with verification | Subjective “better” statement only |
| Human-process assessment | Events, reproducible indicators, bounded interpretation | Psychological or causal overclaim |
| AWS deployment | Live component, architecture role, deployment evidence, reproducible instructions | Logo/config stub only |
| Security | Secret scan, server-only configuration, fictional data | Exposed credentials or real personal data |

## 5. Technical evidence to collect after decisions

### CockroachDB

Record cluster/version, schema and migration history, selected client and rationale, tables/relations that hold protocol state, vector feature/query actually exercised, persistence-after-reload proof, representative query/evidence, failure/recovery behavior, and credential handling. Do not claim sponsor-tool use through naming alone.

### AWS

Record the selected service and why it is a meaningful application component, deployment region/account abstraction (no secrets), architecture diagram, build/deployment steps, live endpoint or judge access method, logs/health evidence, cost/cleanup notes, and which repository revision is deployed.

### AI providers

Record builder/critic/specialist roles, input isolation, provider/model/version where available, prompts/instruction versions, retry/failure handling, and proof that the provider cannot exercise human authority. Competition disclosure rules may require additional detail.

## 6. Submission artifact checklist

Subject to official rules, prepare:

- public repository at an exact commit/tag with an approved license;
- README with problem, fixed identity, architecture, setup, demo, limitations, and security notes;
- reproducible fictional demo and reset path;
- short video showing application state for all 14 demonstration steps;
- architecture diagram showing browser/app, agent boundaries, CockroachDB, and AWS component;
- database schema/migrations and evidence of actual vector retrieval;
- deployed URL or access instructions;
- test report mapped to [ACCEPTANCE_TESTS.md](./ACCEPTANCE_TESTS.md);
- provenance export or screenshots for the canonical run;
- V1-versus-Final and human-process evidence;
- attribution, third-party licenses, AI-use disclosures, and team/eligibility declarations;
- explicit limitations and TBDs resolved before submission.

Screenshots should supplement live/persisted evidence, not substitute for it.

## 7. Pre-submission gates

### Gate A — Rules verified

Official rules are archived or linked, eligibility is confirmed, sponsor criteria are mapped, prohibited content/services are checked, and all deadlines/time zones are recorded.

### Gate B — Behavior complete

Mandatory acceptance tests pass, demonstration can be run from reset, thread isolation and human authority negative tests pass, and no required stage is simulated without disclosure.

### Gate C — Infrastructure genuine

CockroachDB persistence/vector behavior and the AWS component are live and evidenced; selected tools are no longer marked TBD in decision records.

### Gate D — Security and publication

Secrets and history are scanned, fictional fixtures are reviewed, dependencies/licenses are checked, public configuration is safe, and logs/screens contain no credentials or identifying data.

### Gate E — Claims calibrated

Public text follows [ORIGINALITY_AND_POSITIONING.md](./ORIGINALITY_AND_POSITIONING.md), the demo is not described as scientific proof, and every material claim has evidence.

## 8. Open competition decisions

Before implementation or submission, explicitly decide and record: target competition/rules version, required CockroachDB tooling, database client/migrations/vector approach, AWS service/deployment boundary, AI provider/model, test harness, public license, hosting/access method, telemetry policy, retention/reset policy, and submission owner/timeline. Until then, these remain unresolved rather than silently assumed.
