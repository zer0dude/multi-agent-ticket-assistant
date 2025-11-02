"""
Real research agents for the multi-agent system
"""

import time
from typing import List, Dict, Any, Optional
from app.core.models import Ticket
from app.core.data import load_all_data
from app.core.llm_client import LLMClient
from app.core.fuzzy_search import CustomerFuzzySearch
from app.core.embeddings import TicketEmbeddingSystem
from app.core.research_models import (
    FullResearchResult, CustomerMatchResult, ManualSearchResult, 
    ManualSection, TicketSimilarityResult, ResearchSummary, ConfidenceLevel
)

class ResearchOrchestrator:
    """Main orchestrator for the 4-step research process"""
    
    def __init__(self):
        """Initialize all research components"""
        self.llm_client = LLMClient()
        self.embedding_system = TicketEmbeddingSystem()
        
        # Load demo data
        self.crm_data, self.tickets, self.manuals, self.sops = load_all_data()
        
        # Initialize fuzzy search
        self.fuzzy_search = CustomerFuzzySearch(self.crm_data)
        
        # Preprocess historical tickets for embeddings (if needed)
        self._ensure_embeddings_ready()
    
    def conduct_full_research(self, ticket: Ticket) -> FullResearchResult:
        """Conduct complete 4-step research process"""
        start_time = time.time()
        errors = []
        
        try:
            # Step 1: Customer Identification
            print("Step 1: Customer identification...")
            customer_result = self._identify_customer(ticket)
            
            # Step 2: Manual Search
            print("Step 2: Manual search...")
            manual_results = self._search_manuals(ticket)
            
            # Step 3: Ticket Similarity Search
            print("Step 3: Ticket similarity search...")
            similarity_result = self._find_similar_tickets(ticket)
            
            # Step 4: Research Summary Generation
            print("Step 4: Generate research summary...")
            research_summary = self._generate_research_summary(
                ticket, customer_result, manual_results, similarity_result
            )
            
            processing_time = time.time() - start_time
            
            return FullResearchResult(
                customer_identification=customer_result,
                manual_search=manual_results,
                ticket_similarity=similarity_result,
                research_summary=research_summary,
                processing_time_seconds=processing_time,
                errors_encountered=errors
            )
            
        except Exception as e:
            errors.append(f"Research process error: {str(e)}")
            processing_time = time.time() - start_time
            
            # Return partial results with error
            return FullResearchResult(
                customer_identification=CustomerMatchResult(
                    confidence_score=0.0,
                    match_reason="Error during customer identification"
                ),
                manual_search=[],
                ticket_similarity=TicketSimilarityResult(
                    similar_tickets_found=False,
                    similar_tickets=[],
                    search_summary="Error during similarity search"
                ),
                research_summary=ResearchSummary(
                    customer_status="Error in research process",
                    technical_findings="Unable to complete research",
                    historical_context="Research incomplete",
                    confidence_assessment=ConfidenceLevel.LOW,
                    recommended_next_steps=["Manual investigation required"],
                    open_questions=["Research process failed - manual review needed"],
                    urgency_level="medium"
                ),
                processing_time_seconds=processing_time,
                errors_encountered=errors
            )
    
    def _identify_customer(self, ticket: Ticket) -> CustomerMatchResult:
        """Step 1: Identify customer using fuzzy search"""
        try:
            # Extract customer info from ticket
            company_name = ticket.customer_id  # Using customer_id as company name for manual tickets
            contact_email = ticket.created_by if '@' in ticket.created_by else ""
            
            # Use fuzzy search to match customer
            return self.fuzzy_search.find_customer_match(
                company_name=company_name,
                contact_email=contact_email
            )
            
        except Exception as e:
            return CustomerMatchResult(
                confidence_score=0.0,
                match_reason=f"Error during customer identification: {str(e)}"
            )
    
    def _search_manuals(self, ticket: Ticket) -> List[ManualSearchResult]:
        """Step 2: Search relevant manuals using LLM"""
        manual_results = []
        
        for product_sku in ticket.related_skus:
            try:
                # Find manual for this product
                relevant_manual = None
                for manual in self.manuals:
                    if manual.product_sku == product_sku:
                        relevant_manual = manual
                        break
                
                if not relevant_manual:
                    manual_results.append(ManualSearchResult(
                        product_sku=product_sku,
                        manual_found=False,
                        relevant_sections=[],
                        overall_confidence=ConfidenceLevel.LOW,
                        summary=f"No manual found for product {product_sku}"
                    ))
                    continue
                
                # Use LLM to find relevant sections
                relevant_sections = self._find_relevant_manual_sections(
                    ticket, relevant_manual
                )
                
                # Determine overall confidence
                if relevant_sections:
                    avg_relevance = sum(s.relevance_score for s in relevant_sections) / len(relevant_sections)
                    if avg_relevance >= 0.8:
                        confidence = ConfidenceLevel.HIGH
                    elif avg_relevance >= 0.6:
                        confidence = ConfidenceLevel.MEDIUM
                    else:
                        confidence = ConfidenceLevel.LOW
                else:
                    confidence = ConfidenceLevel.LOW
                
                manual_results.append(ManualSearchResult(
                    product_sku=product_sku,
                    manual_found=True,
                    relevant_sections=relevant_sections,
                    overall_confidence=confidence,
                    summary=self._create_manual_summary(relevant_sections, product_sku)
                ))
                
            except Exception as e:
                manual_results.append(ManualSearchResult(
                    product_sku=product_sku,
                    manual_found=False,
                    relevant_sections=[],
                    overall_confidence=ConfidenceLevel.LOW,
                    summary=f"Error searching manual for {product_sku}: {str(e)}"
                ))
        
        return manual_results
    
    def _find_relevant_manual_sections(self, ticket: Ticket, manual) -> List[ManualSection]:
        """Use LLM to find relevant sections in manual"""
        try:
            # Create prompt for LLM
            prompt = f"""
You are a technical support expert analyzing a product manual to find sections relevant to a customer issue.

CUSTOMER ISSUE:
Title: {ticket.title}
Description: {ticket.body}
Product: {', '.join(ticket.related_skus)}
Priority: {ticket.priority.value}

MANUAL CONTENT:
{manual.content}

TASK:
Analyze the manual and identify the most relevant sections for this customer issue. Return your response as a JSON object with this structure:

{{
    "relevant_sections": [
        {{
            "section_title": "Section name from the manual",
            "content_excerpt": "Key relevant excerpt (max 150 words)",
            "relevance_score": 0.85,
            "relevance_reason": "Why this section is relevant"
        }}
    ]
}}

GUIDELINES:
- Only include sections with relevance_score >= 0.6
- Focus on sections that directly address the issue symptoms
- Include troubleshooting, installation, and technical specifications if relevant
- Provide specific excerpts, not generic descriptions
- Maximum 5 sections
"""

            messages = [
                {"role": "system", "content": "You are a technical manual analysis expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm_client.structured_completion(messages, {})
            
            # Parse response and create ManualSection objects
            relevant_sections = []
            
            if "relevant_sections" in response:
                for section_data in response["relevant_sections"]:
                    if section_data.get("relevance_score", 0) >= 0.6:
                        section = ManualSection(
                            manual_name=f"{manual.product_sku} Manual",
                            section_title=section_data.get("section_title", "Unknown Section"),
                            content_excerpt=section_data.get("content_excerpt", ""),
                            relevance_score=min(1.0, max(0.0, section_data.get("relevance_score", 0.0))),
                            relevance_reason=section_data.get("relevance_reason", "")
                        )
                        relevant_sections.append(section)
            
            return relevant_sections
            
        except Exception as e:
            print(f"Error in manual section analysis: {e}")
            return []
    
    def _find_similar_tickets(self, ticket: Ticket) -> TicketSimilarityResult:
        """Step 3: Find similar historical tickets"""
        try:
            # Filter to historical (closed) tickets only
            historical_tickets = [t for t in self.tickets if hasattr(t, 'status') and t.status.value == 'closed']
            
            return self.embedding_system.find_similar_tickets(ticket, historical_tickets)
            
        except Exception as e:
            return TicketSimilarityResult(
                similar_tickets_found=False,
                similar_tickets=[],
                search_summary=f"Error during similarity search: {str(e)}"
            )
    
    def _generate_research_summary(self, ticket: Ticket, customer_result: CustomerMatchResult, 
                                 manual_results: List[ManualSearchResult], 
                                 similarity_result: TicketSimilarityResult) -> ResearchSummary:
        """Step 4: Generate comprehensive research summary using GPT-4o"""
        try:
            # Prepare context for LLM
            context = self._prepare_research_context(ticket, customer_result, manual_results, similarity_result)
            
            prompt = f"""
You are a senior technical support analyst creating a comprehensive research summary for a customer ticket.

{context}

TASK:
Create a detailed research summary that synthesizes all findings. Return your response as a JSON object:

{{
    "customer_status": "Brief summary of customer identification results",
    "technical_findings": "Key technical insights from manuals and documentation", 
    "historical_context": "Relevant insights from similar past tickets",
    "probable_root_cause": "Most likely root cause based on all evidence (or null if unclear)",
    "confidence_assessment": "high|medium|low",
    "recommended_next_steps": ["step 1", "step 2", "step 3"],
    "open_questions": ["question 1", "question 2"],
    "urgency_level": "low|medium|high|critical"
}}

GUIDELINES:
- Synthesize information from all sources
- Be specific and actionable
- Identify patterns and connections
- Highlight high-confidence findings
- Note gaps requiring human input
- Consider customer context (support tier, history, etc.)
"""

            messages = [
                {"role": "system", "content": "You are a senior technical support analyst with deep expertise in troubleshooting and customer service. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ]
            
            # Use GPT-4o (full model) for high-quality synthesis
            response = self.llm_client.structured_completion(messages, {}, model=self.llm_client.gpt_full)
            
            # Create ResearchSummary object
            return ResearchSummary(
                customer_status=response.get("customer_status", "Customer identification incomplete"),
                technical_findings=response.get("technical_findings", "Limited technical findings available"),
                historical_context=response.get("historical_context", "No relevant historical context found"),
                probable_root_cause=response.get("probable_root_cause"),
                confidence_assessment=ConfidenceLevel(response.get("confidence_assessment", "low")),
                recommended_next_steps=response.get("recommended_next_steps", ["Manual investigation required"]),
                open_questions=response.get("open_questions", ["Further investigation needed"]),
                urgency_level=response.get("urgency_level", "medium")
            )
            
        except Exception as e:
            return ResearchSummary(
                customer_status="Error in research summary generation",
                technical_findings=f"Research summary failed: {str(e)}",
                historical_context="Unable to generate summary",
                confidence_assessment=ConfidenceLevel.LOW,
                recommended_next_steps=["Manual review required due to system error"],
                open_questions=["System error - manual investigation needed"],
                urgency_level="medium"
            )
    
    def _prepare_research_context(self, ticket: Ticket, customer_result: CustomerMatchResult,
                                manual_results: List[ManualSearchResult], 
                                similarity_result: TicketSimilarityResult) -> str:
        """Prepare comprehensive context for research summary"""
        context = f"""
TICKET INFORMATION:
ID: {ticket.ticket_id}
Title: {ticket.title}
Description: {ticket.body}
Products: {', '.join(ticket.related_skus)}
Priority: {ticket.priority.value}
Customer: {ticket.customer_id}
Created by: {ticket.created_by}

CUSTOMER IDENTIFICATION RESULTS:
"""
        
        if customer_result.customer_id:
            context += f"✅ Customer matched: {customer_result.customer_name} (ID: {customer_result.customer_id})\n"
            context += f"Confidence: {customer_result.confidence_score:.1%}\n"
            context += f"Reason: {customer_result.match_reason}\n"
            if customer_result.relevant_data:
                context += f"Support Tier: {customer_result.relevant_data.get('support_tier', 'Unknown')}\n"
                if 'purchased_products' in customer_result.relevant_data:
                    products = [p['sku'] for p in customer_result.relevant_data['purchased_products']]
                    context += f"Customer's Products: {', '.join(products)}\n"
        else:
            context += f"❌ No customer match found: {customer_result.match_reason}\n"
        
        context += "\nMANUAL SEARCH RESULTS:\n"
        for manual_result in manual_results:
            context += f"Product {manual_result.product_sku}: "
            if manual_result.manual_found:
                context += f"Manual found, {len(manual_result.relevant_sections)} relevant sections\n"
                for section in manual_result.relevant_sections:
                    context += f"  - {section.section_title}: {section.content_excerpt[:100]}...\n"
            else:
                context += "No manual found\n"
        
        context += f"\nSIMILAR TICKETS:\n"
        if similarity_result.similar_tickets_found:
            context += f"Found {len(similarity_result.similar_tickets)} similar tickets:\n"
            for similar in similarity_result.similar_tickets:
                context += f"  - {similar.ticket_id}: {similar.title} ({similar.similarity_score:.1%} similar)\n"
                context += f"    Resolution: {similar.resolution_summary[:100]}...\n"
        else:
            context += "No similar tickets found\n"
        
        return context
    
    def _create_manual_summary(self, sections: List[ManualSection], product_sku: str) -> str:
        """Create summary of manual search results"""
        if not sections:
            return f"No relevant sections found in {product_sku} manual"
        
        return f"Found {len(sections)} relevant sections in {product_sku} manual covering {', '.join([s.section_title for s in sections])}"
    
    def _ensure_embeddings_ready(self):
        """Ensure historical ticket embeddings are available"""
        try:
            # Check if we have embeddings for historical tickets
            historical_tickets = [t for t in self.tickets if hasattr(t, 'status') and t.status.value == 'closed']
            
            missing_embeddings = []
            for ticket in historical_tickets:
                if ticket.ticket_id not in self.embedding_system.embeddings_cache:
                    missing_embeddings.append(ticket)
            
            if missing_embeddings:
                print(f"Generating embeddings for {len(missing_embeddings)} historical tickets...")
                self.embedding_system.generate_embeddings_for_tickets(missing_embeddings)
                
        except Exception as e:
            print(f"Warning: Could not prepare embeddings: {e}")
