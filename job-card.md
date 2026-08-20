# Job card: Enrich Research Records

**What it does:** Classifies a messy research log entry, generates a 1-sentence summary, and extracts quality flags.
**Input:** 
{ "title": "string, 1-300 chars", "raw_text": "string, 10-5000 chars" }

**Output:**
{
  "category": "one of [clinical_nlp | predictive_modeling | medical_imaging | other]",
  "summary": "string, exactly one sentence",
  "quality_flags": ["array of zero or more from: missing_metrics | small_cohort | synthetic_data"],
  "confidence": "number 0.0-1.0",
  "reasoning": "one short sentence"
}

**It must never:**
- Invent a category or quality flag outside the allowed lists.
- Return raw markdown text outside of the JSON object.

**When unsure it should:**
- Use the "other" category with a confidence below 0.5, and do not guess.