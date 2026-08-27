# HUMAN VECTOR — Current Architecture

## Reciprocal HUMAN ↔ AI Cognitive Challenge

~~~mermaid
flowchart TD
    H[HUMAN]
    UI[Next.js / TypeScript]
    CR[Private Google Cloud Run]
    ADK[Google Agent Development Kit]
    CORE[HUMAN VECTOR CORE / Python]

    B[Gemini Builder]
    C[Independent Gemini Critic]
    G[Gemini 3.5 Flash]

    M[Active Agentic Memory]
    F[(Firestore Native)]
    S[Secret Manager]

    H -->|Direction / Response / Selection / Verification| UI
    UI --> CR
    CR --> ADK
    ADK --> CORE

    CORE --> B
    CORE --> C

    B --> G
    C --> G

    B --> CORE
    C --> CORE

    CORE --> M
    M <--> F
    M --> CORE

    S -->|Runtime credential| CR

    CORE -->|State / Evidence / HUMAN Gates| H
~~~

## Canonical Workflow

HUMAN Direction
→ Builder V1
→ Human Cognitive Response
→ Independent Critic
→ Conflict Space
→ HUMAN Selection
→ Manual Cognitive Transfer
→ Active Agentic Memory
→ Reconstruction
→ Builder Vn
→ Version Comparison
→ HUMAN Verification
→ HUMAN Final Version Declaration

## Consecutive Reconstruction

V1 + HUMAN contribution → V2

V2 + new HUMAN contribution → V3

V3 + new HUMAN contribution → V4

Each new version uses the immediately preceding version plus the new authorized HUMAN contribution.

## Authority Boundary

AI executes, constructs, retrieves, criticizes, compares and reconstructs.

HUMAN retains direction, selection, memory authorization, cognitive transfer, verification, reconsideration and final authority.

Execution autonomy does not equal authority autonomy.

## Validated Google Stack

- Gemini 3.5 Flash
- Google Agent Development Kit
- Google Cloud Run
- Firestore Native
- Secret Manager
- Cloud Build
- Artifact Registry

## Validated Runtime

authenticated session → HTTP 200

ADK /run → HTTP 200

real Gemini response → confirmed
