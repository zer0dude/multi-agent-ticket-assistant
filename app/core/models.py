"""
Data models for the Multi-Agent Ticketing Assistant
Using Pydantic for validation and type safety
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class TicketStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    IN_PROGRESS = "in_progress"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


class SupportTier(str, Enum):
    STANDARD = "Standard"
    PREMIUM = "Premium"


# CRM Models
class CompanyContact(BaseModel):
    phone: str
    email: str
    website: str


class Company(BaseModel):
    name: str
    address: str
    founded: int
    employees: int
    specialization: str
    contact: CompanyContact


class ProductSpecifications(BaseModel):
    max_flow: str
    max_pressure: str
    power: str
    inlet_size: str
    outlet_size: str
    max_temp: str
    weight: str
    max_inlet_height: Optional[str] = None
    max_viscosity: Optional[str] = None


class Product(BaseModel):
    sku: str
    name: str
    type: str
    description: str
    specifications: ProductSpecifications
    applications: List[str]


class ContactPerson(BaseModel):
    name: str
    title: str
    email: str
    phone: str


class CompanyInfo(BaseModel):
    founded: int
    employees: int
    business: str


class Purchase(BaseModel):
    sku: str
    quantity: int
    purchase_date: str
    installation_location: str


class Customer(BaseModel):
    id: str
    name: str
    address: str
    contact_person: ContactPerson
    company_info: CompanyInfo
    purchases: List[Purchase]
    customer_since: str
    support_tier: SupportTier
    notes: str


class CRMData(BaseModel):
    company: Company
    products: List[Product]
    customers: List[Customer]


# Ticket Models
class TicketSummary(BaseModel):
    context: str
    root_cause: str
    steps_taken: str
    outcome: str
    future_cues: List[str]
    tags: List[str]


class Ticket(BaseModel):
    ticket_id: str
    customer_id: str
    title: str
    body: str
    related_skus: List[str]
    status: TicketStatus
    priority: TicketPriority
    created_date: str
    created_by: str
    resolved_date: Optional[str] = None
    resolution: Optional[str] = None
    summary: Optional[TicketSummary] = None


# Search Models
class SearchResultType(str, Enum):
    MANUAL = "manual"
    PRIOR_TICKET = "prior_ticket"
    CRM = "crm"


class SearchResult(BaseModel):
    type: SearchResultType
    source_id: str
    section: Optional[str] = None
    quote: str
    score: float
    relevance_note: Optional[str] = None


# Agent Models
class ResearchBundle(BaseModel):
    customer_summary: str
    product_guess: Optional[str] = None
    findings: List[SearchResult]
    open_questions: List[str]


class PlanStep(BaseModel):
    id: int
    owner: str  # "agent", "human", "customer"
    desc: str
    evidence_refs: Optional[List[str]] = None


class Plan(BaseModel):
    difficulty: str  # "easy", "moderate", "hard"
    steps: List[PlanStep]
    briefing: str
    escalation_brief: Optional[str] = None


class CustomerEmail(BaseModel):
    subject: str
    body: str


class ExecutionArtifacts(BaseModel):
    customer_email: CustomerEmail
    internal_note: str
    extra_findings: Optional[List[SearchResult]] = None


class Summary(BaseModel):
    context: str
    root_cause: Optional[str] = None
    steps_taken: str
    outcome: str
    future_cues: List[str]
    tags: List[str]


# Workflow State Models
class WorkflowState(BaseModel):
    ticket: Optional[Ticket] = None
    research: Optional[ResearchBundle] = None
    plan: Optional[Plan] = None
    approved: bool = False
    execution: Optional[ExecutionArtifacts] = None
    summary: Optional[Summary] = None
    trace: List[Dict[str, Any]] = Field(default_factory=list)


# Manual Models
class ManualSection(BaseModel):
    title: str
    content: str
    product_sku: str
    manual_file: str


# Configuration Models
class LLMConfig(BaseModel):
    provider: str  # "openai", "anthropic"
    model: str
    temperature: float
    api_key: str


class AppConfig(BaseModel):
    llm: LLMConfig
    data_path: str = "data"
    max_search_results: int = 6
    debug_mode: bool = False
