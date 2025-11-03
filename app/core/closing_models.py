"""
Data models for intelligent ticket closing workflow
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from enum import Enum


class QuestionCategory(Enum):
    """Categories for followup questions"""
    TECHNICAL = "technical"
    CUSTOMER = "customer"  
    PROCESS = "process"


class QuestionImportance(Enum):
    """Importance levels for followup questions"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ClosingNotes:
    """User input for how the ticket was resolved"""
    primary_solution: str
    steps_taken: List[str]
    challenges_encountered: List[str]
    customer_feedback: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ClosingNotes':
        """Create ClosingNotes from dictionary"""
        return cls(
            primary_solution=data.get('primary_solution', ''),
            steps_taken=data.get('steps_taken', []),
            challenges_encountered=data.get('challenges_encountered', []),
            customer_feedback=data.get('customer_feedback', '')
        )


@dataclass
class FollowupQuestion:
    """AI-generated followup question for completeness"""
    question: str
    category: QuestionCategory
    importance: QuestionImportance
    reasoning: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FollowupQuestion':
        """Create FollowupQuestion from dictionary"""
        return cls(
            question=data.get('question', ''),
            category=QuestionCategory(data.get('category', 'technical')),
            importance=QuestionImportance(data.get('importance', 'medium')),
            reasoning=data.get('reasoning', '')
        )


@dataclass
class ClosingReport:
    """Final AI-generated ticket closing report"""
    ticket_id: str
    context_summary: str
    root_cause: str
    solution_implemented: str
    outcome: str
    future_recommendations: List[str]
    tags: List[str]
    generated_at: datetime
    
    @classmethod
    def from_dict(cls, data: dict, ticket_id: str) -> 'ClosingReport':
        """Create ClosingReport from dictionary"""
        return cls(
            ticket_id=ticket_id,
            context_summary=data.get('context_summary', ''),
            root_cause=data.get('root_cause', ''),
            solution_implemented=data.get('solution_implemented', ''),
            outcome=data.get('outcome', ''),
            future_recommendations=data.get('future_recommendations', []),
            tags=data.get('tags', []),
            generated_at=datetime.now()
        )


@dataclass
class ClosingWorkflowState:
    """State management for closing workflow"""
    notes_submitted: bool = False
    notes_data: Optional[ClosingNotes] = None
    followup_questions_generated: bool = False
    followup_questions: List[FollowupQuestion] = None
    followup_answers: str = ""
    report_generated: bool = False
    report_content: str = ""
    ticket_closed: bool = False
    
    def __post_init__(self):
        if self.followup_questions is None:
            self.followup_questions = []


# JSON Schema for structured AI responses
FOLLOWUP_QUESTIONS_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object", 
                "properties": {
                    "question": {"type": "string"},
                    "category": {"type": "string", "enum": ["technical", "customer", "process"]},
                    "importance": {"type": "string", "enum": ["high", "medium", "low"]},
                    "reasoning": {"type": "string"}
                },
                "required": ["question", "category", "importance", "reasoning"],
                "additionalProperties": False
            }
        }
    },
    "required": ["questions"],
    "additionalProperties": False
}

CLOSING_REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "context_summary": {"type": "string"},
        "root_cause": {"type": "string"},
        "solution_implemented": {"type": "string"},
        "outcome": {"type": "string"},
        "future_recommendations": {
            "type": "array",
            "items": {"type": "string"}
        },
        "tags": {
            "type": "array", 
            "items": {"type": "string"}
        }
    },
    "required": ["context_summary", "root_cause", "solution_implemented", "outcome", "future_recommendations", "tags"],
    "additionalProperties": False
}


# Demo closing notes are now loaded from data/closing_notes.json via DataLoader
# This keeps data consistent with other files in the data/ directory
