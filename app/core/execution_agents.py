"""
Execution agents for AI-powered email and documentation generation
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

from .llm_client import LLMClient
from .research_models import FullResearchResult
from .planning_models import PlanRecommendation


class ExecutionAgent:
    """AI execution agent for email and documentation generation"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize execution agent with LLM client"""
        self.llm_client = llm_client or LLMClient(provider="openai")
        self.model = "gpt-4o"
        
    def generate_customer_email(
        self, 
        ticket: Any, 
        research_results: FullResearchResult,
        plan: PlanRecommendation,
        communication_guidelines: str
    ) -> str:
        """Generate customer email using communication guidelines"""
        
        # Build context for email generation
        context = self._build_email_context(ticket, research_results, plan)
        
        # Create email generation prompt
        messages = self._create_email_prompt(context, communication_guidelines)
        
        try:
            # Get email from GPT-4o
            response = self.llm_client.chat_completion(
                messages=messages,
                model=self.model,
                temperature=0.3  # Lower temperature for consistent professional tone
            )
            
            return response if response else self._create_fallback_email(context)
            
        except Exception as e:
            print(f"⚠️ Email generation failed: {e}")
            return self._create_fallback_email(context)
    
    def generate_documentation_summary(
        self,
        ticket: Any,
        research_results: FullResearchResult, 
        plan: PlanRecommendation,
        email_content: str
    ) -> str:
        """Generate internal documentation summary for CRM/ticket systems"""
        
        # Build context for documentation
        context = self._build_documentation_context(ticket, research_results, plan, email_content)
        
        # Create documentation prompt
        messages = self._create_documentation_prompt(context)
        
        try:
            # Get documentation from GPT-4o
            response = self.llm_client.chat_completion(
                messages=messages,
                model=self.model,
                temperature=0.2  # Very low temperature for consistent documentation format
            )
            
            return response if response else self._create_fallback_documentation(context)
            
        except Exception as e:
            print(f"⚠️ Documentation generation failed: {e}")
            return self._create_fallback_documentation(context)
    
    def revise_email_with_feedback(
        self,
        original_email: str,
        feedback: str,
        context: Dict[str, Any],
        communication_guidelines: str
    ) -> str:
        """Revise email based on human feedback"""
        
        messages = self._create_email_revision_prompt(original_email, feedback, context, communication_guidelines)
        
        try:
            response = self.llm_client.chat_completion(
                messages=messages,
                model=self.model,
                temperature=0.3
            )
            
            return response if response else original_email
            
        except Exception as e:
            print(f"⚠️ Email revision failed: {e}")
            return original_email
    
    def revise_documentation_with_feedback(
        self,
        original_doc: str,
        feedback: str,
        context: Dict[str, Any]
    ) -> str:
        """Revise documentation based on human feedback"""
        
        messages = self._create_documentation_revision_prompt(original_doc, feedback, context)
        
        try:
            response = self.llm_client.chat_completion(
                messages=messages,
                model=self.model,
                temperature=0.2
            )
            
            return response if response else original_doc
            
        except Exception as e:
            print(f"⚠️ Documentation revision failed: {e}")
            return original_doc
    
    def _build_email_context(self, ticket: Any, research_results: FullResearchResult, plan: PlanRecommendation) -> Dict[str, Any]:
        """Build context for email generation"""
        
        # Safe attribute access for ticket
        ticket_id = getattr(ticket, 'ticket_id', 'Unknown')
        title = getattr(ticket, 'title', 'No title')
        body = getattr(ticket, 'body', 'No description')
        customer_id = getattr(ticket, 'customer_id', 'Unknown')
        priority = getattr(ticket, 'priority', None)
        related_skus = getattr(ticket, 'related_skus', [])
        
        priority_str = priority.value if priority else 'Unknown'
        
        return {
            'ticket': {
                'id': ticket_id,
                'title': title,
                'description': body,
                'customer': customer_id,
                'priority': priority_str,
                'products': related_skus
            },
            'research_summary': research_results.research_summary,
            'plan_summary': plan.research_context_summary,
            'clarification_questions': plan.clarification_questions,
            'technical_findings': research_results.research_summary.technical_findings,
            'customer_data': research_results.customer_identification
        }
    
    def _build_documentation_context(self, ticket: Any, research_results: FullResearchResult, plan: PlanRecommendation, email_content: str) -> Dict[str, Any]:
        """Build context for documentation generation"""
        
        email_context = self._build_email_context(ticket, research_results, plan)
        email_context['generated_email'] = email_content
        email_context['work_assessment'] = plan.work_assessment
        
        return email_context
    
    def _create_email_prompt(self, context: Dict[str, Any], communication_guidelines: str) -> list:
        """Create system prompt for email generation"""
        
        ticket = context['ticket']
        research = context['research_summary']
        
        system_prompt = f"""Du bist ein Senior Technical Support Specialist bei Pumpen GmbH, einem deutschen Pumpen-Hersteller.

DEINE ROLLE:
- Erstelle professionelle Kunden-E-Mails basierend auf technischer Analyse
- Folge strikt den Unternehmens-Kommunikationsrichtlinien
- Verwende deutschen B2B-Standard mit technischer Expertise
- Sei lösungsorientiert und konkret in Handlungsempfehlungen

UNTERNEHMEN-KONTEXT:
- Pumpen GmbH: Premium deutsche Industriepumpen
- Produkte: KW-100 (Kleinwasser), GW-300 (Großwasser), VP-200 (ViskoPro)  
- Kundenstamm: Technisch versierte B2B-Kunden
- Standard: Höchste technische Qualität und Service-Excellence

KOMMUNIKATIONSRICHTLINIEN:
{communication_guidelines}

AUFTRAG:
Erstelle eine vollständige, versandfertige E-Mail an den Kunden basierend auf:
- Ticket-Informationen
- Technischer Recherche-Analyse  
- Identifizierter Problemursache
- Konkreten Lösungsempfehlungen

WICHTIGE ANFORDERUNGEN:
- Verwende EXAKT die vorgegebene E-Mail-Struktur aus den Richtlinien
- Bestätige das Problemverständnis
- Erkläre die technische Ursache verständlich
- Gib konkrete, umsetzbare Handlungsempfehlungen
- Terminiere Nachfass-Kommunikation
- Professioneller, hilfsreicher Ton
- Keine Platzhalter - vollständige, versandfertige E-Mail"""

        # Safely extract research data
        try:
            technical_findings = research.technical_findings if research.technical_findings else "Nicht verfügbar"
            customer_status = research.customer_status if research.customer_status else "Nicht verfügbar"
            initial_cause = research.initial_cause_assessment if research.initial_cause_assessment else "Nicht verfügbar"
        except Exception as e:
            print(f"⚠️ Warning: Error accessing research data: {e}")
            technical_findings = "Nicht verfügbar"
            customer_status = "Nicht verfügbar" 
            initial_cause = "Nicht verfügbar"

        user_prompt = f"""TICKET-DETAILS:
Ticket-ID: {ticket['id']}
Titel: {ticket['title']}
Kundenbeschreibung: {ticket['description']}
Kunde: {ticket['customer']}
Betroffene Produkte: {', '.join(ticket['products'])}
Priorität: {ticket['priority']}

TECHNISCHE ANALYSE:
Kundenstatus: {customer_status}
Technische Erkenntnisse: {technical_findings}
Identifizierte Ursache: {initial_cause}

VERSTÄNDNISFRAGEN (zur Information):
{chr(10).join([f"- {q.question}" for q in context.get('clarification_questions', [])])}

Erstelle eine vollständige, professionelle E-Mail die dem Kunden eine konkrete Lösung bietet und den Kommunikationsrichtlinien entspricht."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _create_documentation_prompt(self, context: Dict[str, Any]) -> list:
        """Create system prompt for internal documentation"""
        
        ticket = context['ticket']
        
        system_prompt = """Du bist ein Senior Technical Support Specialist bei Pumpen GmbH.

AUFTRAG: INTERNE DOKUMENTATION
Erstelle eine präzise, strukturierte interne Notiz für das CRM- und Ticketing-System.

FORMAT-ANFORDERUNGEN:
- Technisch präzise aber kompakt
- Für andere Techniker schnell erfassbar
- Evidenz-basierte Ursachenanalyse
- Klare Lösungsschritte dokumentiert
- Nachverfolgung und Eskalationsstatus

ZIELGRUPPE:
- Andere technische Fachkräfte
- Qualitätssicherung  
- Management (bei Eskalation)
- Wissensmanagement-System

STRUKTUR (EXAKT so verwenden):
```
TICKET: [ID] | KUNDE: [Name] | PRODUKT: [Produktname]

GRUNDURSACHE IDENTIFIZIERT:
• [Hauptursache mit technischen Details]
• [Auswirkungen/Symptome]  
• [Bestätigung durch...]

EVIDENZ:
• [Handbuch-Referenzen]
• [Ähnliche Tickets/Präzedenzfälle]
• [Technische Messungen/Symptome]

EMPFOHLENE LÖSUNG:
• Primär: [Hauptlösung mit Details]
• Sekundär: [Alternativlösung falls nötig]
• Nachfass in [Zeitrahmen] geplant

ESKALATION: [Status und Begründung]
KUNDE-KONTEXT: [Wichtige Kundenspezifika]
```

Erstelle eine vollständige, strukturierte Dokumentation nach diesem Format."""

        user_prompt = f"""TICKET-INFORMATION:
ID: {ticket['id']}
Kunde: {ticket['customer']}
Produkt: {', '.join(ticket['products'])}
Problem: {ticket['description']}

TECHNISCHE ANALYSE:
{context.get('plan_summary', 'Nicht verfügbar')}

GENERIERTE KUNDEN-E-MAIL:
{context.get('generated_email', 'Nicht verfügbar')}

ARBEITSAUFWAND-BEWERTUNG:
Komplexität: {context.get('work_assessment').complexity_level.value if context.get('work_assessment') else 'Unbekannt'}
Geschätzte Stunden: {context.get('work_assessment').estimated_hours if context.get('work_assessment') else 'Unbekannt'}

Erstelle die interne Dokumentation im vorgegebenen Format."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _create_email_revision_prompt(self, original_email: str, feedback: str, context: Dict[str, Any], communication_guidelines: str) -> list:
        """Create prompt for email revision based on feedback"""
        
        system_prompt = f"""Du bist ein Senior Technical Support Specialist bei Pumpen GmbH.

AUFTRAG: E-MAIL ÜBERARBEITUNG
Du erhältst eine ursprüngliche E-Mail und menschliches Feedback. Überarbeite die E-Mail entsprechend dem Feedback, während du die professionellen Standards und Kommunikationsrichtlinien beibehältst.

KOMMUNIKATIONSRICHTLINIEN:
{communication_guidelines}

REVISION-PRINZIPIEN:
- Adressiere jeden Punkt des Feedbacks explizit
- Behalte professionellen Ton und Struktur bei
- Verbessere technische Genauigkeit falls erforderlich
- Stelle sicher, dass die E-Mail vollständig und versandfertig bleibt"""

        user_prompt = f"""URSPRÜNGLICHE E-MAIL:
{original_email}

MENSCHLICHES FEEDBACK:
{feedback}

Überarbeite die E-Mail basierend auf diesem Feedback. Gib die komplette überarbeitete E-Mail zurück."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _create_documentation_revision_prompt(self, original_doc: str, feedback: str, context: Dict[str, Any]) -> list:
        """Create prompt for documentation revision based on feedback"""
        
        system_prompt = """Du bist ein Senior Technical Support Specialist bei Pumpen GmbH.

AUFTRAG: DOKUMENTATIONS-ÜBERARBEITUNG
Überarbeite die interne Dokumentation basierend auf menschlichem Feedback, während du das strukturierte Format und die technische Genauigkeit beibehältst."""

        user_prompt = f"""URSPRÜNGLICHE DOKUMENTATION:
{original_doc}

MENSCHLICHES FEEDBACK:
{feedback}

Überarbeite die Dokumentation basierend auf diesem Feedback. Behalte die strukturierte Format bei."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _create_fallback_email(self, context: Dict[str, Any]) -> str:
        """Create fallback email when AI fails"""
        
        ticket = context['ticket']
        
        return f"""Betreff: [{ticket['id']}] {', '.join(ticket['products'])} - Technische Unterstützung

Sehr geehrte Damen und Herren,

vielen Dank für Ihre Anfrage bezüglich {', '.join(ticket['products'])}.

Wir haben Ihr Anliegen erhalten und werden uns zeitnah mit einer detaillierten technischen Analyse bei Ihnen melden.

Falls Sie dringende Rückfragen haben, erreichen Sie unser Support-Team unter +49 89 555-8900.

Mit freundlichen Grüßen

Technisches Support-Team
Pumpen GmbH
Tel: +49 89 555-8900"""
    
    def _create_fallback_documentation(self, context: Dict[str, Any]) -> str:
        """Create fallback documentation when AI fails"""
        
        ticket = context['ticket']
        
        return f"""TICKET: {ticket['id']} | KUNDE: {ticket['customer']} | PRODUKT: {', '.join(ticket['products'])}

GRUNDURSACHE IDENTIFIZIERT:
• Technische Analyse in Bearbeitung
• Standardverfahren angewendet

EVIDENZ:
• Kundenangaben dokumentiert
• Produktspezifikationen geprüft

EMPFOHLENE LÖSUNG:
• Detaillierte Analyse erforderlich
• Nachfass in 24h geplant

ESKALATION: Standard-Bearbeitung
KUNDE-KONTEXT: Regulärer Support-Fall"""
