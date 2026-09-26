# Privacy-Preserving Complaint Intelligence Platform

An NLP platform that redacts personally identifiable information (PII) from
customer complaints **before** any downstream analysis happens, then
classifies, and analyzes the anonymized text to surface actionable
insights — without ever exposing sensitive customer data.

The project combines privacy-by-design document processing (NER-based PII
redaction) with comparative NLP methodology (classical ML vs. sentence
embeddings vs. fine-tuned transformers) for complaint domain classification,
and is built to comply with data-privacy principles found in regulations
such as GDPR, HIPAA, and India's DPDP Act.

## Pipeline Overview

```
Raw Complaint Text
      |
      v
[1] PII Redaction  ---------------- Presidio (NER + custom regex recognizers)
      |
      v
[2] Domain/Category Classification - TF-IDF+SVM | Sentence-BERT+LogReg | DistilBERT (fine-tuned)
      |
      v
[3] Sentiment & Emotion Analysis -- (in progress)
      |
      v
[4] Duplicate Detection ----------- Sentence-BERT + FAISS (planned)
      |
      v
[5] Topic Modeling ----------------- BERTopic (planned)
      |
      v
[6] Priority Prediction ----------- feature-based classifier (planned)
      |
      v
Dashboard (Streamlit) -- privacy-safe aggregated insights, no PII surfaced
```

## Status: What's Done So Far

### 1. Datasets

| File | Rows | Purpose |
|---|---|---|
| `data/processed/complaints_small.csv` | ~3,242 | Domain classification training/eval. Stratified, cleaned sample of the CFPB Consumer Complaint Database. |
| `data/eval/synth_data.json` | 30 | Synthetic, fully labeled complaints used to evaluate the PII redaction pipeline. Contains ground-truth spans for PERSON, EMAIL_ADDRESS, PHONE_NUMBER, ACCOUNT_NUMBER, AADHAAR_NUMBER, COMPLAINT_ID, and CREDIT_CARD. |

CFPB's raw `Product` labels were consolidated into 9 unified categories
(`Product_clean`) to correct for taxonomy revisions CFPB made over the
years, which had fragmented semantically identical complaints across
near-duplicate labels (e.g. "Credit reporting" vs. "Credit reporting,
credit repair services, or other personal consumer reports"). Categories
with fewer than 20 rows were dropped as statistically unreliable.

### 2. PII Redaction Module (`src/redaction/`)

Built on Microsoft Presidio, extended with custom regex-based recognizers
(`custom_recognizers.py`) for entity types Presidio doesn't detect
out of the box: `ACCOUNT_NUMBER`, `AADHAAR_NUMBER`, `COMPLAINT_ID`, and
`CREDIT_CARD`.

**Latest evaluation results** (`python -m src.redaction.evaluate_redaction`,
30-complaint synthetic eval set):

| Entity Type | Precision | Recall | F1 |
|---|---|---|---|
| PERSON | 83.33% | 100.00% | 90.91% |
| EMAIL_ADDRESS | 100.00% | 100.00% | 100.00% |
| PHONE_NUMBER | 88.24% | 100.00% | 93.75% |
| ACCOUNT_NUMBER | 100.00% | 100.00% | 100.00% |
| AADHAAR_NUMBER | 100.00% | 100.00% | 100.00% |
| COMPLAINT_ID | 100.00% | 100.00% | 100.00% |
| CREDIT_CARD | 100.00% | 100.00% | 100.00% |
| **Overall** | **95.45%** | **100.00%** | **97.67%** |

100% recall across every entity type — no PII is missed. Remaining
precision loss is limited to Presidio's built-in PERSON and PHONE_NUMBER
recognizers (spaCy-based NER), not the custom regex recognizers, all of
which are now perfect.

### 3. Complaint Classification Module (`src/classification/`)

Three approaches trained and evaluated on the same consolidated category
schema, for a direct comparison of classical ML, embedding-based, and
transformer fine-tuning methods:

| Model | Accuracy | Weighted F1 |
|---|---|---|
| TF-IDF + Linear SVM (`baseline_tfidf_svm.py`) | 74.38% | 74.61% |
| Sentence-BERT + Logistic Regression (`sentence_bert_classifier.py`) | 73.92% | 74.66% |
| DistilBERT (fine-tuned) (`distilbert_finetune.py`) | *pending run* | *pending run* |

**Observation:** the two approaches perform nearly identically overall,
but diverge on categories with vocabulary overlap. Sentence-BERT trades
precision for recall on categories like `Money transfer` and `Vehicle
loan or lease` — its semantic embeddings pull related-but-distinct
categories closer together, while TF-IDF's literal word-overlap draws
sharper (if more superficial) boundaries. This tradeoff is discussed
further in the project report.

### 4. Not Yet Built

- Sentiment & emotion analysis module
- Duplicate/semantic similarity detection (Sentence-BERT + FAISS)
- Topic modeling (BERTopic)
- Priority/severity prediction
- Full pipeline orchestration (`src/pipeline/full_pipeline.py`)
- FastAPI endpoints and Streamlit dashboard wiring
- Docker containerization validation

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS/Linux
   ```
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_lg
   ```
3. Copy `.env.example` to `.env` and fill in any secrets (e.g. API keys
   for LLM-assisted modules, if used).
4. Run individual modules directly to test them in isolation, e.g.:
   ```bash
   python -m src.redaction.evaluate_redaction
   python -m src.classification.baseline_tfidf_svm
   python -m src.classification.sentence_bert_classifier
   python -m src.classification.distilbert_finetune
   ```
5. Once the full pipeline is wired up:
   ```bash
   uvicorn api.main:app --reload
   streamlit run dashboard/streamlit_app.py
   ```

## Top-Level Folders

- `data/` — raw downloads (gitignored), processed/sampled datasets, and
  evaluation datasets (`data/eval/synth_data.json`).
- `models/` — saved model checkpoints (gitignored) and version notes.
- `notebooks/` — exploratory and experimental notebooks.
- `src/` — reusable Python modules:
  - `src/data/` — dataset loading, cleaning, sampling
  - `src/redaction/` — Presidio pipeline, custom recognizers, evaluation
  - `src/classification/` — TF-IDF+SVM, Sentence-BERT, DistilBERT models
  - `src/sentiment/`, `src/duplicate_detection/`, `src/topic_modeling/`,
    `src/priority/` — planned modules
  - `src/pipeline/` — end-to-end orchestration (planned)
  - `src/utils/` — shared config and logging
- `api/` — FastAPI application entrypoint, routes, and schemas.
- `dashboard/` — Streamlit dashboard app.
- `tests/` — regression tests for core workflows.
- `scripts/` — standalone scripts for dataset creation and evaluation.

## Tech Stack

- **Redaction:** Microsoft Presidio, spaCy, custom regex recognizers
- **Classification:** scikit-learn (TF-IDF, SVM, Logistic Regression),
  Sentence-Transformers (`all-MiniLM-L6-v2`), HuggingFace `transformers`
  (fine-tuned `distilbert-base-uncased`)
- **Planned:** BERTopic, FAISS, FastAPI, Streamlit, Docker

## Notes on Methodology

- All three classification models are evaluated on an identical
  consolidated label schema and identical train/test split
  (`random_state=42`, stratified 80/20) to ensure a fair, apples-to-apples
  comparison.
- The PII evaluation dataset is fully synthetic (no real personal data),
  generated with controlled ground-truth entity spans so redaction
  precision/recall can be measured exactly.
- Category consolidation (merging CFPB's revised taxonomy labels) improved
  baseline classification accuracy from 56.86% to 74.38%, demonstrating
  that label-schema cleanliness had a larger effect than model choice at
  this stage.