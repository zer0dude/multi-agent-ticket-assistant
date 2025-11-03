"""
Planning models and data structures for action planning phase
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class QuestionCategory(str, Enum):
    TECHNICAL = "technical"
    BUSINESS = "business"
    CUSTOMER = "customer"


class Importance(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Owner(str, Enum):
    AI_AGENT = "ai_agent"
    TECHNICAL_ASSISTANT = "technical_assistant"
    CUSTOMER = "customer"


class ComplexityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ClarificationQuestion(BaseModel):
    """A question to better understand the ticket situation"""
    question: str = Field(description="The clarification question text")
    category: QuestionCategory = Field(description="Category of the question")
    importance: Importance = Field(description="How important this question is")
    reasoning: str = Field(description="Why this question is important")


class ActionItem(BaseModel):
    """An action item in the plan"""
    id: str = Field(description="Unique identifier for the action")
    description: str = Field(description="Description of the action to take")
    owner: Owner = Field(description="Who is responsible for this action")
    priority: int = Field(description="Priority level (1=highest, 3=lowest)", ge=1, le=3)
    estimated_time: str = Field(description="Estimated time to complete")
    dependencies: List[str] = Field(default=[], description="IDs of actions this depends on")
    reasoning: str = Field(description="Why this action is necessary")


class WorkAssessment(BaseModel):
    """Assessment of work complexity and effort"""
    complexity_level: ComplexityLevel = Field(description="Overall complexity assessment")
    estimated_hours: int = Field(description="Total estimated hours", ge=0)
    confidence_level: ConfidenceLevel = Field(description="Confidence in the assessment")
    reasoning: str = Field(description="Detailed reasoning for the assessment")
    risk_factors: List[str] = Field(default=[], description="Potential risks or complications")
    success_probability: float = Field(description="Probability of successful resolution", ge=0.0, le=1.0)


class PlanRecommendation(BaseModel):
    """Complete plan recommendation from AI planning agent"""
    
    # Core planning components
    clarification_questions: List[ClarificationQuestion] = Field(
        description="Questions to better understand the situation"
    )
    ai_actions: List[ActionItem] = Field(
        description="Actions that AI agents can perform"
    )
    technical_assistant_actions: List[ActionItem] = Field(
        description="Actions requiring human technical assistant"
    )
    customer_actions: List[ActionItem] = Field(
        description="Actions the customer needs to take"
    )
    work_assessment: WorkAssessment = Field(
        description="Assessment of overall work required"
    )
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.now)
    revision_count: int = Field(default=0, description="Number of times this plan has been revised")
    original_plan_id: Optional[str] = Field(default=None, description="ID of original plan if this is a revision")
    
    # Context preservation
    research_context_summary: str = Field(
        description="Summary of research findings this plan is based on"
    )
    ticket_summary: str = Field(
        description="Summary of the original ticket"
    )

    def get_all_actions(self) -> List[ActionItem]:
        """Get all actions regardless of owner"""
        return self.ai_actions + self.technical_assistant_actions + self.customer_actions

    def get_total_estimated_hours(self) -> float:
        """Calculate total estimated hours from work assessment"""
        return float(self.work_assessment.estimated_hours)

    def get_high_priority_questions(self) -> List[ClarificationQuestion]:
        """Get only high importance clarification questions"""
        return [q for q in self.clarification_questions if q.importance == Importance.HIGH]


class PlanRevisionRequest(BaseModel):
    """Request to revise an existing plan based on human feedback"""
    original_plan: PlanRecommendation = Field(description="The original plan to revise")
    human_feedback: str = Field(description="Human feedback and requested changes")
    feedback_provided_at: datetime = Field(default_factory=datetime.now)
    revision_instructions: Optional[str] = Field(
        default=None, 
        description="Specific instructions for the AI on how to handle the revision"
    )


class PlanningWorkflowState(BaseModel):
    """State tracking for the planning workflow"""
    current_plan: Optional[PlanRecommendation] = None
    revision_history: List[PlanRecommendation] = Field(default=[])
    plan_approved: bool = False
    pending_revision: Optional[PlanRevisionRequest] = None
    
    def add_plan(self, plan: PlanRecommendation):
        """Add a new plan and update state"""
        if self.current_plan:
            # Archive current plan to history
            self.revision_history.append(self.current_plan)
        self.current_plan = plan
        self.plan_approved = False
        
    def approve_current_plan(self):
        """Mark current plan as approved"""
        if self.current_plan:
            self.plan_approved = True
            
    def get_revision_count(self) -> int:
        """Get total number of plan revisions"""
        return len(self.revision_history)


# JSON Schema for LLM structured responses
PLAN_RECOMMENDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "clarification_questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "category": {"type": "string", "enum": ["technical", "business", "customer"]},
                    "importance": {"type": "string", "enum": ["high", "medium", "low"]},
                    "reasoning": {"type": "string"}
                },
                "required": ["question", "category", "importance", "reasoning"]
            }
        },
        "ai_actions": {
            "type": "array", 
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "description": {"type": "string"},
                    "owner": {"type": "string", "enum": ["ai_agent"]},
                    "priority": {"type": "integer", "minimum": 1, "maximum": 3},
                    "estimated_time": {"type": "string"},
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "reasoning": {"type": "string"}
                },
                "required": ["id", "description", "owner", "priority", "estimated_time", "reasoning"]
            }
        },
        "technical_assistant_actions": {
            "type": "array",
            "items": {
                "type": "object", 
                "properties": {
                    "id": {"type": "string"},
                    "description": {"type": "string"},
                    "owner": {"type": "string", "enum": ["technical_assistant"]},
                    "priority": {"type": "integer", "minimum": 1, "maximum": 3},
                    "estimated_time": {"type": "string"},
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "reasoning": {"type": "string"}
                },
                "required": ["id", "description", "owner", "priority", "estimated_time", "reasoning"]
            }
        },
        "customer_actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "description": {"type": "string"},
                    "owner": {"type": "string", "enum": ["customer"]},
                    "priority": {"type": "integer", "minimum": 1, "maximum": 3},
                    "estimated_time": {"type": "string"},
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "reasoning": {"type": "string"}
                },
                "required": ["id", "description", "owner", "priority", "estimated_time", "reasoning"]
            }
        },
        "work_assessment": {
            "type": "object",
            "properties": {
                "complexity_level": {"type": "string", "enum": ["low", "medium", "high"]},
                "estimated_hours": {"type": "integer", "minimum": 0},
                "confidence_level": {"type": "string", "enum": ["high", "medium", "low"]},
                "reasoning": {"type": "string"},
                "risk_factors": {"type": "array", "items": {"type": "string"}},
                "success_probability": {"type": "number", "minimum": 0.0, "maximum": 1.0}
            },
            "required": ["complexity_level", "estimated_hours", "confidence_level", "reasoning", "success_probability"]
        },
        "research_context_summary": {"type": "string"},
        "ticket_summary": {"type": "string"}
    },
    "required": [
        "clarification_questions", 
        "ai_actions", 
        "technical_assistant_actions", 
        "customer_actions",
        "work_assessment",
        "research_context_summary",
        "ticket_summary"
    ]
}
