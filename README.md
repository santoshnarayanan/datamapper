# 📊 Excel Transformation & Mapping System

A backend-driven data processing system inspired by Power Query, designed to ingest, transform, and map Excel data to structured banking templates (EBA format).

---

## 🚀 Overview

This project enables users to:

* Upload Excel files
* Perform step-by-step data transformations
* Map source data to predefined EBA templates
* Persist transformation logic for replay and reuse

The system is designed with a **workflow-centric architecture**, where each user session is tracked and processed independently.

---

## 🧱 Core Architecture

### 🔑 Workflow-Centric Design

All operations are tied to a unique `workflow_id`, which acts as the central entity connecting:

* Uploaded worksheets
* Data transformation steps
* Mapping configurations

---

### 🗄️ Data Storage (PostgreSQL)

* Excel data stored as **JSONB** (dynamic schema support)
* Transformation steps stored as ordered operations
* Mapping configurations stored for reuse

---

### ⚙️ Backend (FastAPI)

* REST APIs for workflow creation and file upload
* Modular architecture:

  * Routes (API layer)
  * Services (business logic)
  * Repositories (data access)
  * Models (ORM)

---

### 📊 Excel Processing

* Excel files parsed using pandas
* Data normalized into:

  ```json
  {
    "columns": [...],
    "rows": [...]
  }
  ```

---

## 🔄 Application Flow

### 1. Home Screen (Upload)

* User uploads Excel file(s)
* Data is parsed and stored in PostgreSQL (JSONB)
* Linked to a `workflow_id`

---

### 2. Data Prepare Screen

* User performs transformations:

  * Delete columns
  * Remove rows
  * Set header row
* Each operation is stored as:

  * Step (action performed)
  * Snapshot (data state)

---

### 3. Data Mapping Screen

Three-grid interface:

| Grid   | Description            |
| ------ | ---------------------- |
| Left   | Source worksheet data  |
| Middle | Mapping between fields |
| Right  | EBA template structure |

* Supports drag-and-drop mapping
* Mapping stored as JSON
* Designed for AI-assisted suggestions (future phase)

---

## 🧩 Tech Stack

### Backend

* FastAPI
* SQLAlchemy
* PostgreSQL (JSONB)

### Data Processing

* Pandas
* OpenPyXL

### Frontend (Planned)

* Next.js
* Redux
* Material UI
* Tailwind CSS

### Future Integrations

* Temporal (workflow replay)
* Pinecone (AI-based mapping suggestions)
* AWS Cognito (authentication)

---

## 🎯 Phase 1 Scope (Current)

* FastAPI project setup
* PostgreSQL schema design
* SQLAlchemy models
* Excel upload & parsing API
* JSONB-based storage

---

## 🔮 Future Roadmap

* Data transformation engine with replay (Temporal)
* AI-assisted mapping using vector search (Pinecone)
* Full frontend integration
* Export to Excel (EBA format)

---

## 🧠 Design Principles

* Keep PostgreSQL as the **source of truth**
* Use JSONB for flexibility with dynamic schemas
* Separate business logic from data access
* Build extensible architecture for AI and workflow orchestration

---

## ▶️ Running the Project

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload
```

---

## 📌 Notes

This project is designed as a **scalable backend system** for data transformation and mapping workflows, with future support for AI-driven automation and workflow orchestration.

---
