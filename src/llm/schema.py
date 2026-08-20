from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

# The allowed closed lists from your Job Card
class ResearchCategory(str, Enum):
    clinical_nlp = "clinical_nlp"
    predictive_modeling = "predictive_modeling"
    medical_imaging = "medical_imaging"
    other = "other"

class QualityFlag(str, Enum):
    missing_metrics = "missing_metrics"
    small_cohort = "small_cohort"
    synthetic_data = "synthetic_data"

# What the user sends to us
class EnrichRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    raw_text: str = Field(..., min_length=10, max_length=5000)

# What we strictly return to the user
class EnrichResponse(BaseModel):
    category: ResearchCategory
    summary: str
    quality_flags: List[QualityFlag] = []
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str