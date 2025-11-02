"""
Pydantic models for structured research agent responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"

class CustomerMatchResult(BaseModel):
    """Result of customer identification"""
    customer_id: Optional[str] = Field(None, description="Matched customer ID from CRM")
    customer_name: Optional[str] = Field(None, description="Full customer name")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Match confidence 0-1")
    match_reason: str = Field(..., description="Why this customer was matched")
    relevant_data: Optional[dict] = Field(None, description="Relevant customer data from CRM")

class ManualSection(BaseModel):
    """A relevant section found in technical manual"""
    manual_name: str = Field(..., description="Name of the manual (e.g., 'GW-300 Manual')")
    section_title: str = Field(..., description="Title of the relevant section")
    content_excerpt: str = Field(..., description="Key excerpt from this section")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="How relevant this section is")
    relevance_reason: str = Field(..., description="Why this section is relevant to the ticket")

class ManualSearchResult(BaseModel):
    """Result of manual search"""
    product_sku: str = Field(..., description="Product SKU that was searched")
    manual_found: bool = Field(..., description="Whether a manual was found for this product")
    relevant_sections: List[ManualSection] = Field(default_factory=list, description="Relevant sections found")
    overall_confidence: ConfidenceLevel = Field(..., description="Overall confidence in findings")
    summary: str = Field(..., description="Brief summary of manual findings")

class SimilarTicket(BaseModel):
    """A similar historical ticket"""
    ticket_id: str = Field(..., description="ID of the similar ticket")
    title: str = Field(..., description="Title of the similar ticket")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score 0-1")
    resolution_summary: str = Field(..., description="Summary of how it was resolved")
    key_learnings: str = Field(..., description="Key insights relevant to current ticket")

class TicketSimilarityResult(BaseModel):
    """Result of ticket similarity search"""
    similar_tickets_found: bool = Field(..., description="Whether similar tickets were found")
    similar_tickets: List[SimilarTicket] = Field(default_factory=list, description="Similar tickets found")
    similarity_threshold_used: float = Field(0.75, description="Threshold used for similarity")
    search_summary: str = Field(..., description="Summary of similarity search results")

class ResearchSummary(BaseModel):
    """Final research report summary"""
    customer_status: str = Field(..., description="Summary of customer identification")
    technical_findings: str = Field(..., description="Key technical findings from manuals")
    historical_context: str = Field(..., description="Relevant historical ticket context")
    probable_root_cause: Optional[str] = Field(None, description="Most likely root cause of the issue")
    confidence_assessment: ConfidenceLevel = Field(..., description="Overall confidence in analysis")
    recommended_next_steps: List[str] = Field(..., description="Recommended next steps for resolution")
    open_questions: List[str] = Field(..., description="Questions that need human input")
    urgency_level: Literal["low", "medium", "high", "critical"] = Field(..., description="Recommended urgency level")

class FullResearchResult(BaseModel):
    """Complete research results from all agents"""
    customer_identification: CustomerMatchResult
    manual_search: List[ManualSearchResult] 
    ticket_similarity: TicketSimilarityResult
    research_summary: ResearchSummary
    processing_time_seconds: Optional[float] = None
    errors_encountered: List[str] = Field(default_factory=list)
