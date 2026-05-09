# 🚀 SchemaFlow-AI — Governed Intelligent Data Mapping Platform

## 🧠 Overview

SchemaFlow-AI is an enterprise-grade intelligent data mapping and transformation platform designed to automate Excel and schema mapping workflows using adaptive AI orchestration.

The platform combines:

- Rule-based mapping
- Semantic vector search
- Adaptive feedback learning
- Deterministic orchestration
- Explainable AI
- Governance & guardrails
- Workflow replay & orchestration

Unlike traditional RAG systems, SchemaFlow-AI evolves AI suggestions into a governed and explainable decision platform suitable for enterprise workflows.

---

# 🎯 Key Objectives

The platform was designed to solve enterprise challenges around:

- Manual spreadsheet mapping
- Repetitive transformation workflows
- Inconsistent field mapping
- Lack of explainability in AI systems
- Mapping instability and AI hallucinations
- Workflow replay and operational reliability

SchemaFlow-AI transforms AI-assisted mapping into:

# ✅ Governed Adaptive AI Decision Platform

---

# 🏗️ Architecture Overview

## Core Architecture Layers

```text
Excel Upload
    ↓
Data Preparation
    ↓
Temporal Workflow Orchestration
    ↓
AI Mapping Pipeline
    ↓
Feedback Learning Engine
    ↓
Governance & Guardrails
    ↓
Controlled Persistence
```

---

# 🧩 Major Platform Capabilities

## 📊 Intelligent Data Mapping

Supports:

- Rule-based matching
- Semantic similarity search
- AI-assisted mapping suggestions
- Controlled decision selection
- Historical learning

---

## 🔄 Temporal Workflow Orchestration

Uses Temporal for:

- Durable workflows
- Replayable execution
- Step retry
- Fault tolerance
- Workflow state management
- Activity orchestration

Example workflow capabilities:

- Upload processing
- Data transformation replay
- Snapshot recovery
- Execution logging
- Step orchestration

---

## 🧠 AI Mapping Engine (Phase 7)

The AI mapping engine combines:

### Rule-Based Matching

- Exact matching
- Normalized matching
- Similarity thresholds

### Semantic Search

Using:

- OpenAI embeddings
- Pinecone vector database

Capabilities:

- Semantic similarity
- Context-aware matching
- Top-k candidate retrieval

### Controlled AI Decisioning

Instead of allowing unrestricted LLM decisions, the system uses:

- Candidate ranking
- Confidence scoring
- Deterministic orchestration
- Controlled selection

This ensures:

- Predictable mappings
- Reduced hallucinations
- Explainable outcomes

---

# 🔁 Feedback Learning Engine (Phase 9)

The platform continuously learns from user feedback.

## Features

- ACCEPT / REJECT feedback capture
- Mapping history persistence
- Workflow-specific learning
- Candidate injection
- Feedback-aware reranking

Example:

```json
{
  "source_field": "Customer Name",
  "suggested_field": "Customer Identification",
  "final_field": "Full Name",
  "action": "REJECT"
}
```

---

# 📈 Adaptive Intelligence Layer (Phase 10)

Introduced adaptive AI learning capabilities.

## Capabilities

- Score calibration
- Strong ACCEPT enforcement
- Strong REJECT blocking
- Candidate reranking
- Controlled feedback overrides
- Mapping intelligence

### Decision Priority

```text
1. RULE
2. STRONG ACCEPT
3. STRONG REJECT
4. Adjusted Candidates
5. Controlled Decision
```

---

# 🛡️ Governance & Guardrails (Phase 11)

Phase 11 transformed the platform into an enterprise-grade governed AI system.

## Explainability Layer

Every AI decision includes:

- Decision trace
- Confidence score
- Candidate rankings
- Feedback contribution
- Reasoning explanation

Example:

```json
{
  "selected_target": "Customer Identification",
  "confidence": 0.95,
  "method": "FEEDBACK_STRONG_ACCEPT",
  "reason": "Selected due to strong user acceptance history"
}
```

---

## Unified Confidence Model

The platform combines:

- Rule score
- Semantic score
- Feedback score

into a calibrated confidence evaluation.

This enables:

- Stable orchestration
- Confidence governance
- Controlled persistence

---

## Stability Layer

Prevents mapping flip-flops caused by tiny confidence changes.

Example:

| Existing Mapping | Score |
|---|---|
| Customer Identification | 0.81 |

| New Candidate | Score |
|---|---|
| Client ID | 0.82 |

Tiny score differences do not immediately replace stable mappings.

---

## Governance Layer

Introduced controlled AI governance states.

| Confidence | Governance |
|---|---|
| ≥ 0.90 | AUTO_APPROVED |
| 0.70 – 0.89 | REVIEW_REQUIRED |
| < 0.70 | BLOCKED_LOW_CONFIDENCE |

This prevents unsafe AI persistence.

---

## AI Guardrails

Implemented deterministic AI safety controls.

### Includes

- Structure validation
- Confidence floor validation
- Target existence validation
- Hallucination prevention
- Controlled persistence

---

# 🗄️ Data Storage (PostgreSQL)

Uses PostgreSQL with JSONB support.

## Stores

- Workflow metadata
- Uploaded worksheets
- Transformation steps
- Snapshots
- Mapping configuration
- Feedback history
- Execution logs
- Decision traces

---

# 📦 Tech Stack

## Backend

- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic

## Workflow Orchestration

- Temporal

## AI & Semantic Search

- OpenAI Embeddings
- Pinecone
- Vector Similarity Search

## Data Processing

- Pandas
- OpenPyXL

## Frontend (Planned)

- Next.js
- Redux
- Material UI
- Tailwind CSS

## Cloud & Deployment

- AWS EC2
- AWS RDS
- Docker
- Amazon S3
- CloudWatch
- AWS Secrets Manager

---

# 🔄 End-to-End AI Orchestration Pipeline

```text
Semantic Retrieval
    ↓
Feedback Reranking
    ↓
Confidence Calibration
    ↓
Stability Layer
    ↓
Governance Layer
    ↓
AI Guardrails
    ↓
Controlled Persistence
```

---

# 🧠 Key Design Principles

## Deterministic AI Orchestration

AI suggestions are always controlled through:

- governance
- confidence thresholds
- stability rules
- deterministic orchestration

---

## Explainability First

Every mapping decision must be:

- traceable
- explainable
- auditable

---

## PostgreSQL as Source of Truth

The platform keeps PostgreSQL as the authoritative data source.

---

## Adaptive Learning Without Retraining

The platform learns dynamically using:

- feedback memory
- score adjustments
- temporal weighting

without requiring expensive model retraining.

---

# 📊 Project Evolution

| Phase | Capability |
|---|---|
| Phase 1–5 | Workflow foundation & Temporal orchestration |
| Phase 7 | AI mapping engine |
| Phase 9 | Feedback learning |
| Phase 10 | Adaptive intelligence |
| Phase 11 | Governed AI platform |

---

# 🚀 Running the Project

## Create Virtual Environment

```bash
python -m venv venv
```

## Activate Environment (Windows)

```bash
venv\Scripts\activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Start FastAPI Server

```bash
uvicorn app.main:app --reload
```

---

# 🧪 Testing

Run all tests:

```bash
pytest tests/ -v
```

Example test areas:

- Governance testing
- Stability testing
- Guardrail validation
- End-to-end orchestration
- Feedback learning
- Decision trace validation

---

# ☁️ AWS Deployment Roadmap

Planned deployment architecture includes:

- AWS EC2
- AWS RDS PostgreSQL
- Docker containers
- Amazon S3
- AWS CloudWatch
- Elastic Load Balancer
- AWS Secrets Manager

---

# 🧠 Final Engineering Insight

A major architectural lesson from this project:

> Enterprise AI systems require orchestration, governance, stability, and explainability more than generation alone.

SchemaFlow-AI focuses on building:

# ✅ Governed Adaptive AI Infrastructure

rather than a simple LLM wrapper or RAG demo.

---

# 🔗 Project Repository

GitHub:

https://github.com/santoshnarayanan/SchemaFlow-AI

