"""
Interactive ticket closing component with AI-powered workflow
"""

import streamlit as st
import sys
from pathlib import Path
import time

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from app.ui.utils.state import get_workflow_state, advance_to_stage, complete_workflow_reset
from app.ui.utils.german import get_text
from app.core.closing_agents import ClosingAgent
from app.core.closing_models import (
    ClosingNotes, ClosingWorkflowState
)
from app.core.data import load_all_data, load_closing_notes


def render_closing_section():
    """Render the interactive ticket closing section"""
    
    workflow_state = get_workflow_state()
    selected_ticket = workflow_state.get('selected_ticket')
    
    st.markdown("## 🎯 Ticket-Abschluss")
    
    if not selected_ticket:
        st.error("Kein Ticket ausgewählt")
        return
    
    # Get required data from previous stages
    research_results = st.session_state.get('research_results')
    planning_state = st.session_state.get('planning_workflow_state')
    execution_state = st.session_state.get('execution_state')
    
    if not all([research_results, planning_state, execution_state]):
        st.error("Nicht alle vorherigen Schritte abgeschlossen. Bitte durchlaufen Sie zuerst Research, Planning und Execution.")
        return
    
    # Initialize closing state
    if 'closing_workflow_state' not in st.session_state:
        st.session_state.closing_workflow_state = ClosingWorkflowState()
    
    closing_state = st.session_state.closing_workflow_state
    
    # Build complete context for AI
    ticket_context = {
        'ticket': selected_ticket,
        'research_results': research_results,
        'planning_results': planning_state.current_plan,
        'execution_results': execution_state
    }
    
    # Progressive sections - show all completed sections plus active section
    
    # Section 1: Closing Notes Input (always show, but status changes)
    render_closing_notes_input(closing_state, selected_ticket)
    
    # Section 2: AI Followup Questions (show if notes submitted)
    if closing_state.notes_submitted:
        st.markdown("---")
        if not closing_state.followup_questions_generated:
            render_followup_questions_generation(closing_state, ticket_context)
        else:
            # Show completed status
            render_followup_questions_completed(closing_state)
    
    # Section 3: Followup Questions Interface (show if questions generated)
    if closing_state.followup_questions_generated:
        st.markdown("---")
        if not closing_state.report_generated:
            render_followup_questions_interface(closing_state, ticket_context)
        else:
            # Show completed status
            render_followup_answers_completed(closing_state)
    
    # Section 4: Report Generation & Review (show if answers provided)
    if closing_state.report_generated:
        st.markdown("---")
        if not closing_state.ticket_closed:
            render_report_review_interface(closing_state, ticket_context)
        else:
            # Show completed status
            render_report_completed(closing_state)
    
    # Section 5: Final Ticket Closing (show if report finalized)
    if closing_state.ticket_closed:
        st.markdown("---")
        render_ticket_closed_confirmation()


def render_ticket_context_section(selected_ticket):
    """Render expandable ticket context section like in research step"""
    
    st.markdown("### 📋 Ursprüngliches Ticket")
    with st.expander("🔍 Ticket-Details anzeigen", expanded=False):
        if selected_ticket:
            # Safe attribute access for Pydantic model
            ticket_id = getattr(selected_ticket, 'ticket_id', 'Unknown')
            title = getattr(selected_ticket, 'title', 'No title')
            body = getattr(selected_ticket, 'body', 'No description')
            customer_id = getattr(selected_ticket, 'customer_id', 'Unknown')
            
            # Handle priority enum safely
            priority = getattr(selected_ticket, 'priority', None)
            priority_str = priority.value if priority else 'Unknown'
            
            st.markdown(f"**Titel:** {title}")
            st.markdown(f"**Beschreibung:**")
            st.markdown(f"> {body}")
            st.markdown(f"**Priorität:** {priority_str}")
            st.markdown(f"**Kunde:** {customer_id}")
        else:
            st.warning("Ticket-Kontext nicht verfügbar")
    
    st.markdown("---")


def render_closing_notes_input(closing_state: ClosingWorkflowState, selected_ticket):
    """Render the closing notes input interface"""
    
    # Add ticket context section at the top (like research step)
    render_ticket_context_section(selected_ticket)
    
    st.markdown("### 📝 Schließungsnotizen")
    
    # Show completion status if already submitted
    if closing_state.notes_submitted:
        st.success("✅ Schließungsnotizen erfolgreich übermittelt")
        
        # Show submitted data in collapsed expander
        with st.expander("📋 Eingereichte Notizen anzeigen", expanded=False):
            notes = closing_state.notes_data
            if notes:
                st.markdown(f"**Primäre Lösung:** {notes.primary_solution}")
                st.markdown("**Durchgeführte Schritte:**")
                for step in notes.steps_taken:
                    st.markdown(f"• {step}")
                if notes.challenges_encountered:
                    st.markdown("**Herausforderungen:**")
                    for challenge in notes.challenges_encountered:
                        st.markdown(f"• {challenge}")
                st.markdown(f"**Kundenfeedback:** {notes.customer_feedback}")
        
        return  # Don't show form again
    
    st.markdown("Beschreiben Sie, wie das Ticket gelöst wurde:")
    
    # Example selection or custom input
    # Fix ticket_id access - try different attribute names
    ticket_id = None
    if hasattr(selected_ticket, 'ticket_id'):
        ticket_id = selected_ticket.ticket_id
    elif hasattr(selected_ticket, 'id'):
        ticket_id = selected_ticket.id
    else:
        # Try to get from dict if it's a dict
        if isinstance(selected_ticket, dict):
            ticket_id = selected_ticket.get('ticket_id') or selected_ticket.get('id')
    
    if not ticket_id:
        ticket_id = 'Unknown'
    
    # Load demo closing notes from data file
    demo_closing_notes = {}
    try:
        if 'demo_data' not in st.session_state:
            crm_data, tickets, manuals, sops = load_all_data()
            closing_notes = load_closing_notes()
            st.session_state.demo_data = {
                'crm': crm_data,
                'tickets': tickets,
                'manuals': manuals,
                'sops': sops,
                'closing_notes': closing_notes
            }
        demo_closing_notes = st.session_state.demo_data.get('closing_notes', {})
    except Exception as e:
        st.warning(f"Fehler beim Laden der Demo-Daten: {e}")
        demo_closing_notes = {}
    
    # Show ALL available demo examples regardless of current ticket
    demo_options = ["Eigene Eingabe"]
    for available_ticket_id in demo_closing_notes.keys():
        demo_options.append(f"Beispiel für {available_ticket_id}")
    
    input_type = st.selectbox(
        "Eingabe-Option",
        demo_options,
        help="Wählen Sie ein Beispiel oder geben Sie eigene Daten ein"
    )
    
    # Load demo data based on selection
    if input_type.startswith("Beispiel für"):
        # Extract ticket ID from selection (e.g., "Beispiel für T-EX1" -> "T-EX1")
        selected_ticket_id = input_type.replace("Beispiel für ", "")
        
        if selected_ticket_id in demo_closing_notes:
            demo_data = demo_closing_notes[selected_ticket_id]
            default_solution = demo_data['primary_solution']
            default_steps = '\n'.join([f"• {step}" for step in demo_data['steps_taken']])
            default_challenges = '\n'.join([f"• {challenge}" for challenge in demo_data['challenges_encountered']])
            default_feedback = demo_data['customer_feedback']
        else:
            default_solution = ""
            default_steps = ""
            default_challenges = ""
            default_feedback = ""
    else:
        default_solution = ""
        default_steps = ""
        default_challenges = ""
        default_feedback = ""
    
    # Input fields
    col1, col2 = st.columns(2)
    
    with col1:
        primary_solution = st.text_area(
            "Primäre Lösung",
            value=default_solution,
            height=100,
            help="Beschreiben Sie die Hauptlösung des Problems"
        )
        
        customer_feedback = st.text_area(
            "Kundenfeedback",
            value=default_feedback,
            height=80,
            help="Feedback und Reaktion des Kunden zur Lösung"
        )
    
    with col2:
        steps_taken = st.text_area(
            "Durchgeführte Schritte",
            value=default_steps,
            height=120,
            help="Listen Sie die konkreten Schritte auf (• als Aufzählungszeichen)"
        )
        
        challenges_encountered = st.text_area(
            "Herausforderungen (optional)",
            value=default_challenges,
            height=80,
            help="Herausforderungen während der Problemlösung"
        )
    
    # Submit notes
    if st.button("📋 Notizen übermitteln", type="primary", disabled=not primary_solution.strip()):
        if primary_solution.strip():
            # Parse steps and challenges from text
            steps_list = [step.strip().lstrip('•').strip() for step in steps_taken.split('\n') if step.strip()]
            challenges_list = [challenge.strip().lstrip('•').strip() for challenge in challenges_encountered.split('\n') if challenge.strip()]
            
            # Create ClosingNotes object
            notes = ClosingNotes(
                primary_solution=primary_solution.strip(),
                steps_taken=steps_list,
                challenges_encountered=challenges_list,
                customer_feedback=customer_feedback.strip()
            )
            
            # Update state
            closing_state.notes_submitted = True
            closing_state.notes_data = notes
            
            st.success("✅ Notizen erfolgreich übermittelt!")
            st.success("🤖 Starte automatische KI-Analyse...")
            
            # Build ticket context for AI generation
            workflow_state = get_workflow_state()
            selected_ticket = workflow_state.get('selected_ticket')
            research_results = st.session_state.get('research_results')
            planning_state = st.session_state.get('planning_workflow_state')
            execution_state = st.session_state.get('execution_state')
            
            ticket_context = {
                'ticket': selected_ticket,
                'research_results': research_results,
                'planning_results': planning_state.current_plan if planning_state else None,
                'execution_results': execution_state
            }
            
            # Automatically trigger question generation
            generate_followup_questions(closing_state, ticket_context)


def render_followup_questions_generation(closing_state: ClosingWorkflowState, ticket_context):
    """Generate AI followup questions - now automatic"""
    
    st.markdown("### 🤖 KI analysiert Vollständigkeit...")
    
    # Automatically trigger if not already done (fallback for edge cases)
    if not closing_state.followup_questions_generated:
        st.info("🤖 Automatische KI-Analyse läuft...")
        generate_followup_questions(closing_state, ticket_context)
    else:
        st.success("✅ KI-Analyse abgeschlossen!")


def generate_followup_questions(closing_state: ClosingWorkflowState, ticket_context):
    """Generate followup questions using AI"""
    
    with st.spinner("🤖 KI analysiert Schließungsnotizen und generiert Nachfragen..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Initialize closing agent
            status_text.text("Initialisiere KI-Closing Agent...")
            progress_bar.progress(0.3)
            
            closing_agent = ClosingAgent()
            
            # Generate questions
            status_text.text("Analysiere Vollständigkeit der Notizen...")
            progress_bar.progress(0.7)
            
            questions = closing_agent.generate_followup_questions(
                closing_state.notes_data,
                ticket_context
            )
            
            # Store results
            closing_state.followup_questions = questions
            closing_state.followup_questions_generated = True
            
            progress_bar.progress(1.0)
            status_text.text("✅ Nachfragen erfolgreich generiert!")
            
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Fehler bei Nachfragen-Generierung: {str(e)}")


def render_followup_questions_interface(closing_state: ClosingWorkflowState, ticket_context):
    """Display followup questions and collect answers"""
    
    st.markdown("### ❓ KI-Nachfragen zur Vollständigkeit")
    
    if not closing_state.followup_questions:
        st.error("Keine Nachfragen verfügbar")
        return
    
    # Display questions
    st.markdown("Die KI hat folgende Nachfragen zur Vervollständigung des Abschlussberichts:")
    
    for i, question in enumerate(closing_state.followup_questions, 1):
        importance_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        category_icons = {"technical": "🔧", "customer": "👥", "process": "⚙️"}
        
        importance_color = importance_colors.get(question.importance.value, "⚪")
        category_icon = category_icons.get(question.category.value, "❓")
        
        st.markdown(f"**{i}. {importance_color} {category_icon} {question.question}**")
        st.caption(question.reasoning)
        if i < len(closing_state.followup_questions):
            st.markdown("---")
    
    # Answer input
    st.markdown("#### 📝 Ihre Antworten")
    followup_answers = st.text_area(
        "Beantworten Sie die Nachfragen",
        value=closing_state.followup_answers,
        height=150,
        placeholder="Beantworten Sie die obigen Fragen um den Bericht zu vervollständigen...",
        help="Ihre Antworten helfen der KI, einen vollständigen Abschlussbericht zu erstellen"
    )
    
    # Update answers in state
    if followup_answers != closing_state.followup_answers:
        closing_state.followup_answers = followup_answers
    
    # Generate report button
    if st.button("📊 Abschlussbericht generieren", type="primary", disabled=not followup_answers.strip()):
        if followup_answers.strip():
            generate_closing_report(closing_state, ticket_context)


def generate_closing_report(closing_state: ClosingWorkflowState, ticket_context):
    """Generate final closing report using AI"""
    
    with st.spinner("🤖 KI erstellt strukturierten Abschlussbericht..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Initialize closing agent
            status_text.text("Initialisiere KI-Report Generator...")
            progress_bar.progress(0.2)
            
            closing_agent = ClosingAgent()
            
            # Generate report
            status_text.text("Analysiere alle Informationen...")
            progress_bar.progress(0.5)
            
            status_text.text("Erstelle strukturierten Abschlussbericht...")
            progress_bar.progress(0.8)
            
            report = closing_agent.generate_closing_report(
                closing_state.notes_data,
                closing_state.followup_answers,
                ticket_context
            )
            
            # Store results
            closing_state.report_content = report
            closing_state.report_generated = True
            
            progress_bar.progress(1.0)
            status_text.text("✅ Abschlussbericht erfolgreich erstellt!")
            
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Fehler bei Bericht-Generierung: {str(e)}")


def render_report_review_interface(closing_state: ClosingWorkflowState, ticket_context):
    """Display generated report with editing options"""
    
    st.markdown("### 📊 Generierter Abschlussbericht")
    
    # Display report in editable text area
    edited_report = st.text_area(
        "Abschlussbericht (editierbar)",
        value=closing_state.report_content,
        height=400,
        help="Sie können den Bericht direkt bearbeiten"
    )
    
    # Update report if edited
    if edited_report != closing_state.report_content:
        closing_state.report_content = edited_report
    
    # Feedback for AI revision
    st.markdown("#### 🔄 KI-Überarbeitung")
    report_feedback = st.text_area(
        "Überarbeitungsanfrage an KI",
        placeholder="z.B. 'Mehr Details zur Ursache hinzufügen' oder 'Empfehlungen spezifischer formulieren'",
        help="Die KI wird den Bericht basierend auf Ihrem Feedback überarbeiten",
        key="report_revision_feedback",
        height=80
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🤖 KI-Überarbeitung", disabled=not report_feedback.strip()):
            if report_feedback.strip():
                revise_report_with_ai(closing_state, ticket_context, report_feedback)
    
    with col2:
        if st.button("✅ Bericht ist final", type="primary"):
            # Final ticket closing
            close_ticket_final(closing_state, ticket_context)


def revise_report_with_ai(closing_state: ClosingWorkflowState, ticket_context, feedback):
    """Revise report using AI feedback"""
    
    with st.spinner("🤖 KI überarbeitet Abschlussbericht..."):
        try:
            closing_agent = ClosingAgent()
            
            revised_report = closing_agent.revise_report_with_feedback(
                closing_state.report_content,
                feedback,
                ticket_context
            )
            
            closing_state.report_content = revised_report
            st.success("✅ Bericht erfolgreich überarbeitet!")
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Fehler bei Bericht-Überarbeitung: {str(e)}")


def close_ticket_final(closing_state: ClosingWorkflowState, ticket_context):
    """Simulate final ticket closing process"""
    
    with st.spinner("Schließe Ticket endgültig..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        ticket_id = getattr(ticket_context.get('ticket'), 'ticket_id', 'Unknown')
        
        status_text.text("Verbinde mit Ticketing-System...")
        progress_bar.progress(0.2)
        time.sleep(1)
        
        status_text.text("Speichere Abschlussbericht...")
        progress_bar.progress(0.4)
        time.sleep(1)
        
        status_text.text("Aktualisiere Ticket-Status...")
        progress_bar.progress(0.6)
        time.sleep(1)
        
        status_text.text("Erstelle Wissensmanagement-Eintrag...")
        progress_bar.progress(0.8)
        time.sleep(1)
        
        closing_state.ticket_closed = True
        
        progress_bar.progress(1.0)
        status_text.text(f"✅ Ticket {ticket_id} erfolgreich geschlossen!")
        
        time.sleep(1)
        st.success(f"✅ Ticket {ticket_id} erfolgreich geschlossen!")
        st.rerun()


def render_followup_questions_completed(closing_state: ClosingWorkflowState):
    """Show completed status for followup questions generation"""
    
    st.markdown("### 🤖 KI-Nachfragen generiert")
    st.success(f"✅ {len(closing_state.followup_questions)} Nachfragen erfolgreich generiert")
    
    # Show summary in collapsed expander
    with st.expander("🧠 Generierte Nachfragen anzeigen", expanded=False):
        for i, question in enumerate(closing_state.followup_questions, 1):
            importance_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            category_icons = {"technical": "🔧", "customer": "👥", "process": "⚙️"}
            
            importance_color = importance_colors.get(question.importance.value, "⚪")
            category_icon = category_icons.get(question.category.value, "❓")
            
            st.markdown(f"**{i}. {importance_color} {category_icon} {question.question}**")


def render_followup_answers_completed(closing_state: ClosingWorkflowState):
    """Show completed status for followup answers"""
    
    st.markdown("### ❓ Nachfragen beantwortet")
    st.success("✅ Alle Nachfragen erfolgreich beantwortet")
    
    # Show answers in collapsed expander
    with st.expander("📝 Antworten anzeigen", expanded=False):
        st.text_area(
            "Ihre Antworten:",
            value=closing_state.followup_answers,
            height=100,
            disabled=True
        )


def render_report_completed(closing_state: ClosingWorkflowState):
    """Show completed status for report generation"""
    
    st.markdown("### 📊 Abschlussbericht finalisiert")
    st.success("✅ Abschlussbericht erfolgreich erstellt und finalisiert")
    
    # Show report in collapsed expander
    with st.expander("📋 Finaler Bericht anzeigen", expanded=False):
        st.text_area(
            "Finaler Abschlussbericht:",
            value=closing_state.report_content,
            height=300,
            disabled=True
        )


def render_ticket_closed_confirmation():
    """Display final confirmation of ticket closing"""
    
    st.markdown("### 🎉 Ticket erfolgreich geschlossen")
    
    st.success("Das Ticket wurde erfolgreich verarbeitet und geschlossen!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Status", "✅ Geschlossen")
    
    with col2:
        st.metric("Bericht", "📊 Gespeichert")
    
    with col3:
        st.metric("Wissen", "🧠 Archiviert")
    
    st.markdown("---")
    
    st.markdown("#### 📋 Zusammenfassung")
    st.markdown("- Ticket-Problem vollständig analysiert und gelöst")
    st.markdown("- Strukturierter Abschlussbericht erstellt")
    st.markdown("- Wissen für zukünftige Fälle archiviert")
    st.markdown("- Alle Systeme aktualisiert")
    
    # Option to reset demo completely
    if st.button("🔄 Demo zurücksetzen", type="primary"):
        # Complete nuclear reset of all demo data
        complete_workflow_reset()
        st.success("✅ Demo erfolgreich zurückgesetzt!")
        time.sleep(1)
        st.rerun()
