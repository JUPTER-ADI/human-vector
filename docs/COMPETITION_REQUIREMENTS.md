# Competition Requirements and Evidence Matrix

## 1. Purpose

This document is a readiness framework, not a claim that a competition requirement is already satisfied. The identified target is the **CockroachDB × AWS Hackathon — Build with Agentic Memory**. Its published technical requirements and deadline have been mapped from official sources, while participant eligibility, legal applicability, team/submission ownership, public license selection, and completed evidence remain unresolved.

Accepted decision `D-015` and [TECHNICAL_ARCHITECTURE_PROPOSAL.md](./TECHNICAL_ARCHITECTURE_PROPOSAL.md) select the documented minimum competition architecture. Acceptance is not implementation evidence: no CockroachDB client, migration, vector, model, AWS, authentication, or competition-tool integration is implemented by this document. The six-part compatibility spike remains separately blocked pending explicit human authorization.

## 2. Requirement source register

The requirement register uses:

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

Only an official competition source can close an `UNKNOWN`. Marketing summaries are not authoritative where official rules differ.

### 2.1 Dated official-source mapping

Sources accessed 2026-08-02:

- [Official challenge page](https://cockroachdb-ai.devpost.com/) — challenge, technical requirements, required integrations, submission artifacts, judging criteria, and published deadline.
- [Official rules](https://cockroachdb-ai.devpost.com/rules) — legal rules controlling eligibility and submission. A human must verify their applicability to the participant/team.

| Requirement ID | Official requirement summary | Mandatory | Planned evidence | Fulfillment status |
|---|---|---:|---|---|
| `COMP-OFFICIAL-01` | Build an agentic application. | Yes | Separate agent executions, manifests, outputs, and application-time actions | `NOT_STARTED` |
| `COMP-OFFICIAL-02` | Use CockroachDB as the application's persistent memory layer; the agent stores, retrieves, and acts on memory. | Yes | Persisted transactional records, reload proof, retrieval records, and reconstruction lineage | `NOT_STARTED` |
| `COMP-OFFICIAL-03` | Deploy the application on AWS. | Yes | Functional AWS-hosted demo, health evidence, exact revision, and architecture role | `NOT_STARTED` |
| `COMP-OFFICIAL-04` | Use at least two listed CockroachDB tools: Managed MCP Server, Distributed Vector Indexing, `ccloud` CLI, or Agent Skills Repo. | Yes | Two genuine application-time tool traces and an explanation of what each agent/system did | `NOT_STARTED` |
| `COMP-OFFICIAL-05` | Use at least one AWS service that powers the agent's environment. | Yes | Live service invocation/deployment evidence and documented role | `NOT_STARTED` |
| `COMP-OFFICIAL-06` | Submit a public open-source repository with required code, documentation, dependencies, example configuration/data as applicable, setup/run instructions, and a visible open-source license. | Yes | Public release/tag, license, clean history/secret scan, and reproducibility check | `NOT_STARTED` |
| `COMP-OFFICIAL-07` | Submit a functional demo application. | Yes | Judge-accessible URL and smoke-test record | `NOT_STARTED` |
| `COMP-OFFICIAL-08` | Submit a public video under three minutes showing the application and CockroachDB memory layer. | Yes | Public video URL and timed evidence script | `NOT_STARTED` |
| `COMP-OFFICIAL-09` | Identify the CockroachDB tools and AWS services used and explain how they were used. | Yes | Submission narrative linked to persisted/tool evidence | `NOT_STARTED` |
| `COMP-OFFICIAL-10` | Meet the published deadline: August 18, 2026 at 5:00 p.m. EDT. | Yes | Submission receipt and timestamp | `NOT_STARTED` |

Source verification does not establish product fulfillment. Every row remains `NOT_STARTED` until inspectable implementation evidence exists.

## 3. Current known project commitments

These are accepted project commitments and repository requirements, independent of whether the competition requires each one:

- public GitHub repository later;
- CockroachDB-backed persistent memory, provenance, versions, relational records, and vector retrieval;
- at least one genuinely deployed AWS component;
- fictional demonstration data only;
- no committed secrets or credentials;
- a complete human-directed lifecycle with independent threads, selective transfer, memory influence, final human decision, provenance, and V1-versus-Final comparison.

They are designed to support the official challenge but do not establish participant eligibility or completed sponsor criteria.

## 4. Accepted competition-integration architecture

The human accepted the following `D-015` mapping after reviewing the complete proposal, all four documentation changes, its boundaries, risks, alternatives, gates, and spike scope. Architecture acceptance is not competition evidence and does not change any `NOT_STARTED` fulfillment status.

| Required integration | Accepted meaningful running role | Current status |
|---|---|---|
| CockroachDB tool 1: Distributed Vector Indexing | Persist 1,024-dimensional Titan embeddings and execute an actual `project_id`-prefixed cosine vector-index query over eligible fictional memory. Record candidates, exclusions, query plan/index use, and the later human-selected subset supplied to reconstruction. | `ACCEPTED DESIGN — NOT IMPLEMENTED` |
| CockroachDB tool 2: Agent Skills Repo | A non-authoritative Retrieval Safety Agent uses an immutable-pinned, reviewed `cockroachdb-sql` skill against sanitized schema, exact retrieval SQL, redacted `EXPLAIN`, policy, and fictional relevance evidence. It reports CockroachDB-specific query/schema hazards but has no credentials, mutation tool, memory-selection power, transfer authority, or final authority. | `ACCEPTED DESIGN — NOT IMPLEMENTED` |
| AWS hosting: Elastic Beanstalk | Run the unchanged Next.js full-stack production server in a single-instance Node.js 22 environment in region `eu-central-1`. | `ACCEPTED DESIGN — NOT IMPLEMENTED` |
| AWS models: Amazon Bedrock | Titan Text Embeddings V2 produces exactly 1,024 dimensions; Nova 2 Lite runs Builder, Critic, Reconstruction, and Retrieval Safety executions through a suitable EU geographic inference profile with application-side output validation. | `ACCEPTED DESIGN — NOT IMPLEMENTED` |

Managed MCP is excluded from the accepted minimum architecture. It may be reconsidered only as an optional read-only, post-final Evidence Agent after a separate security and meaningful-integration review. `ccloud` CLI is not selected as a minimum competition tool. None of these accepted roles authorizes the compatibility spike, resource creation, deployment, or application implementation.

## 5. Product evidence matrix

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

## 6. Technical evidence to collect after decisions

### CockroachDB

Record cluster/version, schema and migration history, selected client and rationale, tables/relations that hold protocol state, vector feature/query actually exercised, persistence-after-reload proof, representative query/evidence, failure/recovery behavior, and credential handling. Do not claim sponsor-tool use through naming alone.

### AWS

Record the selected service and why it is a meaningful application component, deployment region/account abstraction (no secrets), architecture diagram, build/deployment steps, live endpoint or judge access method, logs/health evidence, cost/cleanup notes, and which repository revision is deployed.

### AI providers

Record builder/critic/specialist roles, input isolation, provider/model/version where available, prompts/instruction versions, retry/failure handling, and proof that the provider cannot exercise human authority. Competition disclosure rules may require additional detail.

## 7. Submission artifact checklist

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

## 8. Pre-submission gates

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

## 9. Open competition decisions

`D-015` now accepts the minimum CockroachDB client/migrations/vector, AWS deployment, model, and two-tool architecture; their live-account, compatibility, and competition evidence remains open and no fulfillment row is evidenced. Before implementation or submission, explicitly decide and record the `D-106` test harness, `D-107` authentication/actor identity, `D-108` retention/administrative policy, `D-109` eligibility/legal/submission compliance, and `D-110` public license/publication plan. The immutable Agent Skill pin and reviewed invocation boundary, live hosting/access details, telemetry, reset procedure, submission owner/timeline, and applicable official-rules interpretation also remain open validation or implementation artifacts. Implementation and the six-part compatibility spike remain separately blocked.
