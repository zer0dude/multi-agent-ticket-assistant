"""
Planning agents for intelligent action plan generation
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

from .llm_client import LLMClient
from .planning_models import (
    PlanRecommendation, PlanRevisionRequest, PLAN_RECOMMENDATION_SCHEMA,
    ActionItem, ClarificationQuestion, WorkAssessment
)
from .research_models import FullResearchResult


class PlanningAgent:
    """AI planning agent for intelligent plan generation"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize planning agent with LLM client"""
        self.llm_client = llm_client or LLMClient(provider="openai")
        self.model = "gpt-4o"  # Model configuration
        
    def generate_initial_plan(self, research_results: FullResearchResult, ticket: Any) -> PlanRecommendation:
        """Generate initial plan from research findings"""
        
        # Create planning context
        context = self._build_planning_context(research_results, ticket)
        
        # Create planning messages
        messages = self._create_planning_prompt(context)
        
        try:
            # Get structured response from GPT-4o
            response = self.llm_client.structured_completion(
                messages=messages,
                response_format=PLAN_RECOMMENDATION_SCHEMA,
                model=self.model
            )
            
            # Parse and validate response
            plan = self._parse_plan_response(response, context)
            
            return plan
            
        except Exception as e:
            print(f"⚠️  Planning agent failed: {e}")
            # Return fallback plan
            return self._create_fallback_plan(context)
    
    def revise_plan(
        self, 
        original_plan: PlanRecommendation, 
        human_feedback: str, 
        research_context: FullResearchResult
    ) -> PlanRecommendation:
        """Revise plan based on human feedback"""
        
        # Build revision context with proper JSON serialization
        revision_context = {
            'original_plan': original_plan.model_dump(mode='json'),  # Fix: Properly serialize datetime objects
            'human_feedback': human_feedback,
            'research_results': research_context
        }
        
        # Create revision messages
        messages = self._create_revision_prompt(revision_context)
        
        try:
            # Get revised plan from GPT-4o
            response = self.llm_client.structured_completion(
                messages=messages,
                response_format=PLAN_RECOMMENDATION_SCHEMA,
                model=self.model
            )
            
            # Parse revised plan
            revised_plan = self._parse_plan_response(response, revision_context)
            revised_plan.revision_count = original_plan.revision_count + 1
            revised_plan.original_plan_id = original_plan.generated_at.isoformat()
            
            return revised_plan
            
        except Exception as e:
            print(f"⚠️  Plan revision failed: {e}")
            # Return original plan with error note
            return original_plan
    
    def _build_planning_context(self, research_results: FullResearchResult, ticket: Any) -> Dict[str, Any]:
        """Build comprehensive context for planning - SIMPLIFIED like research.py"""
        
        # Safe attribute access for ticket
        ticket_id = getattr(ticket, 'ticket_id', 'Unknown')
        title = getattr(ticket, 'title', 'No title')
        body = getattr(ticket, 'body', 'No description')
        customer_id = getattr(ticket, 'customer_id', 'Unknown')
        priority = getattr(ticket, 'priority', None)
        related_skus = getattr(ticket, 'related_skus', [])
        
        priority_str = priority.value if priority else 'Unknown'
        
        # SIMPLIFIED: Pass research_summary directly, handle enums at access time
        # This copies the pattern from research.py which works perfectly
        context = {
            'ticket': {
                'id': ticket_id,
                'title': title,
                'description': body,
                'customer': customer_id,
                'priority': priority_str,
                'products': related_skus
            },
            'research_summary': research_results.research_summary,  # Pass object directly
            'customer_data': research_results.customer_identification,
            'manual_findings': research_results.manual_search,
            'similar_tickets': research_results.ticket_similarity
        }
        
        return context
    
    def _create_planning_prompt(self, context: Dict[str, Any]) -> list:
        """Create detailed system prompt for planning"""
        
        ticket = context['ticket']
        research = context['research_summary']
        
        system_prompt = f"""Du bist ein Senior Technical Planning Specialist bei Pumpen GmbH, einem deutschen Pumpen-Hersteller.

DEINE ROLLE:
- Erstellst intelligente Aktionspläne basierend auf KI-Recherche-Ergebnissen
- Berücksichtigst deutsche B2B-Kommunikationsstandards
- Unterscheidest zwischen KI-Agent, Techniker und Kunden-Aktionen
- Bewertest Arbeitsaufwand realistisch mit Begründung

UNTERNEHMENKONTEXT:
- Pumpen GmbH: Deutscher Industriepumpen-Hersteller
- Produkte: KW-100 (Kleinwasser), GW-300 (Großwasser), VP-200 (ViskoPro)
- Kunden: Premium-Support für etablierte Kunden
- Support-Philosophie: Technische Exzellenz mit menschlicher Kontrolle

AUFTRAG:
Basierend auf der Recherche, erstelle einen strukturierten Aktionsplan mit:

1. VERSTÄNDNISFRAGEN (3-5):
   - Jede Frage muss spezifisch zu DIESEM konkreten Ticket sein
   - Begründung: 2-3 Sätze die erklären warum diese Frage für DIESES Problem kritisch ist
   - Erkläre welche technischen Entscheidungen von der Antwort abhängen
   - Verbinde die Frage mit den vorhandenen Recherche-Erkenntnissen

2. VOLLSTÄNDIGE AUFGABENVERTEILUNG:
   
   KI-Agent (EXAKT 3 Aufgaben - STANDARDISIERT):
   - AI001: "Technische Antwort-E-Mail für Kunden vorformulieren"
   - AI002: "Ticket-Dokumentation in System eintragen"  
   - AI003: "Lern-Zusammenfassung für Ticket-Datenbank erstellen"
   
   Technische Fachkraft (3-5 Aufgaben): Verifikation, Koordination, Eskalation, Qualitätskontrolle, Wissensmanagement
   Kunde (3-5 Aufgaben): Tests, Implementierung, Feedback, Monitoring, Dokumentation
   
   WICHTIG: Plane die KOMPLETTE Ticket-Resolution von Anfang bis Ende!
   - Sofort-Aufgaben (heute)
   - Kurz-term Aufgaben (1-2 Tage)  
   - Mittel-term Aufgaben (1 Woche)
   - Berücksichtige bedingte Aufgaben ("Falls X, dann Y")
   
   AUFGABENFORMAT:
   - Erstelle saubere, professionelle Aufgabenbeschreibungen ohne übermäßige Emojis
   - Aufgaben müssen direkt in Projektmanagement-Tools importierbar sein
   - Fokus auf Klarheit, Ausführbarkeit und messbare Ergebnisse
   - Verwende nur minimale, sinnvolle Emojis wenn notwendig

3. REALISTISCHE AUFWANDSSCHÄTZUNG:
   - Schätze komplette Zeit bis Ticket-Schließung (Stunden bis Wochen)
   - Berücksichtige Worst-Case-Szenarien: Vor-Ort-Besuche, Ersatzteilbeschaffung, komplexe Diagnosen
   - Berücksichtige mögliche Verzögerungen durch Kundenverfügbarkeit, Lieferzeiten, Koordination
   - Begründung: mindestens 3-4 detaillierte Sätze mit Analyse der Zeitfaktoren

WICHTIGE PRINZIPIEN:
- Sei spezifisch zum konkreten Ticket-Problem
- Berücksichtige Kundenhistorie und Support-Tier
- Berücksichtige verfügbare Lösungsansätze
- Plane realistische Zeitschätzungen
- Identifiziere mögliche Risikofaktoren"""

        # Safely extract research data with fallback handling
        try:
            # Extract confidence assessment
            confidence_assessment = research.confidence_assessment
            confidence_value = confidence_assessment.value if confidence_assessment else "Nicht verfügbar"
            
            # Extract urgency level
            urgency_value = research.urgency_level if research.urgency_level else "Nicht verfügbar"
            
            # Extract other research data
            customer_status = research.customer_status if research.customer_status else "Nicht verfügbar"
            technical_findings = research.technical_findings if research.technical_findings else "Nicht verfügbar"
            historical_context = research.historical_context if research.historical_context else "Nicht verfügbar"
            initial_cause = research.initial_cause_assessment if research.initial_cause_assessment else "Nicht verfügbar"
            
        except Exception as e:
            print(f"⚠️ Warning: Error accessing research data: {e}")
            # Fallback values for robust operation
            confidence_value = "Nicht verfügbar"
            urgency_value = "Nicht verfügbar" 
            customer_status = "Nicht verfügbar"
            technical_findings = "Nicht verfügbar"
            historical_context = "Nicht verfügbar"
            initial_cause = "Nicht verfügbar"

        # Create JSON example outside f-string to avoid format conflicts
        json_example = """{
  "clarification_questions": [
    {
      "question": "Wie hoch ist der aktuelle Eingangsdruck?",
      "category": "technical",
      "importance": "high",
      "reasoning": "Der Eingangsdruck bestimmt..."
    }
  ],
  "ai_actions": [
    {
      "id": "AI001",
      "description": "Technische Antwort-E-Mail für Kunden vorformulieren",
      "owner": "ai_agent",
      "priority": 1,
      "estimated_time": "",
      "dependencies": [],
      "reasoning": "Erste Kommunikation..."
    },
    {
      "id": "AI002", 
      "description": "Ticket-Dokumentation in System eintragen",
      "owner": "ai_agent",
      "priority": 2,
      "estimated_time": "",
      "dependencies": ["AI001"],
      "reasoning": "Strukturierte Dokumentation..."
    },
    {
      "id": "AI003",
      "description": "Lern-Zusammenfassung für Ticket-Datenbank erstellen", 
      "owner": "ai_agent",
      "priority": 3,
      "estimated_time": "",
      "dependencies": ["AI002"],
      "reasoning": "Wissensaufbau..."
    }
  ],
  "work_assessment": {
    "complexity_level": "medium",
    "estimated_hours": 24,
    "confidence_level": "high",
    "reasoning": "Detaillierte Begründung...",
    "risk_factors": ["Ersatzteile", "Kundenzeit"],
    "success_probability": 0.8
  }
}"""

        user_prompt = f"""TICKET-INFORMATION:
Ticket-ID: {ticket['id']}
Titel: {ticket['title']}
Beschreibung: {ticket['description']}
Kunde: {ticket['customer']}
Priorität: {ticket['priority']}
Produkte: {', '.join(ticket['products'])}

RECHERCHE-ERGEBNISSE:
Kundenstatus: {customer_status}
Technische Erkenntnisse: {technical_findings}
Historischer Kontext: {historical_context}
Erste Ursacheneinschätzung: {initial_cause}
Einschätzungskonfidenz: {confidence_value}
Dringlichkeit: {urgency_value}

AUSGABE-FORMAT - KRITISCH: Verwende deutsche Inhalte aber ENGLISCHE JSON-Feldnamen und Enum-Werte:

TOP-LEVEL FELDER (Pflicht):
- "clarification_questions" (NICHT "Verständnisfragen")
- "ai_actions" (NICHT "KI_Aktionen") 
- "technical_assistant_actions" (NICHT "Techniker_Aktionen")
- "customer_actions" (NICHT "Kunden_Aktionen")
- "work_assessment" (NICHT "Arbeitsaufwand")
- "research_context_summary"
- "ticket_summary"

CLARIFICATION_QUESTIONS Felder:
- "question", "category", "importance", "reasoning"

ACTION ITEM Felder (für alle 3 Action-Arrays):
- "id": string
- "description": string
- "owner": string enum ("ai_agent", "technical_assistant", "customer")
- "priority": integer (1=highest, 2=medium, 3=lowest) - NICHT "high"/"medium"/"low"
- "estimated_time": string
- "dependencies": array of strings
- "reasoning": string

WORK_ASSESSMENT Felder:
- "complexity_level": string enum ("low", "medium", "high")
- "estimated_hours": integer (z.B. 24, NICHT "24-48 hours")
- "confidence_level": string enum ("high", "medium", "low")
- "reasoning": string
- "risk_factors": array of strings (z.B. ["Ersatzteile", "Kundenzeit"])
- "success_probability": decimal number between 0.0 and 1.0 (z.B. 0.8)

ENUM-WERTE (nur Englisch):
- category: "technical", "business", "customer"
- importance: "high", "medium", "low" 
- owner: "ai_agent", "technical_assistant", "customer"
- complexity_level: "low", "medium", "high"
- confidence_level: "high", "medium", "low"

BEISPIEL JSON-STRUKTUR (achte auf Datentypen):
{json_example}

Erstelle basierend auf diesen Informationen einen detaillierten, ticketspezifischen Aktionsplan im JSON-Format."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _create_revision_prompt(self, revision_context: Dict[str, Any]) -> list:
        """Create revision prompt with full context"""
        
        original_plan = revision_context['original_plan']
        feedback = revision_context['human_feedback']
        
        system_prompt = """Du bist ein Senior Technical Planning Specialist bei Pumpen GmbH.

AUFTRAG: PLAN-ÜBERARBEITUNG
Du erhältst einen ursprünglichen Plan und menschliches Feedback. Überarbeite den Plan und berücksichtige das Feedback, während du die technische Genauigkeit beibehältst.

REVISION-PRINZIPIEN:
- Adressiere jeden Punkt des menschlichen Feedbacks explizit
- Behalte ursprüngliche technische Erkenntnisse bei, außer sie werden korrigiert
- Passe Aufgabenzuweisungen an, wenn gewünscht
- Aktualisiere Arbeitsaufwand-Bewertung bei Umfangsänderungen
- Erkläre Änderungen in den Begründungen

AUSGABE-FORMAT - KRITISCH: Verwende deutsche Inhalte aber ENGLISCHE JSON-Feldnamen und Enum-Werte:

TOP-LEVEL FELDER (Pflicht):
- "clarification_questions" (NICHT "Verständnisfragen")
- "ai_actions" (NICHT "KI_Aktionen") 
- "technical_assistant_actions" (NICHT "Techniker_Aktionen")
- "customer_actions" (NICHT "Kunden_Aktionen")
- "work_assessment" (NICHT "Arbeitsaufwand")
- "research_context_summary"
- "ticket_summary"

CLARIFICATION_QUESTIONS Felder:
- "question", "category", "importance", "reasoning"

ACTION ITEM Felder (für alle 3 Action-Arrays):
- "id": string
- "description": string
- "owner": string enum ("ai_agent", "technical_assistant", "customer")
- "priority": integer (1=highest, 2=medium, 3=lowest) - NICHT "high"/"medium"/"low"
- "estimated_time": string
- "dependencies": array of strings
- "reasoning": string

WORK_ASSESSMENT Felder:
- "complexity_level": string enum ("low", "medium", "high")
- "estimated_hours": integer (z.B. 24, NICHT "24-48 hours")
- "confidence_level": string enum ("high", "medium", "low")
- "reasoning": string
- "risk_factors": array of strings (z.B. ["Ersatzteile", "Kundenzeit"])
- "success_probability": decimal number between 0.0 and 1.0 (z.B. 0.8)

ENUM-WERTE (nur Englisch):
- category: "technical", "business", "customer"
- importance: "high", "medium", "low" 
- owner: "ai_agent", "technical_assistant", "customer"
- complexity_level: "low", "medium", "high"
- confidence_level: "high", "medium", "low"

Kompletter überarbeiteter Plan im JSON-Format"""

        user_prompt = f"""URSPRÜNGLICHER PLAN:
{json.dumps(original_plan, indent=2, ensure_ascii=False)}

MENSCHLICHES FEEDBACK:
{feedback}

Überarbeite den Plan basierend auf diesem Feedback und gib den kompletten überarbeiteten Plan im JSON-Format zurück."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _parse_plan_response(self, response: Dict[str, Any], context: Dict[str, Any]) -> PlanRecommendation:
        """Parse and validate LLM response into PlanRecommendation"""
        
        try:
            # Add context summaries if not provided by LLM
            if 'research_context_summary' not in response:
                response['research_context_summary'] = self._create_context_summary(context)
            
            if 'ticket_summary' not in response:
                response['ticket_summary'] = self._create_ticket_summary(context.get('ticket', {}))
            
            # Validate and create PlanRecommendation
            plan = PlanRecommendation(**response)
            
            return plan
            
        except Exception as e:
            print(f"⚠️  Error parsing plan response: {e}")
            # Return fallback plan
            return self._create_fallback_plan(context)
    
    def _create_context_summary(self, context: Dict[str, Any]) -> str:
        """Create summary of research context - SIMPLIFIED like research.py"""
        research = context.get('research_summary')
        
        if not research:
            return "Recherche-Kontext nicht verfügbar"
        
        # SIMPLIFIED: Direct access like research.py - NO .get() calls on enum objects
        confidence_value = research.confidence_assessment.value if research.confidence_assessment else "Unbekannt"
        urgency_value = research.urgency_level if research.urgency_level else "Unbekannt"
        
        technical_findings = research.technical_findings if research.technical_findings else 'Keine verfügbar'
        technical_excerpt = technical_findings[:100] + "..." if len(technical_findings) > 100 else technical_findings
        
        customer_status = research.customer_status if research.customer_status else "Unbekannt"
        
        return f"""
        Kundenstatus: {customer_status}
        Technische Erkenntnisse: {technical_excerpt}
        Konfidenz: {confidence_value}
        Dringlichkeit: {urgency_value}
        """.strip()
    
    def _create_ticket_summary(self, ticket: Dict[str, Any]) -> str:
        """Create summary of ticket information"""
        return f"""
        Ticket {ticket.get('id', 'Unknown')}: {ticket.get('title', 'Kein Titel')}
        Kunde: {ticket.get('customer', 'Unbekannt')}
        Produkte: {', '.join(ticket.get('products', []))}
        Priorität: {ticket.get('priority', 'Unbekannt')}
        """.strip()
    
    def _create_fallback_plan(self, context: Dict[str, Any]) -> PlanRecommendation:
        """Create fallback plan when LLM fails"""
        
        ticket = context.get('ticket', {})
        
        return PlanRecommendation(
            clarification_questions=[
                ClarificationQuestion(
                    question="Wie ist die aktuelle Betriebssituation der Pumpe?",
                    category="technical",
                    importance="high",
                    reasoning="Diese Information ist kritisch um zu verstehen, ob das Problem kontinuierlich oder intermittierend auftritt. Die Antwort bestimmt ob eine sofortige Stilllegung erforderlich ist oder ob eine geplante Wartung ausreicht. Basierend auf den Recherche-Erkenntnissen könnte dies mit der identifizierten Ursache zusammenhängen."
                ),
                ClarificationQuestion(
                    question="Wann trat das Problem zum ersten Mal auf?",
                    category="technical", 
                    importance="medium",
                    reasoning="Der Zeitpunkt hilft bei der Ursachenanalyse und zeigt ob es sich um Verschleiß, eine plötzliche Störung oder ein schleichendes Problem handelt. Diese Information bestimmt die Dringlichkeit der Reparatur und ob Ersatzteile sofort oder geplant beschafft werden müssen."
                ),
                ClarificationQuestion(
                    question="Gibt es Veränderungen in der Betriebsumgebung?",
                    category="technical",
                    importance="medium", 
                    reasoning="Umgebungsveränderungen können die Pumpenleistung beeinflussen und helfen bei der Diagnose. Die Antwort bestimmt ob zusätzliche Schutzmaßnahmen erforderlich sind und beeinflusst die Auswahl der Lösungsansätze basierend auf den verfügbaren Handbuch-Empfehlungen."
                )
            ],
            ai_actions=[
                ActionItem(
                    id="AI001",
                    description="Technische Antwort-E-Mail für Kunden vorformulieren",
                    owner="ai_agent",
                    priority=1,
                    estimated_time="",
                    dependencies=[],
                    reasoning="Erste professionelle Kommunikation mit verfügbaren technischen Informationen basierend auf Recherche-Erkenntnissen"
                ),
                ActionItem(
                    id="AI002",
                    description="Ticket-Dokumentation in System eintragen",
                    owner="ai_agent",
                    priority=2,
                    estimated_time="",
                    dependencies=["AI001"],
                    reasoning="Strukturierte Dokumentation für effektive Teamkoordination und Nachverfolgung des Ticket-Verlaufs"
                ),
                ActionItem(
                    id="AI003",
                    description="Lern-Zusammenfassung für Ticket-Datenbank erstellen",
                    owner="ai_agent",
                    priority=3,
                    estimated_time="",
                    dependencies=["AI002"],
                    reasoning="Wissensaufbau für verbesserte zukünftige Diagnose-Geschwindigkeit und Mustererkennung"
                )
            ],
            technical_assistant_actions=[
                ActionItem(
                    id="TA001",
                    description="KI-generierte E-Mail vor Versand prüfen",
                    owner="technical_assistant",
                    priority=1,
                    estimated_time="15 Minuten",
                    dependencies=["AI001"],
                    reasoning="Menschliche Qualitätskontrolle vor Kundenkommunikation"
                ),
                ActionItem(
                    id="TA002",
                    description="Kunden-Rückfragen innerhalb 4h beantworten",
                    owner="technical_assistant",
                    priority=1,
                    estimated_time="30 Minuten",
                    dependencies=["TA001"],
                    reasoning="Schnelle Reaktion auf Kundenanfragen"
                ),
                ActionItem(
                    id="TA003",
                    description="Falls nötig, Vor-Ort-Termin koordinieren",
                    owner="technical_assistant",
                    priority=2,
                    estimated_time="45 Minuten",
                    dependencies=["TA002"],
                    reasoning="Bedingte Aufgabe für komplexe Fälle"
                ),
                ActionItem(
                    id="TA004",
                    description="Lösungsqualität nach Implementation bewerten",
                    owner="technical_assistant",
                    priority=2,
                    estimated_time="20 Minuten",
                    dependencies=["TA003"],
                    reasoning="Qualitätssicherung und Lessons Learned"
                )
            ],
            customer_actions=[
                ActionItem(
                    id="CU001",
                    description="Detaillierte technische Parameter bereitstellen",
                    owner="customer",
                    priority=1,
                    estimated_time="30 Minuten",
                    dependencies=[],
                    reasoning="Grundlage für präzise Diagnose"
                ),
                ActionItem(
                    id="CU002",
                    description="Vor-Ort-Inspektion durchführen lassen",
                    owner="customer",
                    priority=2,
                    estimated_time="2 Stunden",
                    dependencies=["CU001"],
                    reasoning="Detaillierte Zustandsbewertung der Anlage"
                ),
                ActionItem(
                    id="CU003",
                    description="Empfohlene Lösungsschritte implementieren",
                    owner="customer",
                    priority=2,
                    estimated_time="4 Stunden",
                    dependencies=["CU002"],
                    reasoning="Umsetzung der technischen Empfehlungen"
                ),
                ActionItem(
                    id="CU004",
                    description="Betriebstest und Feedback dokumentieren",
                    owner="customer",
                    priority=3,
                    estimated_time="1 Stunde",
                    dependencies=["CU003"],
                    reasoning="Bestätigung der Lösungseffektivität"
                )
            ],
            work_assessment=WorkAssessment(
                complexity_level="medium",
                estimated_hours=72,
                confidence_level="low",
                reasoning="Die Komplexität ergibt sich aus der notwendigen mehrstufigen Diagnose und möglichen Vor-Ort-Intervention bei Pumpensystemen. Bei Standard-Problemen ist mit 8-16 Stunden bis zur Ticket-Schließung zu rechnen, jedoch können Ersatzteilbeschaffung oder komplexe Systemintegration den Aufwand auf 2-3 Wochen ausdehnen. Worst-Case-Szenarien mit Technikerbesuchen, Anlagenanalyse und Systemneukonfiguration können bis zu 72 Stunden reine Arbeitszeit über mehrere Wochen verteilt in Anspruch nehmen. Verzögerungen durch Kundenverfügbarkeit, Lieferzeiten und Koordination zwischen mehreren Stakeholdern sind dabei bereits berücksichtigt.",
                risk_factors=["Unvollständige Informationen", "Mögliche Ersatzteilbeschaffung", "Kundenverfügbarkeit für Vor-Ort-Termine", "Komplexität der Systemintegration"],
                success_probability=0.6
            ),
            research_context_summary=self._create_context_summary(context),
            ticket_summary=self._create_ticket_summary(ticket)
        )
