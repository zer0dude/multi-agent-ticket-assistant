"""
AI agents for intelligent ticket closing workflow
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from .llm_client import LLMClient
from .closing_models import (
    ClosingNotes, FollowupQuestion, ClosingReport,
    FOLLOWUP_QUESTIONS_SCHEMA, CLOSING_REPORT_SCHEMA
)


class ClosingAgent:
    """AI agent for intelligent ticket closing workflow"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize closing agent with LLM client"""
        self.llm_client = llm_client or LLMClient(provider="openai")
        self.model = "gpt-4o"
        
    def generate_followup_questions(
        self,
        closing_notes: ClosingNotes,
        ticket_context: Dict[str, Any]
    ) -> List[FollowupQuestion]:
        """Generate followup questions to ensure report completeness"""
        
        # Create context for question generation
        context = self._build_question_context(closing_notes, ticket_context)
        
        # Create followup questions prompt
        messages = self._create_followup_questions_prompt(context)
        
        try:
            # Get structured response from GPT-4o
            response = self.llm_client.structured_completion(
                messages=messages,
                response_format=FOLLOWUP_QUESTIONS_SCHEMA,
                model=self.model
            )
            
            # Parse and validate response
            questions = self._parse_followup_questions(response)
            
            return questions
            
        except Exception as e:
            print(f"⚠️ Followup questions generation failed: {e}")
            return self._create_fallback_questions()
    
    def generate_closing_report(
        self,
        closing_notes: ClosingNotes,
        followup_answers: str,
        ticket_context: Dict[str, Any]
    ) -> str:
        """Generate final closing report"""
        
        # Build context for report generation
        context = self._build_report_context(closing_notes, followup_answers, ticket_context)
        
        # Create report generation prompt
        messages = self._create_report_prompt(context)
        
        try:
            # Get structured response from GPT-4o
            response = self.llm_client.structured_completion(
                messages=messages,
                response_format=CLOSING_REPORT_SCHEMA,
                model=self.model
            )
            
            # Format the response into a readable report
            formatted_report = self._format_closing_report(response, ticket_context)
            
            return formatted_report
            
        except Exception as e:
            print(f"⚠️ Closing report generation failed: {e}")
            return self._create_fallback_report(closing_notes, ticket_context)
    
    def revise_report_with_feedback(
        self,
        original_report: str,
        feedback: str,
        ticket_context: Dict[str, Any]
    ) -> str:
        """Revise closing report based on human feedback"""
        
        messages = self._create_revision_prompt(original_report, feedback, ticket_context)
        
        try:
            response = self.llm_client.chat_completion(
                messages=messages,
                model=self.model,
                temperature=0.2
            )
            
            return response if response else original_report
            
        except Exception as e:
            print(f"⚠️ Report revision failed: {e}")
            return original_report
    
    def _build_question_context(self, closing_notes: ClosingNotes, ticket_context: Dict[str, Any]) -> Dict[str, Any]:
        """Build context for followup question generation"""
        
        ticket = ticket_context.get('ticket', {})
        
        return {
            'ticket_info': {
                'id': getattr(ticket, 'ticket_id', 'Unknown'),
                'title': getattr(ticket, 'title', 'No title'),
                'description': getattr(ticket, 'body', 'No description'),
                'customer': getattr(ticket, 'customer_id', 'Unknown'),
                'products': getattr(ticket, 'related_skus', [])
            },
            'closing_notes': {
                'primary_solution': closing_notes.primary_solution,
                'steps_taken': closing_notes.steps_taken,
                'challenges': closing_notes.challenges_encountered,
                'customer_feedback': closing_notes.customer_feedback
            },
            'research_summary': ticket_context.get('research_results', {})
        }
    
    def _build_report_context(
        self, 
        closing_notes: ClosingNotes, 
        followup_answers: str, 
        ticket_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build context for report generation"""
        
        context = self._build_question_context(closing_notes, ticket_context)
        context['followup_answers'] = followup_answers
        
        return context
    
    def _create_followup_questions_prompt(self, context: Dict[str, Any]) -> list:
        """Create system prompt for followup questions"""
        
        ticket_info = context['ticket_info']
        notes = context['closing_notes']
        
        system_prompt = """Du bist ein Senior Technical Support Specialist bei Pumpen GmbH.

AUFTRAG: NACHFRAGE-GENERIERUNG
Analysiere die Ticket-Schließungsnotizen und generiere 3-5 gezielte Nachfragen, um sicherzustellen, dass der Abschlussbericht vollständig ist.

ZIEL:
- Identifiziere fehlende Informationen für einen vollständigen Abschlussbericht
- Stelle sicher, dass alle wichtigen Aspekte der Problemlösung dokumentiert sind
- Erfasse Lessons Learned und Verbesserungsvorschläge

KATEGORIEN:
- "technical": Technische Details zur Lösung
- "customer": Kundenzufriedenheit und Follow-up
- "process": Interne Prozesse und Verbesserungen

WICHTIGKEIT:
- "high": Kritische Information fehlt
- "medium": Hilft bei Vollständigkeit  
- "low": Nice-to-have Information

PRINZIPIEN:
- Frage nur nach wirklich fehlenden Informationen
- Berücksichtige den Kontext des spezifischen Tickets
- Fokus auf Informationen, die für zukünftige ähnliche Fälle wertvoll sind
- Stelle sicher, dass jede Frage einen klaren Zweck hat"""

        user_prompt = f"""TICKET-INFORMATION:
ID: {ticket_info['id']}
Titel: {ticket_info['title']}
Beschreibung: {ticket_info['description']}
Kunde: {ticket_info['customer']}
Produkte: {', '.join(ticket_info['products'])}

SCHLIESSUNGSNOTIZEN:
Primäre Lösung: {notes['primary_solution']}

Durchgeführte Schritte:
{chr(10).join([f"• {step}" for step in notes['steps_taken']])}

Herausforderungen:
{chr(10).join([f"• {challenge}" for challenge in notes['challenges']])}

Kundenfeedback: {notes['customer_feedback']}

Generiere 3-5 gezielte Nachfragen im JSON-Format, um den Abschlussbericht zu vervollständigen."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _create_report_prompt(self, context: Dict[str, Any]) -> list:
        """Create system prompt for report generation"""
        
        system_prompt = """Du bist ein Senior Technical Support Specialist bei Pumpen GmbH.

AUFTRAG: TICKET-ABSCHLUSSBERICHT
Erstelle einen strukturierten, professionellen Abschlussbericht für das Ticketing-System.

FORMAT-ANFORDERUNGEN:
- Technisch präzise aber für alle Stakeholder verständlich
- Fokus auf Ursache, Lösung und Outcome
- Actionable Empfehlungen für die Zukunft
- Suchbare Tags für Wissensmanagement

STRUKTUR:
```
TICKET: [ID] | [KUNDE] | [PRODUKT] - GESCHLOSSEN

KONTEXT: [Kurze Zusammenfassung des Problems]

GRUNDURSACHE: [Identifizierte Hauptursache]

IMPLEMENTIERTE LÖSUNG: [Konkrete Lösungsschritte]

ERGEBNIS: [Messbare Outcomes und Kundenfeedback]

EMPFEHLUNGEN FÜR ZUKUNFT:
• [Konkrete Empfehlung 1]
• [Konkrete Empfehlung 2]
• [...]

TAGS: [Suchbare Schlüsselwörter]
```

QUALITÄTSKRITERIEN:
- Jeder Abschnitt soll eigenständig verständlich sein
- Fokus auf Lessons Learned
- Empfehlungen sollen umsetzbar sein
- Tags sollen für ähnliche Fälle hilfreich sein"""

        ticket_info = context['ticket_info']
        notes = context['closing_notes']
        followup = context.get('followup_answers', '')

        user_prompt = f"""VOLLSTÄNDIGE TICKET-INFORMATION:
ID: {ticket_info['id']}
Kunde: {ticket_info['customer']}
Produkte: {', '.join(ticket_info['products'])}
Originales Problem: {ticket_info['description']}

SCHLIESSUNGSNOTIZEN:
Primäre Lösung: {notes['primary_solution']}
Durchgeführte Schritte: {', '.join(notes['steps_taken'])}
Herausforderungen: {', '.join(notes['challenges'])}
Kundenfeedback: {notes['customer_feedback']}

ZUSÄTZLICHE INFORMATIONEN:
{followup}

Erstelle einen strukturierten Abschlussbericht im JSON-Format mit den Feldern: context_summary, root_cause, solution_implemented, outcome, future_recommendations, tags."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _create_revision_prompt(self, original_report: str, feedback: str, ticket_context: Dict[str, Any]) -> list:
        """Create prompt for report revision"""
        
        system_prompt = """Du bist ein Senior Technical Support Specialist bei Pumpen GmbH.

AUFTRAG: BERICHT-ÜBERARBEITUNG
Überarbeite den Ticket-Abschlussbericht basierend auf menschlichem Feedback, während du die professionelle Struktur und technische Genauigkeit beibehältst.

REVISION-PRINZIPIEN:
- Adressiere jeden Punkt des Feedbacks explizit
- Behalte die strukturierte Format bei
- Verbessere Klarheit und Vollständigkeit
- Stelle sicher, dass der Bericht eigenständig verständlich bleibt"""

        user_prompt = f"""URSPRÜNGLICHER BERICHT:
{original_report}

MENSCHLICHES FEEDBACK:
{feedback}

Überarbeite den Bericht basierend auf diesem Feedback und gib den kompletten überarbeiteten Bericht zurück."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _parse_followup_questions(self, response: Dict[str, Any]) -> List[FollowupQuestion]:
        """Parse and validate followup questions response"""
        
        try:
            questions_data = response.get('questions', [])
            questions = []
            
            for q_data in questions_data:
                question = FollowupQuestion.from_dict(q_data)
                questions.append(question)
            
            return questions
            
        except Exception as e:
            print(f"⚠️ Error parsing followup questions: {e}")
            return self._create_fallback_questions()
    
    def _format_closing_report(self, response: Dict[str, Any], ticket_context: Dict[str, Any]) -> str:
        """Format structured response into readable report"""
        
        ticket = ticket_context.get('ticket', {})
        ticket_id = getattr(ticket, 'ticket_id', 'Unknown')
        customer = getattr(ticket, 'customer_id', 'Unknown')
        products = ', '.join(getattr(ticket, 'related_skus', []))
        
        report = f"""TICKET: {ticket_id} | {customer} | {products} - GESCHLOSSEN

KONTEXT: {response.get('context_summary', 'Nicht verfügbar')}

GRUNDURSACHE: {response.get('root_cause', 'Nicht identifiziert')}

IMPLEMENTIERTE LÖSUNG: {response.get('solution_implemented', 'Nicht dokumentiert')}

ERGEBNIS: {response.get('outcome', 'Nicht bewertet')}

EMPFEHLUNGEN FÜR ZUKUNFT:"""
        
        recommendations = response.get('future_recommendations', [])
        for rec in recommendations:
            report += f"\n• {rec}"
        
        tags = response.get('tags', [])
        report += f"\n\nTAGS: {', '.join(tags)}"
        
        return report
    
    def _create_fallback_questions(self) -> List[FollowupQuestion]:
        """Create fallback questions when AI fails"""
        
        from .closing_models import QuestionCategory, QuestionImportance
        
        return [
            FollowupQuestion(
                question="Wurde die Lösung vom Kunden erfolgreich getestet?",
                category=QuestionCategory.CUSTOMER,
                importance=QuestionImportance.HIGH,
                reasoning="Bestätigung der Lösungseffektivität durch den Kunden ist kritisch"
            ),
            FollowupQuestion(
                question="Sind Follow-up Termine oder Wartungsarbeiten geplant?",
                category=QuestionCategory.PROCESS,
                importance=QuestionImportance.MEDIUM, 
                reasoning="Nachverfolgung hilft bei präventiver Wartung"
            ),
            FollowupQuestion(
                question="Welche Lessons Learned ergeben sich aus diesem Fall?",
                category=QuestionCategory.PROCESS,
                importance=QuestionImportance.MEDIUM,
                reasoning="Kontinuierliche Verbesserung der Support-Prozesse"
            )
        ]
    
    def _create_fallback_report(self, closing_notes: ClosingNotes, ticket_context: Dict[str, Any]) -> str:
        """Create fallback report when AI fails"""
        
        ticket = ticket_context.get('ticket', {})
        ticket_id = getattr(ticket, 'ticket_id', 'Unknown')
        customer = getattr(ticket, 'customer_id', 'Unknown')
        products = ', '.join(getattr(ticket, 'related_skus', []))
        
        return f"""TICKET: {ticket_id} | {customer} | {products} - GESCHLOSSEN

KONTEXT: Support-Ticket erfolgreich bearbeitet

GRUNDURSACHE: Wie in Closing Notes dokumentiert

IMPLEMENTIERTE LÖSUNG: {closing_notes.primary_solution}

ERGEBNIS: {closing_notes.customer_feedback}

EMPFEHLUNGEN FÜR ZUKUNFT:
• Regelmäßige Wartung empfohlen
• Kundenschulung zu Best Practices

TAGS: support, {products.lower().replace('-', '')}"""
