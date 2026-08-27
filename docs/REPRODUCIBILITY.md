# HUMAN VECTOR — Reproducibility

## Requirements

- Node.js / npm
- Python 3.13
- Gemini API credential
- Google Agent Development Kit 2.6.3
- Google Cloud Firestore client 2.28.1

## Frontend

Install dependencies:

    npm install

Development:

    npm run dev

Production build:

    npm run build

Production start:

    npm run start

Lint:

    npm run lint

## ADK Service

Python dependencies are defined in:

    hv-adk/requirements.txt

Install them with:

    python3 -m pip install -r hv-adk/requirements.txt

The containerized runtime starts the ADK API server on port 8080.

Docker runtime:

    python:3.13-slim

ADK server:

    adk api_server --host 0.0.0.0 --port ${PORT:-8080} /app/hv-adk

## Configuration and Secrets

Runtime credentials are not committed to the repository.

The validated Google Cloud deployment provides the Gemini credential through Google Secret Manager.

A reviewer reproducing the system must provide their own valid Gemini credential and required Google Cloud configuration.

## Validated Cloud Stack

- Gemini 3.5 Flash
- Google Agent Development Kit
- Google Cloud Run
- Firestore Native
- Secret Manager
- Cloud Build
- Artifact Registry

## Validated Runtime Evidence

    authenticated session -> HTTP 200
    ADK /run -> HTTP 200
    real Gemini response -> confirmed

## Architecture

See:

    docs/CURRENT_ARCHITECTURE.md
