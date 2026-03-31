"""
ai-screener-service  –  Pydantic schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    skills: float = Field(..., ge=0, le=100, description="Skills match score 0-100")
    experience: float = Field(..., ge=0, le=100, description="Experience relevance score 0-100")
    education: float = Field(..., ge=0, le=100, description="Education match score 0-100")
    overall: float = Field(..., ge=0, le=100, description="Weighted overall score 0-100")


class NEREntities(BaseModel):
    companies: list[str] = Field(default_factory=list)
    degrees: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    misc: list[str] = Field(default_factory=list)


class ScreeningResult(BaseModel):
    resume_id: str
    job_id: str
    overall_score: float
    breakdown: ScoreBreakdown
    entities: NEREntities
    summary: str
    raw_llm_response: Optional[str] = None


class ScreenRequest(BaseModel):
    job_id: str
    resume_id: str
    raw_text: str
    job_description: str
