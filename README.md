# Privacy-Preserving Complaint Intelligence Platform

An enterprise NLP platform that redacts personally identifiable information (PII) from consumer financial complaints **before** any downstream analysis happens, then classifies, scores, and analyzes the anonymized text to surface operational intelligence — without ever exposing sensitive customer data.

Built strictly under Privacy-by-Design principles aligning with GDPR, HIPAA, and India's DPDP Act.

---

## Architecture & Pipeline Overview

```
                      +-----------------------------+
                      |   Incoming Raw Complaint    |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |    Presidio PII Redaction   |
                      |  (NER + Custom Regex PII)   |
                      +--------------+--------------+
                                     |
                         [Redacted Narrative Only]
                                     |
       +-----------------------------+-----------------------------+
       |                             |                             |
       v                             v                             v
+--------------+             +---------------+             +---------------+
|  TF-IDF+SVM  |             |  SBERT+LogReg |             |  DistilBERT   |
+-------+------+             +-------+-------+             +-------+-------+
        |                            |                             |
        +----------------------------+-----------------------------+
                                     |
                                     v
                      +-----------------------------+
                      |   Model Agreement Engine    |
                      | (Consensus vs Escalation)   |
                      +--------------+--------------+
                                     |
                      +-----------------------------+
                      |   Hierarchical Classifier   |
                      |    (Domain -> Sub-Issue)    |
                      +--------------+--------------+
                                     |
       +-----------------------------+-----------------------------+
       |                             |                             |
       v                             v                             v
+--------------+             +---------------+             +---------------+
|  Sentiment & |             | FAISS Vector  |             |  Causal Root- |
|  Urgency ML  |             | Duplicate Det |             |  Cause Graph  |
+-------+------+             +-------+-------+             +-------+-------+
        |                            |                             |
        +----------------------------+-----------------------------+
                                     |
                                     v
                      +-----------------------------+
                      |   FastAPI & Streamlit UI    |
                      |   (Real-Time Intelligence)  |
                      +-----------------------------+
```

---

## Core Capabilities & Implemented Modules

### 1. PII Redaction Module (`src/redaction/`)
Built on Microsoft Presidio Analyzer and Anonymizer, extended with custom regex recognizers (`custom_recognizers.py`) for entities Presidio does not detect natively:
- `ACCOUNT_NUMBER` (e.g. `ACC-10023456`, `AC987654321`)
- `AADHAAR_NUMBER` (e.g. `1234 5678 9012`)
- `COMPLAINT_ID` (e.g. `CMP-2026-00001`, `CASE-12345`)
- `CREDIT_CARD` (e.g. `4111 2222 3333 4444`)
- `CREDENTIAL` (e.g. `username is john_doe99`, `password: hunter2`)

**Evaluation Performance** (`python -m src.redaction.evaluate_redaction` on 30-complaint synthetic benchmark):
- **Overall Recall**: **100.00%** (Zero PII leaks)
- **Overall Precision**: **95.45%**
- **Overall F1 Score**: **97.67%**

### 2. Multi-Model Domain Classification & Agreement (`src/classification/`)
Three distinct paradigms evaluated on an identical stratified split across 9 consolidated CFPB categories:
- **TF-IDF + Linear SVM**: 74.38% accuracy, 74.61% weighted F1.
- **Sentence-BERT + Logistic Regression**: 73.92% accuracy, 74.66% weighted F1.
- **DistilBERT (fine-tuned transformer)**: Pretrained checkpoint in `models/saved/domain_classifier_distilbert/`.
- **Model Consensus Engine**: Flags complaints for human review if classifiers diverge or average confidence drops below 0.40.

### 3. Hierarchical Classification (`src/classification/hierarchical_*`)
Two-stage triage: Level 1 predicts the broad financial domain; Level 2 predicts granular sub-issues (e.g. *Debt collection -> Communication tactics*, or *Credit card -> Problem when making payments*) using 8 per-domain sub-classifiers.

### 4. Sentiment, Emotion & Urgency Scoring (`src/sentiment/sentiment_emotion.py`)
Analyzes redacted text for emotional tone (anger, frustration, anxiety, satisfaction) and outputs an operational **Urgency Score** ($0.0 - 1.0$) based on distress indicators, sentiment polarity, and legal escalation keywords.

### 5. Semantic Duplicate Detection (`src/duplicate_detection/semantic_similarity.py`)
Uses `SentenceTransformer` (`all-MiniLM-L6-v2`) embeddings indexed with **FAISS** (with cosine similarity fallback) to identify prior matching or near-duplicate complaints in milliseconds.

### 6. K-Anonymity Privacy Audit & Mitigation (`src/privacy/`)
Audits record-level re-identification risk from structured quasi-identifiers (`Product_clean`, `Sub-product`, `Issue`, `received_month`):
- **Baseline Risk**: 47.38% uniquely identifiable ($k=1$), 82.02% at risk ($k < 5$).
- **Mitigation Strategy (Quarter Binning + Drop Subproduct)**: Reduces uniquely identifiable records to **12.95%** and at-risk records to **44.73%** (a **37.29 percentage-point risk reduction**).

### 7. Causal Root-Cause Graph (`src/causal/`)
Clusters extracted cause-and-effect phrases into a directed semantic network (`models/saved/causal_graph.gexf`), ranking the systemic root causes driving downstream complaints.

### 8. End-to-End Orchestration & REST API (`src/pipeline/`, `api/`)
- Unified `ComplaintPipeline` singleton for real-time and batch execution.
- Production-ready FastAPI endpoints with automatic Pydantic validation:
  - `POST /complaints`: Ingest raw complaint, redact PII, run 3-way classification, sentiment, duplicate check, and agreement evaluation.
  - `GET /dashboard-data`: High-level aggregated metrics, category distributions, and privacy statistics.
  - `GET /complaints/review-queue`: Review queue for flagged complaints.
  - `POST /complaints/{id}/resolve`: Mark escalated complaints as resolved.
  - `GET /health`: Liveness probe.

### 9. Interactive Streamlit Dashboard (`dashboard/streamlit_app.py`)
Full-featured executive and analyst dashboard featuring:
- Live complaint intake and real-time redaction inspector.
- Human review queue with one-click resolution.
- Category volume drill-down by sub-issue and historical trends.
- Privacy protection metrics and K-anonymity audit comparisons.
- Interactive causal graph visualizations and automated volume spike recommendations.

---

## Setup & Quickstart

### 1. Environment & Dependencies
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS

pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

### 2. Run the Test Suite
```bash
python -m pytest tests -v
```

### 3. Launch the API Server
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger documentation is available at `http://localhost:8000/docs`.

### 4. Launch the Streamlit Dashboard
```bash
streamlit run dashboard/streamlit_app.py
```
Access the dashboard at `http://localhost:8501`.

---

## Module Execution Guide

Run any individual module in isolation:

```bash
# Evaluate PII Redaction
python -m src.redaction.evaluate_redaction

# Run Live Prediction CLI Demo
python -m src.classification.live_predict

# Run Hierarchical Prediction Spot-Check
python -m src.classification.hierarchical_predict

# Run K-Anonymity Privacy Audit & Mitigation
python -m src.privacy.k_anonymity_audit
python -m src.privacy.k_anonymity_mitigation

# Rebuild Causal Root-Cause Graph
python -m src.causal.build_causal_graph

# Run Batch Dataset Processing
python -m scripts.run_pipeline_batch
```