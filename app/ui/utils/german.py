"""
German text constants for the UI
"""

GERMAN_TEXT = {
    # Main interface
    'app_title': 'Pumpen GmbH - Agentischer Ticket Assistent',
    'app_subtitle': 'Agentischer Ticket Assistent',
    
    # Header metrics
    'active_products': 'Aktive Produkte',
    'customers': 'Kunden', 
    'open_tickets': 'Offene Tickets',
    
    # Workflow stages (0-5)
    'workflow_progress': 'Workflow-Fortschritt',
    'stage_context': 'Demo-Kontext',
    'stage_ticket_input': 'Ticket',
    'stage_research': 'KI-Recherche',
    'stage_planning': 'Aktionsplanung', 
    'stage_execution': 'Ausführung',
    'stage_closing': 'Abschluss',
    
    # Context page
    'context_title': 'Agentischer Ticket Assistent',
    'demo_overview': 'Demo-Übersicht',
    'demo_intro_paragraph': 'Diese Demo zeigt einen vollständigen KI-gestützten Support-Workflow mit menschlicher Kontrolle für die fiktive deutsche Pumpenunternehmen Pumpen GmbH und deren technischen Ticketing-Workflow. Diese Demo soll die Nutzung von KI-Agenten zur Reduzierung wichtiger menschlicher Arbeitslasten aufzeigen. Es handelt sich um eine einfache Demo, die Unternehmen dazu inspirieren soll, über ihre wichtigsten Arbeitsabläufe nachzudenken und zu überlegen, wie KI-Agenten repetitive menschliche Arbeitslasten reduzieren können.',
    'demo_technical_paragraph': 'Diese Demo nutzt mehrere KI-Agenten in separaten Stufen, um bedeutungsvolle Unterstützung zu bieten. Es werden mehrere Frameworks verwendet. Aus der Dikussion des "Context Engineering" wird das RPE (Research Planning Execution) Framework eingesetzt, um Kontextbewusstsein und hohe Planungsfähigkeiten der KI-Agenten zu gewährleisten. Human-in-the-Loop wird für die Qualitätskontrolle verwendet. Das gesamte Anwendungs-Backbone wurde ohne spezifische KI-Anbieter oder KI-Agent-Frameworks erstellt, um zu zeigen, dass KI-Applikationen keinen Vendor Lock-in haben müssen und dass spezifische KI-Agent-Frameworks nur dem Zweck der Anwendung dienen sollten.',
    'company_overview': 'Unternehmen: Pumpen GmbH',
    'company_description_expanded': 'Pumpen GmbH verkauft 3 Produkte. Eine kleine Wasserpumpe, eine große Wasserpumpe und eine Pumpe für viskose dickflüssige Medien. Jede Pumpe besitzt ihr eigenes technisches Handbuch.',
    'customer_description': 'Pumpen GmbH hat zwei Kunden: Acme, ein etablierter Premium-Kunde, der beide Arten von Wasserpumpen gekauft hat, und Biovisco, ein neuer Kunde, der die Viskosepumpe erworben hat.',
    'manual_buttons': 'Technische Handbücher',
    'manual_kleinwasser': 'Kleinwasser Handbuch',
    'manual_grosswasser': 'Großwasser Handbuch', 
    'manual_viskopro': 'ViskoPro Handbuch',
    'ticketing_system_title': 'Ticketing System von Pumpen GmbH',
    'support_system_description': 'Pumpen GmbH bietet technischen Support für seine Kunden über ein einfaches Ticketing-System. Technische Support-Mitarbeiter mit ausreichendem Fachwissen leisten diesen Support. In speziell schwierigen Fällen müssen die Tickets an die sehr beschäftigten Ingenieure weitergeleitet werden, die an den einzelnen Produkten arbeiten. Dies ist ein sehr kostspieliges Verfahren für Pumpen GmbH, da selbst die Grundunterstützung technisches Personal erfordert, das seine Zeit nicht für andere Arbeiten aufwenden kann, bei denen ihr technisches Fachwissen benötigt wird.',
    'ticket_database_description': 'Tickets werden in einer internen Datenbank zur Referenz gespeichert.',
    'onboarding_guidelines_description': 'Um technische Mitarbeiter in den Ticket-Prozess einzuarbeiten, hat das Unternehmen hilfreiche Richtlinien entwickelt.',
    'historical_tickets': 'Historische Tickets',
    'communication_guidelines': 'Kommunikationsrichtlinien',
    'view_guidelines': 'Richtlinien anzeigen',
    'start_demo': 'Demo starten',
    'products_table': 'Produkte',
    'customers_table': 'Kunden',
    'manuals_overview': 'Technische Handbücher',
    
    # Manual ticket input
    'ticket_simulation_description': 'Dieser Schritt simuliert den Eingang eines Tickets. Sie können ein eigenes Ticket schreiben oder ein vorgefertigtes Beispiel-Ticket auswählen.',
    'manual_ticket_input': 'Ticket-Formular',
    'use_example_ticket': 'Beispiel-Ticket auswählen',
    'ticket_title': 'Titel',
    'ticket_description': 'Beschreibung',
    'company_name': 'Unternehmen',
    'contact_person_name': 'Name des Ansprechpartners',
    'contact_email': 'E-Mail-Adresse',
    'select_priority': 'Priorität auswählen',
    'select_products': 'Betroffene Produkte',
    'form_validation_error': 'Bitte füllen Sie alle Pflichtfelder aus',
    'email_validation_error': 'Bitte geben Sie eine gültige E-Mail-Adresse ein',
    
    # Sidebar
    'demo_configuration': 'Demo-Konfiguration',
    'ticket_selection': 'Ticket-Auswahl',
    'ai_configuration': 'KI-Konfiguration',
    'demo_controls': 'Demo-Steuerung',
    'model': 'Model',
    'temperature': 'Temperature',
    'debug_mode': 'Debug-Modus',
    'reset_workflow': 'Workflow zurücksetzen',
    'reload_data': 'Testdaten neu laden',
    
    # Ticket section
    'ticket_information': 'Ticket-Information',
    'ticket_id': 'Ticket-ID',
    'customer': 'Kunde',
    'product': 'Produkt',
    'priority': 'Priorität',
    'description': 'Beschreibung',
    'start_research': 'KI-Recherche starten',
    'custom_ticket': 'Eigenes Ticket...',
    
    # Research section
    'research_results': 'Recherche-Ergebnisse',
    'customer_identified': 'Kunde identifiziert',
    'product_identified': 'Produkt identifiziert', 
    'relevant_documents': 'Relevante Dokumente',
    'crm_data': 'CRM-Daten',
    'manuals': 'Handbücher',
    'previous_tickets': 'Frühere Tickets',
    'open_questions': 'Offene Fragen',
    'create_plan': 'Plan erstellen',
    'hits': 'Treffer',
    'sections': 'Abschnitte',
    'similar': 'ähnlich',
    
    # Planning section
    'action_plan': 'Aktionsplan',
    'research_review': 'Recherche-Übersicht',
    'plan_recommendation': 'Plan-Empfehlung', 
    'clarification_questions': 'Verständnisfragen',
    'action_breakdown': 'Aufgabenverteilung',
    'work_assessment': 'Arbeitsaufwand-Bewertung',
    'generate_plan': 'Plan Empfehlung generieren',
    'difficulty_level': 'Schwierigkeitsgrad',
    'planned_steps': 'Geplante Schritte',
    'ai_steps': 'KI-Agent Aktionen',
    'human_steps': 'Technische Fachkraft Aktionen',
    'customer_steps': 'Kunden Aktionen',
    'feedback_area': 'Plan-Überarbeitung',
    'plan_feedback': 'Rückmeldung zum Plan',
    'revise_plan': 'Plan überarbeiten',
    'approve_plan': 'Plan genehmigen',
    'complexity_assessment': 'Komplexitätsbewertung',
    'success_probability': 'Erfolgswahrscheinlichkeit',
    'risk_factors': 'Risikofaktoren',
    'estimated_hours': 'Geschätzte Stunden',
    'confidence_level': 'Vertrauen',
    'revision_history': 'Überarbeitungshistorie',
    'technical_category': 'Technisch',
    'business_category': 'Geschäftlich', 
    'customer_category': 'Kunde',
    'high_importance': 'Hoch',
    'medium_importance': 'Mittel',
    'low_importance': 'Niedrig',
    
    # Difficulty levels
    'difficulty_easy': 'Einfach',
    'difficulty_moderate': 'Mittelschwer',
    'difficulty_hard': 'Schwer',
    
    # Execution section
    'execution_results': 'Ausführungsergebnisse',
    'customer_email': 'Kunden-E-Mail',
    'internal_documentation': 'Interne Dokumentation',
    'mark_resolved': 'Als gelöst markieren',
    'subject': 'Betreff',
    'email_body': 'E-Mail Text',
    
    # Priority levels
    'priority_low': 'Niedrig',
    'priority_medium': 'Mittel',
    'priority_high': 'Hoch',
    'priority_critical': 'Kritisch',
    
    # Status
    'status_open': 'Offen',
    'status_closed': 'Geschlossen',
    'status_in_progress': 'In Bearbeitung',
    
    # Buttons
    'btn_start': 'Starten',
    'btn_next': 'Weiter',
    'btn_back': 'Zurück',
    'btn_reset': 'Zurücksetzen',
    'btn_save': 'Speichern',
    'btn_cancel': 'Abbrechen',
    
    # Messages
    'loading': 'Wird geladen...',
    'processing': 'Wird verarbeitet...',
    'complete': 'Abgeschlossen',
    'error': 'Fehler',
    'success': 'Erfolgreich',
    
    # Help text
    'help_temperature': 'Kreativität vs. Konsistenz der KI-Antworten',
    'help_debug': 'Zeigt zusätzliche technische Informationen',
    'help_ticket_selection': 'Wählen Sie ein Demo-Ticket oder geben Sie ein eigenes ein',
    
    # Demo tickets
    'demo_ticket_1': 'T-EX1: Großwasser Problem (Acme)',
    'demo_ticket_2': 'T-EX2: ViskoPro Problem (Biovisco)',
    
    # Error messages
    'error_loading_data': 'Fehler beim Laden der Demo-Daten',
    'error_no_ticket': 'Bitte wählen Sie ein Ticket aus',
    'error_research_failed': 'Recherche fehlgeschlagen',
    'error_planning_failed': 'Planung fehlgeschlagen',
    'error_execution_failed': 'Ausführung fehlgeschlagen',
}


def get_text(key: str, default: str = None) -> str:
    """Get German text by key"""
    return GERMAN_TEXT.get(key, default or key)


def get_priority_text(priority: str) -> str:
    """Get German priority text"""
    priority_map = {
        'low': get_text('priority_low'),
        'medium': get_text('priority_medium'),
        'high': get_text('priority_high'),
        'critical': get_text('priority_critical')
    }
    return priority_map.get(priority.lower(), priority)


def get_status_text(status: str) -> str:
    """Get German status text"""
    status_map = {
        'open': get_text('status_open'),
        'closed': get_text('status_closed'),
        'in_progress': get_text('status_in_progress')
    }
    return status_map.get(status.lower(), status)


def get_difficulty_text(difficulty: str) -> str:
    """Get German difficulty text"""
    difficulty_map = {
        'easy': get_text('difficulty_easy'),
        'moderate': get_text('difficulty_moderate'),
        'hard': get_text('difficulty_hard')
    }
    return difficulty_map.get(difficulty.lower(), difficulty)
