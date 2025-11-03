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
                    initial_cause_assessment=None,
                    confidence_assessment=ConfidenceLevel.LOW,
                    confidence_explanation="Systemfehler - vollständige Recherche nicht möglich",
                    urgency_level="medium",
                    urgency_explanation="Standard-Dringlichkeit aufgrund von Systemfehlern",
                    relevant_manuals=[]
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
Sie sind ein Technischer Support-Experte, der ein Produkthandbuch analysiert, um für ein Kundenproblem relevante Abschnitte zu finden.

KUNDENPROBLEM:
Titel: {ticket.title}
Beschreibung: {ticket.body}
Produkt: {', '.join(ticket.related_skus)}
Priorität: {ticket.priority.value}

HANDBUCH-INHALT:
{manual.content}

AUFGABE:
Analysieren Sie das Handbuch und identifizieren Sie die relevantesten Abschnitte für dieses Kundenproblem. Antworten Sie mit einem JSON-Objekt in dieser Struktur:

{{
    "relevant_sections": [
        {{
            "section_title": "Abschnittstitel aus dem Handbuch",
            "content_excerpt": "Wichtiger relevanter Auszug (max. 150 Wörter)",
            "relevance_score": 0.85,
            "relevance_reason": "Warum dieser Abschnitt relevant ist"
        }}
    ]
}}

RICHTLINIEN:
- Nur Abschnitte mit relevance_score >= 0.6 einschließen
- Fokus auf Abschnitte, die sich direkt mit den Problemsymptomen befassen
- Fehlerbehebung, Installation und technische Spezifikationen einbeziehen falls relevant
- Spezifische Auszüge bereitstellen, keine allgemeinen Beschreibungen
- Maximal 5 Abschnitte
- Antworten Sie auf Deutsch in den Textfeldern
"""

            messages = [
                {"role": "system", "content": "Sie sind ein Experte für technische Handbuch-Analyse. Antworten Sie immer mit gültigem JSON."},
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
                search_summary=f"Fehler bei der Ähnlichkeitssuche: {str(e)}"
            )
    
    def _generate_research_summary(self, ticket: Ticket, customer_result: CustomerMatchResult, 
                                 manual_results: List[ManualSearchResult], 
                                 similarity_result: TicketSimilarityResult) -> ResearchSummary:
        """Step 4: Generate comprehensive research summary using GPT-4o"""
        try:
            # Prepare context for LLM
            context = self._prepare_research_context(ticket, customer_result, manual_results, similarity_result)
            
            prompt = f"""
Sie sind ein Senior-Technischer Support-Analyst, der eine umfassende Recherche-Zusammenfassung für ein Kundenticket erstellt.

{context}

AUFGABE:
Erstellen Sie eine detaillierte Recherche-Zusammenfassung, die alle Erkenntnisse zusammenfasst. Antworten Sie mit einem JSON-Objekt:

{{
    "customer_status": "Kurze Zusammenfassung der Kundenidentifikations-Ergebnisse",
    "technical_findings": "Wichtige technische Erkenntnisse aus Handbüchern und Dokumentation", 
    "historical_context": "Relevante Erkenntnisse aus ähnlichen früheren Tickets",
    "initial_cause_assessment": "Erste Ursacheneinschätzung basierend auf verfügbaren Indizien - formuliert mit angemessener Unsicherheit (oder null wenn völlig unklar)",
    "confidence_assessment": "high|medium|low",
    "confidence_explanation": "Begründung für das Vertrauensniveau basierend auf Datenverfügbarkeit und Übereinstimmung der Quellen",
    "urgency_level": "low|medium|high|critical",
    "urgency_explanation": "Begründung für die Dringlichkeitseinstufung basierend auf Business-Impact und technischen Faktoren"
}}

RICHTLINIEN:
- Informationen aus allen Quellen zusammenfassen
- Bei der Ursacheneinschätzung Unsicherheit sprachlich ausdrücken (z.B. "könnte darauf hindeuten", "möglicherweise verursacht durch")
- Vertrauen und Dringlichkeit ausführlich begründen
- Erkenntnisse mit hoher Zuverlässigkeit hervorheben
- Kundenkontext berücksichtigen (Support-Stufe, Historie, etc.)
- Alle Textantworten auf Deutsch verfassen
- WICHTIG: Keine nächsten Schritte oder offenen Fragen - diese werden in der Planungsphase erstellt
"""

            messages = [
                {"role": "system", "content": "Sie sind ein Senior-Technischer Support-Analyst mit tiefgreifender Expertise in Fehlerbehebung und Kundenservice. Antworten Sie immer mit gültigem JSON."},
                {"role": "user", "content": prompt}
            ]
            
            # Use GPT-4o (full model) for high-quality synthesis
            response = self.llm_client.structured_completion(messages, {}, model=self.llm_client.full_model)
            
            # Validate and sanitize LLM response
            return self._create_validated_research_summary(response, manual_results)
            
        except Exception as e:
            return ResearchSummary(
                customer_status="Error in research summary generation",
                technical_findings=f"Research summary failed: {str(e)}",
                historical_context="Unable to generate summary",
                initial_cause_assessment=None,
                confidence_assessment=ConfidenceLevel.LOW,
                confidence_explanation="Systemfehler - Zusammenfassung konnte nicht erstellt werden",
                urgency_level="medium",
                urgency_explanation="Standard-Dringlichkeit aufgrund von Systemfehlern",
                relevant_manuals=[]
            )
    
    def _prepare_research_context(self, ticket: Ticket, customer_result: CustomerMatchResult,
                                manual_results: List[ManualSearchResult], 
                                similarity_result: TicketSimilarityResult) -> str:
        """Prepare comprehensive context for research summary with robust error handling"""
        try:
            # Safe ticket information extraction
            ticket_id = getattr(ticket, 'ticket_id', 'Unknown')
            title = getattr(ticket, 'title', 'No title')
            body = getattr(ticket, 'body', 'No description')
            related_skus = getattr(ticket, 'related_skus', [])
            priority = getattr(ticket, 'priority', None)
            customer_id = getattr(ticket, 'customer_id', 'Unknown')
            created_by = getattr(ticket, 'created_by', 'Unknown')
            
            context = f"""
TICKET INFORMATION:
ID: {ticket_id}
Title: {title}
Description: {body}
Products: {', '.join(related_skus) if related_skus else 'None specified'}
Priority: {priority.value if priority else 'Unknown'}
Customer: {customer_id}
Created by: {created_by}

CUSTOMER IDENTIFICATION RESULTS:
"""
            
            # Safe customer result processing
            if customer_result and getattr(customer_result, 'customer_id', None):
                customer_name = getattr(customer_result, 'customer_name', 'Unknown')
                confidence = getattr(customer_result, 'confidence_score', 0.0)
                reason = getattr(customer_result, 'match_reason', 'No reason provided')
                
                context += f"✅ Customer matched: {customer_name} (ID: {customer_result.customer_id})\n"
                context += f"Confidence: {confidence:.1%}\n"
                context += f"Reason: {reason}\n"
                
                # Safe relevant data extraction
                relevant_data = getattr(customer_result, 'relevant_data', None)
                if relevant_data and isinstance(relevant_data, dict):
                    support_tier = relevant_data.get('support_tier', 'Unknown')
                    context += f"Support Tier: {support_tier}\n"
                    
                    # Safe purchased products extraction
                    purchased_products = relevant_data.get('purchased_products', [])
                    if purchased_products and isinstance(purchased_products, list):
                        try:
                            products = [p.get('sku', 'Unknown') for p in purchased_products if isinstance(p, dict)]
                            if products:
                                context += f"Customer's Products: {', '.join(products)}\n"
                        except (AttributeError, TypeError):
                            context += "Customer's Products: Unable to extract product information\n"
            else:
                reason = getattr(customer_result, 'match_reason', 'Unknown error') if customer_result else 'Customer result missing'
                context += f"❌ No customer match found: {reason}\n"
            
            # Safe manual results processing
            context += "\nMANUAL SEARCH RESULTS:\n"
            if manual_results and isinstance(manual_results, list):
                for manual_result in manual_results:
                    if not manual_result:
                        continue
                        
                    product_sku = getattr(manual_result, 'product_sku', 'Unknown')
                    manual_found = getattr(manual_result, 'manual_found', False)
                    relevant_sections = getattr(manual_result, 'relevant_sections', [])
                    
                    context += f"Product {product_sku}: "
                    if manual_found and relevant_sections:
                        context += f"Manual found, {len(relevant_sections)} relevant sections\n"
                        for section in relevant_sections[:3]:  # Limit to first 3 sections
                            section_title = getattr(section, 'section_title', 'Unknown Section')
                            content_excerpt = getattr(section, 'content_excerpt', '')
                            # Safely truncate content
                            safe_excerpt = content_excerpt[:100] + "..." if len(content_excerpt) > 100 else content_excerpt
                            context += f"  - {section_title}: {safe_excerpt}\n"
                    else:
                        context += "No manual found or no relevant sections\n"
            else:
                context += "No manual search results available\n"
            
            # Safe similarity results processing
            context += "\nSIMILAR TICKETS:\n"
            if similarity_result and getattr(similarity_result, 'similar_tickets_found', False):
                similar_tickets = getattr(similarity_result, 'similar_tickets', [])
                if similar_tickets:
                    context += f"Found {len(similar_tickets)} similar tickets:\n"
                    for similar in similar_tickets[:3]:  # Limit to first 3 tickets
                        if not similar:
                            continue
                            
                        ticket_id = getattr(similar, 'ticket_id', 'Unknown')
                        title = getattr(similar, 'title', 'No title')
                        similarity_score = getattr(similar, 'similarity_score', 0.0)
                        resolution = getattr(similar, 'resolution_summary', '')
                        
                        context += f"  - {ticket_id}: {title} ({similarity_score:.1%} similar)\n"
                        # Safely truncate resolution
                        safe_resolution = resolution[:100] + "..." if len(resolution) > 100 else resolution
                        context += f"    Resolution: {safe_resolution or 'No resolution available'}\n"
                else:
                    context += "Similar tickets found but details unavailable\n"
            else:
                context += "No similar tickets found\n"
            
            return context
            
        except Exception as e:
            # Fallback context if everything fails
            return f"""
TICKET INFORMATION:
Error preparing research context: {str(e)}

FALLBACK CONTEXT:
This appears to be a support ticket requiring manual investigation due to context preparation failure.
Manual analysis of the ticket data will be required.
"""
    
    def _create_validated_research_summary(self, response: Dict[str, Any], manual_results: List[ManualSearchResult]) -> ResearchSummary:
        """Create and validate ResearchSummary from LLM response"""
        try:
            # Validate response structure
            if not response or not isinstance(response, dict):
                raise ValueError("Invalid response format from LLM")
            
            # Extract and validate each field
            customer_status = str(response.get("customer_status", "Kundenidentifikation unvollständig"))
            technical_findings = str(response.get("technical_findings", "Begrenzte technische Erkenntnisse verfügbar"))
            historical_context = str(response.get("historical_context", "Kein relevanter historischer Kontext gefunden"))
            
            # Handle initial_cause_assessment (can be null)
            initial_cause_assessment = response.get("initial_cause_assessment")
            if initial_cause_assessment is not None:
                initial_cause_assessment = str(initial_cause_assessment).strip()
                if not initial_cause_assessment or initial_cause_assessment.lower() in ["null", "none", ""]:
                    initial_cause_assessment = None
            
            # Validate confidence_assessment
            confidence_raw = response.get("confidence_assessment", "low")
            try:
                confidence_assessment = ConfidenceLevel(confidence_raw.lower())
            except (ValueError, AttributeError):
                print(f"Invalid confidence level: {confidence_raw}, defaulting to LOW")
                confidence_assessment = ConfidenceLevel.LOW
            
            # Extract explanations
            confidence_explanation = str(response.get("confidence_explanation", "Keine Begründung verfügbar"))
            urgency_explanation = str(response.get("urgency_explanation", "Keine Begründung verfügbar"))
            
            # Validate urgency_level
            urgency_raw = response.get("urgency_level", "medium")
            valid_urgency_levels = ["low", "medium", "high", "critical"]
            if urgency_raw and urgency_raw.lower() in valid_urgency_levels:
                urgency_level = urgency_raw.lower()
            else:
                print(f"Invalid urgency level: {urgency_raw}, defaulting to medium")
                urgency_level = "medium"
            
            # Extract relevant_manuals from manual search results for UI modal display
            relevant_manuals = []
            for manual_result in manual_results:
                if manual_result.manual_found and manual_result.relevant_sections:
                    manual_data = {
                        "sku": manual_result.product_sku,
                        "sections": []
                    }
                    
                    for section in manual_result.relevant_sections:
                        section_data = {
                            "title": section.section_title,
                            "content": section.content_excerpt,
                            "relevance_score": section.relevance_score,
                            "relevance_reason": section.relevance_reason
                        }
                        manual_data["sections"].append(section_data)
                    
                    relevant_manuals.append(manual_data)
            
            # Create validated ResearchSummary
            return ResearchSummary(
                customer_status=customer_status,
                technical_findings=technical_findings,
                historical_context=historical_context,
                initial_cause_assessment=initial_cause_assessment,
                confidence_assessment=confidence_assessment,
                confidence_explanation=confidence_explanation,
                urgency_level=urgency_level,
                urgency_explanation=urgency_explanation,
                relevant_manuals=relevant_manuals
            )
            
        except Exception as e:
            print(f"Error validating research summary response: {e}")
            # Return fallback summary
            return ResearchSummary(
                customer_status="Fehler bei der Zusammenfassungsgenerierung",
                technical_findings=f"Validierungsfehler: {str(e)}",
                historical_context="Zusammenfassung konnte nicht erstellt werden",
                initial_cause_assessment=None,
                confidence_assessment=ConfidenceLevel.LOW,
                confidence_explanation="Systemfehler - Validierung fehlgeschlagen",
                urgency_level="medium",
                urgency_explanation="Standard-Dringlichkeit aufgrund von Systemfehlern",
                relevant_manuals=[]
            )
    
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
