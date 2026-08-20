# Research Record Enrichment API

A resilient, schema-validated FastAPI service that takes messy research logs and extracts standardized classification, one-sentence summaries, and quality flags via local LLMs (Ollama). It is built as an extension to a secure Supabase/Postgres CRUD API.

## 🚀 Quickstart

**1. Start the Database (Postgres)**
```bash
docker compose up -d
```

**2. Start the Local AI (Ollama)**
Ensure Ollama is running in the background with the `gemma3:1b` model pulled.

**3. Start the Server**
```bash
.\venv\Scripts\python.exe -m uvicorn main:app --reload
```

## 🧠 The AI Endpoint (`POST /enrich`)

This endpoint acts as an automated data curator, classifying text and extracting strictly validated JSON.

**Example Request:**
```bash
curl -X POST http://localhost:8000/enrich \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Temporal Feature Representation with 1D CNNs\", \"raw_text\":\"We evaluate dilated 1D CNNs on 40,000 MIMIC admissions. AUC was 0.842.\"}"
```

**Example Response (HTTP 200):**
```json
{
  "category": "predictive_modeling",
  "summary": "Dilated 1D CNNs achieve 0.842 AUC on 40,000 EHR admissions.",
  "quality_flags": [],
  "confidence": 0.95,
  "reasoning": "Direct predictive modeling study on tabular EHR data."
}
```

## 🛡️ Reliability & Fault Tolerance
Professional AI integration means planning for failure. This API includes:
* **Explicit Timeout:** Configured to drop unresponsive calls after `30.0s`.
* **Repair Retries:** Exactly 1 repair retry on schema/JSON violation before gracefully failing.
* **Quarantine Logging:** Unrepairable failures are routed to `logs/quarantine.jsonl` rather than crashing the system.
* **Kill Switch:** Setting `LLM_ENABLED=false` in the `.env` file cleanly bypasses the model and returns a deterministic, instant fallback response.
* **Stub Mode:** Setting `LLM_STUB=1` allows frontend UI testing without spending AI compute cycles.

## 📊 Evaluation Results
- **Prompt Version:** `enrich-v1.md`
- **Model:** `gemma3:1b` (Ollama - Local)
- **Score:** **8/8 (100.0%)** on the automated `evals/cases.json` test suite.

## 💰 Cost Analysis
- **Per Call Average:** ~200 input tokens + ~65 output tokens = 265 tokens.
- **Current Cost:** **$0.00** (Running entirely locally on my machine via Ollama).