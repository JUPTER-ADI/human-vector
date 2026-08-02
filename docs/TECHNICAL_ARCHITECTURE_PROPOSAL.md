# HUMAN VECTOR Technical Architecture Proposal

## Decision status, approval, and scope

This document is the complete audited technical architecture accepted by decision `D-015` on 2026-08-02. The human explicitly approved `D-015` after reviewing this complete proposal; the four-document change set comprising this file, [DECISION_LOG.md](./DECISION_LOG.md), [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md), and [COMPETITION_REQUIREMENTS.md](./COMPETITION_REQUIREMENTS.md); and the architecture boundaries, risks, rejected and deferred alternatives, approval gates, and exact six-part compatibility-spike scope.

Acceptance selects the documented minimum technical architecture. It does not alter or supersede accepted decision `D-014`, represent any component as implemented, or authorize application implementation. Decision `D-016`, accepted separately on 2026-08-02, authorizes only the exact six-part compatibility spike in section H. This documentation task does not execute that spike. Application code and all work outside the bounded spike remain unchanged and unauthorized.

## A. Verified repository facts

The following facts were verified directly from the repository on 2026-08-02:

- The application is a minimal full-stack Next.js `16.2.12` App Router scaffold using React `19.2.4`, TypeScript 5, Tailwind CSS 4, ESLint 9, and the standard `next dev`, `next build`, and `next start` scripts.
- The application surface currently consists of the root layout, one starter route, global styling, and static starter assets. No HUMAN VECTOR workflow is implemented.
- `package.json` contains no database client, migration tool, AWS SDK, model provider, authentication library, or test harness.
- Accepted decision `D-014` fixes the database-neutral domain model and server-side human-authority boundary. It does not select a physical schema, database client, migrations, vector implementation, authentication product, model, AWS service, or test framework.
- Accepted decision `D-015` selects the minimum physical architecture documented here while preserving every `D-014` human-authority invariant and the separate compatibility and implementation gates.
- Under `D-014`, only a server-attested validated human can exercise direction, cross-thread transfer, reconstruction-input authorization, critique disposition, and final-review authority. AI output remains proposed content.
- `D-014` requires distinct Builder, Independent Critic, and Reconstruction threads/runs; frozen manifests; optimistic concurrency; idempotency; immutable versions; append-only provenance; and atomic authority action plus provenance persistence.
- `retrieveMemory` may be initiated by a validated human or trusted `SYSTEM` workflow, never by an AI-provider actor. Retrieval returns candidates only; it cannot select used memory, change direction, transfer content, or create a final decision.
- Accepted decisions `D-011` and `D-012` require CockroachDB persistence/vector evidence and a meaningful AWS component in the completed MVP, while leaving their implementation mechanisms open.
- The canonical fictional Lumen Bay demonstration requires persistent transactional memory, semantic retrieval, independent Builder and Critic work, human-controlled transfer, reconstruction, verification, an explicit human final decision, provenance, V1-versus-Final comparison, and bounded human-development assessment.

## B. Externally verified technical facts

These facts were checked against the linked official sources on 2026-08-02. They establish technical plausibility, not live-account entitlement or completed integration.

- The official [CockroachDB × AWS Hackathon page](https://cockroachdb-ai.devpost.com/) requires an agentic application that uses CockroachDB as persistent memory, is deployed on AWS, uses at least two listed CockroachDB tools, and uses at least one AWS service. It also requires the submission to identify how the agent actually used the CockroachDB and AWS tools. The published deadline is August 18, 2026 at 5:00 p.m. EDT. Detailed participant eligibility and legal terms remain subject to the [official rules](https://cockroachdb-ai.devpost.com/rules).
- CockroachDB v25.4 made vector indexing generally available and lists it as available on Basic, Standard, and Advanced in the [v25.4 release notes](https://www.cockroachlabs.com/docs/releases/v25.4).
- CockroachDB's [`VECTOR` type](https://www.cockroachlabs.com/docs/stable/vector) enforces the declared dimensionality and supports cosine distance through `<=>`. A 1,024-dimensional vector is within the documented fixed-dimension and size model.
- CockroachDB [vector indexes](https://www.cockroachlabs.com/docs/stable/vector-indexes) support `vector_cosine_ops` and prefix columns. The optimizer uses a prefixed vector index only when its prefix columns are constrained appropriately, which permits `project_id` to enforce a project-filtered search space.
- CockroachDB Cloud [Standard and Basic regions](https://www.cockroachlabs.com/docs/cockroachcloud/regions) include AWS `eu-central-1` (Frankfurt).
- CockroachDB documents [node-postgres (`pg`) connectivity](https://www.cockroachlabs.com/docs/stable/connect-to-the-database) with `sslmode=verify-full`, and its [Node.js tutorial](https://www.cockroachlabs.com/docs/stable/build-a-nodejs-app-with-cockroachdb) requires client-side retry handling under `SERIALIZABLE` isolation.
- CockroachDB reports retryable serialization failures with SQLSTATE `40001`; its [transaction retry reference](https://www.cockroachlabs.com/docs/stable/transaction-retry-error-reference) requires retrying the whole transaction when client-side intervention is needed.
- Cockroach Labs publishes a public, machine-executable [CockroachDB Agent Skills repository](https://github.com/cockroachlabs/cockroachdb-skills) with explicit boundaries and safety guardrails. Its current catalog includes a `cockroachdb-sql` skill under query and schema design. A repository branch is mutable, so a competition implementation would need an immutable reviewed commit pin and recorded skill hash.
- CockroachDB Basic has usage-based Request Unit and storage charging, with eligibility conditions and resource limits described in [Basic cluster planning](https://www.cockroachlabs.com/docs/cockroachcloud/plan-your-cluster-basic). Free allowance must not be assumed for every account or contract.
- CockroachDB Cloud documents table SQL audit logging, but [audit-log export](https://www.cockroachlabs.com/docs/cockroachcloud/sql-audit-logging) is documented for Standard or Advanced. Basic therefore cannot be assumed to provide the same exported database audit capability; HUMAN VECTOR must rely on its own transactional append-only provenance for protocol evidence.
- AWS Elastic Beanstalk offers a [single-instance environment](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/using-features-managing-env-types.html) consisting of one EC2 instance with an Elastic IP and no load balancer, with Auto Scaling minimum, maximum, and desired capacity fixed at one. It is lower-complexity but not highly available.
- AWS currently lists a supported [Elastic Beanstalk Node.js 22 on Amazon Linux 2023 platform](https://docs.aws.amazon.com/elasticbeanstalk/latest/platforms/platforms-supported.html). The exact platform version is mutable and must be rechecked at deployment time.
- Amazon Bedrock identifies Titan Text Embeddings V2 as `amazon.titan-embed-text-v2:0`; its [model documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html) supports output dimensions of 1,024, 512, or 256, with 1,024 as the default. The selected request must still set `dimensions: 1024` explicitly and validate that exactly 1,024 numeric values are returned.
- AWS lists Titan Text Embeddings V2 for `eu-central-1` and identifies 256, 512, and 1,024 as supported dimensions in its [Bedrock model/region documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-supported.html).
- Amazon Bedrock identifies Nova 2 Lite as `amazon.nova-2-lite-v1:0`. Its [model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-2-lite.html) lists EU geographic inference profile `eu.amazon.nova-2-lite-v1:0` and permits `eu-central-1` as a source region, with possible processing in the documented EU destination regions.

## C. Assumptions requiring live account verification

None of the following is accepted as fact until it is verified in the intended accounts and recorded without secrets:

- A CockroachDB Cloud Basic cluster can be created in AWS Frankfurt for the intended account, on a version with Distributed Vector Indexing enabled, within acceptable RU/storage limits.
- The intended Basic cluster permits the required SQL roles, privileges, connection count, IP allowlisting, schema changes, `VECTOR(1024)`, prefixed cosine vector-index creation, and optimizer use under the actual fictional dataset.
- CockroachDB Basic's operational visibility is sufficient for the demonstration. Exportable database-native audit logs are not assumed; application provenance is the required protocol audit source.
- The selected AWS account can use Titan Text Embeddings V2 in `eu-central-1` and invoke Nova 2 Lite through `eu.amazon.nova-2-lite-v1:0`, with model access, quotas, terms, latency, pricing, and EU geographic routing acceptable to the human.
- Nova 2 Lite output can be made reliable enough through application-side schema validation, quarantine, retry, and failure recording. Model prose or generation success can never exercise authority.
- The unchanged Next.js production server can be packaged for the then-current Elastic Beanstalk Node.js 22 platform without unsupported assumptions about build output, filesystem persistence, server lifetime, streaming, or request duration.
- The selected EC2 instance class, Elastic IP, TLS termination, outbound networking, secret delivery, log retention, and CockroachDB allowlist configuration are available and affordable in `eu-central-1`.
- The official `cockroachdb-sql` Agent Skill remains appropriate after source review. Its exact immutable commit, file hash, license, transitive instructions, and safe invocation contract must be pinned and recorded before use.
- Judges will recognize the Retrieval Safety Agent's actual use of the pinned CockroachDB Agent Skill as a meaningful second CockroachDB tool. The demonstration must show the invocation, inputs, output, safety limitations, and effect on human review rather than merely listing the repository.
- The project's participant eligibility, public-license choice, submission ownership, and all official legal requirements are satisfied. Those are not established by this technical proposal.

## D. Accepted D-015 selections

### D.1 Application, deployment, and regions

- Retain the existing Next.js 16 full-stack application and its Node.js production server.
- Use AWS Elastic Beanstalk in `eu-central-1` (Frankfurt), using a single-instance Node.js 22 on Amazon Linux 2023 environment, subject to the still-unexecuted compatibility and live-account gates.
- Keep the minimum deployment stateless outside CockroachDB. Do not treat the EC2 filesystem or process memory as durable protocol state.
- Use the Elastic Beanstalk instance profile for narrowly scoped Amazon Bedrock invocation. Store secrets only through an approved server-side AWS secret mechanism; no concrete secret service or configuration is accepted by this proposal.
- Use the single instance's Elastic IP as the candidate stable egress address for a narrow CockroachDB Cloud IP allowlist. This behavior must be verified because routing and platform details can change.
- Treat the single-instance environment as a deadline-oriented demonstration deployment, not a highly available production architecture.

### D.2 CockroachDB Cloud, client, and migrations

- Use one CockroachDB Cloud Basic cluster on AWS in `eu-central-1` (Frankfurt), subject to the still-unexecuted compatibility and live-account gates.
- Use the Node.js `pg` client with a small bounded connection pool and full TLS server-certificate verification.
- Handle SQLSTATE `40001` by retrying the complete transaction with a finite attempt limit, bounded backoff/jitter, fresh transaction state, and explicit terminal failure. Human authority commands also retain `D-014` idempotency keys and stale-revision checks; transaction retry must never replay or infer human intent incorrectly.
- Use least-privilege separation between a runtime SQL principal and a migration SQL principal. The runtime principal must have no DDL or broad administrative privileges.
- Use numbered, reviewable, forward SQL migrations. Each migration is immutable after application; corrections are new numbered migrations. Migration execution is a separately authorized operational step and is not performed automatically by ordinary application startup.
- Map `D-014` to transactional tables that preserve immutable artifacts/versions/manifests, append-only provenance and disposition history, current-state projections, command idempotency, and exact lineage. Every successful authority command must commit its state transition, idempotency record, and provenance event atomically. The server command boundary—not database access alone—enforces who may invoke each `D-014` command.

### D.3 Embeddings and semantic retrieval

- Store semantic memory embeddings in a CockroachDB `VECTOR(1024)` column with explicit embedding model/version/status metadata and the source content hash.
- Generate embeddings with Amazon Bedrock Titan Text Embeddings V2, model ID `amazon.titan-embed-text-v2:0`, explicitly requesting exactly 1,024 dimensions and rejecting any response that is not exactly 1,024 finite numeric values.
- Create a Distributed Vector Index whose leading prefix is `project_id` and whose vector operator class is `vector_cosine_ops`.
- Query only inside an exact project boundary and order candidates by cosine distance (`<=>`). Relational eligibility filters for disposition, sensitivity, lifecycle, category, and current authority state remain mandatory; similarity never grants access or authority.
- Persist the retrieval query/hash, policy and embedding versions, project filter, ordered candidates and distances, exclusions and reasons, query-plan/index evidence, failures, and the later human-selected used-memory subset.
- Keep candidate retrieval separate from context authorization. Only the validated human's later `startReconstruction` command can freeze selected memories into a reconstruction manifest and create pre-generation `INCLUDED_IN_CONTEXT` lineage.

### D.4 Agent executions and model boundary

- Invoke Amazon Nova 2 Lite through the EU geographic inference profile `eu.amazon.nova-2-lite-v1:0`, subject to live account, quota, region, routing, and terms verification.
- Run Builder, Independent Critic, and Reconstruction as separate executions with distinct thread/run identities, separately versioned instructions, and immutable input manifests. Do not reuse an opaque model conversation between roles.
- Validate every model result against an application schema. Malformed output is quarantined as a failed attempt; retry creates a new attempt and never overwrites an earlier result.
- Bind all model output to `actorType=AGENT`. Models receive no human-authority command capability and cannot select retrieval candidates, authorize transfer, freeze a reconstruction manifest, verify their own claims as evidence, or create a final-review outcome.
- Preserve explicit human-controlled transfer and the explicit human final decision as mandatory server-enforced transitions. No Builder, Critic, Reconstruction, Retrieval Safety, model, or system execution may infer, initiate, or complete either transition for the human.

### D.5 Competition tool 1 — Distributed Vector Indexing

Distributed Vector Indexing is selected as a required running product capability, not a development label. During the live workflow the trusted system executes the project-filtered cosine query against persisted fictional memory, records the ordered candidates and exclusions, and exposes proof that the prefixed vector index was actually used. The human—not the retrieval system or an AI agent—chooses which eligible candidates enter reconstruction. The Reconstruction Agent then acts on only the human-frozen memory subset, making memory's effect visible in the final lineage.

### D.6 Competition tool 2 — pinned CockroachDB Agent Skill

Use the official `cockroachdb-sql` skill from the CockroachDB Agent Skills repository, pinned to an immutable, human-reviewed commit and recorded file hash. The exact pin is deliberately not fabricated in this architecture record; selecting and reviewing it remains an implementation-gated artifact and does not authorize skill installation or use.

A separate non-authoritative **Retrieval Safety Agent** meaningfully uses that pinned skill during the running workflow:

1. The trusted server supplies only a sanitized, read-only evidence package: the accepted memory table/index design, exact project-filtered cosine retrieval SQL, redacted `EXPLAIN` output, declared eligibility policy, and fictional relevance-test results. It supplies no database credentials, unrestricted schema, raw private data, authority command, or mutation tool.
2. The Retrieval Safety Agent applies the pinned CockroachDB SQL/schema guidance to identify CockroachDB-specific query or schema hazards, including absence of the exact project prefix, distance-operator/opclass mismatch, evidence that the index was not used, unsafe data-type assumptions, missing transaction-retry handling, or a query whose filters could admit ineligible records.
3. It returns an immutable diagnostic artifact containing findings, evidence references, limitations, skill commit/hash, and a proposed `PASS`, `FAIL`, or `INCONCLUSIVE` assessment.
4. The result is advisory. It cannot execute SQL, change schema or configuration, select or exclude a memory candidate, modify a retrieval, transfer content, freeze a manifest, mark a deterministic verification as passed, or make a human decision. The human reviews the diagnostic and decides whether to proceed, correct the design, or request another run.

This provides a judge-visible, application-time agent action attributable to the Agent Skills tool while preserving `D-014`.

### D.7 Authentication sequencing

- Cognito is deferred while the entire workflow is local and uses fictional data. The local functional version may use a conspicuously non-production, server-controlled single test principal so direct `actorType` and cross-project forgery tests can be built without pretending that it is deployment-grade authentication.
- Amazon Cognito, or a separately accepted equivalent, becomes a mandatory gate before public deployment or any remotely reachable human-authority action. It must bind a fresh authenticated session to the server-attested HUMAN actor and project authorization; UI identity and client-supplied actor fields remain untrusted.
- No real user data or multi-user claims are permitted before authentication, retention, and administrative-access decisions are explicitly accepted.

## E. Rejected or deferred alternatives

- **ECS Express Mode/Fargate for the minimum:** rejected from the accepted minimum architecture. It adds image/container work and can create or depend on Fargate tasks/services, load balancing, CloudWatch resources, IAM, networking, and data-transfer paths that are unnecessary for a single deadline-oriented Next.js demonstration. It may be reconsidered for later scaling or high availability.
- **CockroachDB Cloud Managed MCP Server for the minimum:** excluded. It is not needed for the core product workflow, and including it merely as a development assistant would not satisfy the meaningful-integration standard. It may be reconsidered only after the final human decision as an optional read-only **Evidence Agent** over dedicated fictional-data evidence views. That agent would be non-authoritative and unable to affect retrieval, context, transfer, verification state, or final outcomes. Its runtime authentication, least-privilege behavior, auditability, and Basic-plan fit would require a new review and explicit approval.
- **`ccloud` CLI as a competition tool:** rejected from the minimum because cluster/network administration by an agent expands permissions and destructive/cost risk without strengthening the core human-authority demonstration.
- **Cognito before the local workflow:** deferred because it would delay proof of the core protocol. Cognito or an accepted equivalent remains mandatory before public deployment.
- **Load-balanced Elastic Beanstalk, ECS/EKS, multi-region application deployment, Bedrock Agents, and Bedrock Knowledge Bases:** deferred. They add operational surface without being necessary to demonstrate the minimum protocol, and Bedrock Knowledge Bases would duplicate the required CockroachDB vector memory role.
- **Any automatic agent-to-agent transfer or autonomous finalization:** rejected as incompatible with `D-014`, regardless of model or orchestration service.

## F. Cost and security risks

### Cost risks

- CockroachDB Basic charges for Request Units and storage beyond any account-eligible allowance. Vector-index maintenance, similarity queries, migrations, retries, and repeated demo resets consume RUs; a low resource cap may disable the cluster, while no cap risks surprise charges.
- Elastic Beanstalk has no separate service fee, but the created EC2 instance, Elastic IP/public IPv4, EBS volume, deployment artifact storage, CloudWatch logs/alarms, outbound data, DNS/certificates, and any secret service can incur charges. A forgotten single-instance environment continues to cost money.
- Bedrock embeddings and Nova invocations are usage-priced. Separate Builder, Critic, Reconstruction, Retrieval Safety, validation retries, and repeated rehearsals multiply requests. Geo inference pricing and quotas must be checked live.
- Free tiers, credits, and model access are account- and date-dependent. None is a budget guarantee.

### Security and reliability risks

- A public single EC2 instance is a single point of failure and has no load-balancer protection or high availability. OS/platform patching, HTTPS termination, security groups, proxy limits, health checks, log redaction, and recovery need explicit configuration review.
- A stable public egress allowlist is simpler than open database access but does not authenticate the application. CockroachDB still requires full TLS verification, strong rotated credentials, narrow SQL roles, project-scoped queries, and server-only secrets.
- CockroachDB Basic must not be represented as providing exported database-native audit logs equivalent to Standard/Advanced. The application's transactional append-only provenance and security-event records are the protocol evidence; their integrity and administrative access still require threat review.
- `pg` transaction retries can duplicate side effects if model calls or other external actions are placed inside a retried SQL closure. Retried transactions must contain only deterministic database work, and authority idempotency must prevent duplicate logical outcomes.
- Retrieved memory and all model output are prompt-injection-capable untrusted data. Delimited manifests, role-specific tool denial, schema validation, project/eligibility filters, and server-side authority enforcement are mandatory.
- The Agent Skill is executable third-party instruction content. It requires immutable pinning, source/license review, hash recording, constrained inputs, no credentials or mutation tools, output validation, and provenance. Skill output is not proof by itself.
- EU geographic inference can route Nova input among documented EU regions. It is not equivalent to Frankfurt-only processing. Fictional data remains mandatory unless a later privacy decision accepts the provider boundary.
- Deferring Cognito is safe only for a local, non-public, fictional workflow. Public authority actions without server-attested authentication are prohibited.

## G. Approval gates

The following gates are cumulative. The architecture and bounded spike-authorization gates are satisfied; the spike-evidence and all later gates remain unsatisfied:

1. **Architecture decision gate — SATISFIED:** on 2026-08-02, the human accepted `D-015` after the complete review recorded above. This selects the architecture but does not authorize application implementation.
2. **Compatibility-spike authorization gate — SATISFIED:** on 2026-08-02, the human accepted `D-016`, authorizing only the bounded six checks in section H. The spike has not been executed. No production feature work or permanent cloud environment is part of that authorization.
3. **Spike-evidence gate:** the six checks in section H pass with versioned, non-secret evidence. Any material failure returns the affected choice to proposal/review; it is not silently worked around.
4. **Physical-design gate:** schema/migrations, runtime roles, retry/idempotency behavior, model output schemas, skill commit/hash, deployment packaging, and secret/network boundaries receive review before core implementation.
5. **Local protocol gate:** the complete fictional workflow and all P0 authority/transfer/provenance tests pass locally before authentication or public-deployment work is treated as complete.
6. **Public-authentication gate:** Cognito or a separately accepted equivalent, actor/project authorization, retention policy, abuse tests, and secret/log review pass before any public endpoint exposes human-authority actions.
7. **Live-account and cost gate:** CockroachDB and AWS account availability, regions, quotas, routing, pricing, budget alerts/limits, and teardown ownership are verified immediately before resource creation.
8. **Competition-evidence gate:** the deployed revision genuinely demonstrates both selected CockroachDB tools and Amazon Bedrock/Elastic Beanstalk roles, with persisted evidence and no claim based only on documentation.

`D-015` resolves the architecture choices tracked by `D-101` through `D-105`, while their compatibility, live-account, and operational evidence remains open. `D-106` through `D-110` remain `TBD`; `D-107` carries only the accepted authentication-sequencing constraint. No decision status grants implementation authority.

## H. Reversible first compatibility spike

Decision `D-016` explicitly authorizes this bounded, disposable compatibility spike. It has **not** been executed. Authorization is limited to fictional test data and only these six checks:

1. Node.js 22 plus `pg` TLS connectivity with full server-certificate verification to a disposable CockroachDB Cloud Basic target.
2. CockroachDB transaction-retry behavior, including an observed SQLSTATE `40001`, whole-transaction retry, bounded failure, and no duplicate logical authority event under one idempotency key.
3. Titan Text Embeddings V2 invoked with `dimensions: 1024`, with validation that the returned vector contains exactly 1,024 finite numeric values.
4. Creation and actual use of a project-filtered cosine Distributed Vector Index on `VECTOR(1024)`, with project isolation, cosine ordering, isolation fixtures, and `EXPLAIN` evidence showing index use.
5. Nova 2 Lite output-validation behavior through the suitable EU geographic inference profile, including valid, malformed, quarantined, retry, and terminal-failure paths without any authority transition.
6. Packaging of the unchanged Next.js production server for a disposable single-instance Elastic Beanstalk Node.js 22 environment, proving build, startup, health, and a basic server response without adding deployment architecture to the application.

The authorization makes no production claim and permits no permanent architecture expansion, full domain mapping, application implementation, public deployment, authentication implementation, or irreversible or production resource. Any external resource, account configuration, credential entry, paid action, or package installation not already safely available must be separately reported before execution. A failed prerequisite must stop the affected check and be reported honestly; it must not be silently bypassed.

The spike is a compatibility test, not application implementation authorization. Its evidence must be reviewed by the human, and subsequent application implementation still requires separate explicit authorization. `D-016` does not modify, supersede, or reinterpret `D-014` or `D-015`, and no check may create an authority transition.

STATUS: ACCEPTED
IMPLEMENTATION: BLOCKED PENDING SEPARATE EXPLICIT HUMAN AUTHORIZATION
COMPATIBILITY SPIKE: AUTHORIZED BY D-016 — NOT EXECUTED
