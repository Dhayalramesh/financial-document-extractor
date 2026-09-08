"""Pydantic schemas — defines the structured shape we force the LLM
to extract into. This is what makes the output reliable and testable,
not just free-text generation.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class EarningsExtraction(BaseModel):
    company_name: Optional[str] = Field(None, description="Full company name")
    ticker: Optional[str] = Field(None, description="Stock ticker symbol if mentioned")
    period: Optional[str] = Field(None, description="Reporting period, e.g. 'Q2 FY26'")

    revenue: Optional[str] = Field(None, description="Reported revenue figure with currency/unit")
    revenue_yoy_growth_pct: Optional[float] = Field(None, description="YoY revenue growth percentage, as a number e.g. 12.5")

    eps: Optional[str] = Field(None, description="Reported EPS figure")
    eps_yoy_growth_pct: Optional[float] = Field(None, description="YoY EPS growth percentage, as a number")

    net_profit: Optional[str] = Field(None, description="Net profit / PAT figure")
    net_margin_pct: Optional[float] = Field(None, description="Net profit margin percentage")

    guidance_summary: Optional[str] = Field(None, description="1-2 sentence summary of forward guidance or outlook")
    key_risks: Optional[str] = Field(None, description="1-2 sentence summary of risks flagged, if any")

    result_sentiment: Optional[Literal["beat", "miss", "inline", "not_stated"]] = Field(
        None, description="Whether results beat, missed, or were inline with estimates, if explicitly stated"
    )

    extraction_confidence: Optional[Literal["high", "medium", "low"]] = Field(
        None, description="Your own confidence in the accuracy of this extraction given the source text"
    )


class ExtractionResponse(BaseModel):
    filename: str
    extracted: EarningsExtraction
    processing_time_ms: float
    raw_text_char_count: int