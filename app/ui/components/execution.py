"""
Interactive execution component with real AI integration
"""

import streamlit as st
import sys
from pathlib import Path
import time

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from app.ui.utils.state import get_workflow_state, advance_to_stage
from app.ui.utils.german import get_text
from app.core.execution_agents import ExecutionAgent


def render_execution_section():
    """Render the interactive execution section"""
    
    workflow_state = get_workflow_state()
    selected_ticket = workflow_state.get('selected_ticket')
    
    st.markdown("## 🚀 " + get_text('execution_results'))
    
    if not selected_ticket:
        st.error("Kein Ticket ausgewählt")
        return
    
    # Get required data from previous stages
    research_results = st.session_state.get('research_results')
    planning_state = st.session_state.get('planning_workflow_state')
    
    if not research_results or not planning_state or not planning_state.current_plan:
        st.error("Keine Recherche- oder Planungsergebnisse verfügbar. Bitte durchlaufen Sie zuerst die vorherigen Schritte.")
        return
    
    # Initialize execution state
    if 'execution_state' not in st.session_state:
        st.session_state.execution_state = {
            'email_generated': False,
            'email_content': None,
            'email_approved': False,
            'documentation_generated': False,
            'documentation_content': None,
            'documentation_approved': False,
            'tasks_added_to_system': False,
            'systems_updated': False
        }
    
    plan = planning_state.current_plan
    execution_state = st.session_state.execution_state
    
    # Section 1: Plan Review (Expandable)
    render_plan_review_section(plan)
    
    st.markdown("---")
    
    # Section 2: Customer Actions & Clarification Questions
    render_customer_and_questions_section(plan)
    
    st.markdown("---")
    
    # Section 3: Technical Staff Tasks & System Integration  
    render_technical_tasks_section(plan, execution_state)
    
    st.markdown("---")
    
    # Section 4: AI Task Execution
    render_ai_execution_section(plan, execution_state, selected_ticket, research_results)
    
    # Final completion check - simplified without manual approval steps
    if all([
        execution_state.get('email_generated', False),
        execution_state.get('documentation_generated', False),
        execution_state.get('systems_updated', False)
    ]):
        render_ticket_completion_section()


def render_plan_review_section(plan):
    """Section 1: Expandable plan review"""
    
    with st.expander("📋 Plan-Übersicht", expanded=False):
        st.markdown("#### ❓ Verständnisfragen")
        for i, question in enumerate(plan.clarification_questions, 1):
            importance_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            category_icons = {"technical": "🔧", "business": "💼", "customer": "👥"}
            
            importance_color = importance_colors.get(question.importance.value, "⚪")
            category_icon = category_icons.get(question.category.value, "❓")
            
            st.markdown(f"**{i}. {importance_color} {category_icon} {question.question}**")
            st.caption(question.reasoning)
        
        st.markdown("---")
        
        # Task overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🤖 KI-Agent Aufgaben**")
            for action in plan.ai_actions:
                st.markdown(f"• **{action.id}:** {action.description}")
        
        with col2:
            st.markdown("**👨‍💼 Technische Fachkraft Aufgaben**")  
            for action in plan.technical_assistant_actions:
                st.markdown(f"• **{action.id}:** {action.description}")
        
        with col3:
            st.markdown("**🏭 Kunden Aufgaben**")
            for action in plan.customer_actions:
                st.markdown(f"• **{action.id}:** {action.description}")
        
        st.markdown("---")
        
        # Work Assessment (exactly like planning stage)
        st.markdown("#### 📊 " + get_text('work_assessment'))
        
        # Two-column metrics (exactly like planning stage)
        assess_col1, assess_col2 = st.columns(2)
        
        with assess_col1:
            complexity_colors = {
                "low": "🟢",
                "medium": "🟡",
                "high": "🔴"
            }
            complexity_color = complexity_colors.get(plan.work_assessment.complexity_level.value, "⚪")
            st.metric(
                get_text('complexity_assessment'), 
                f"{complexity_color} {plan.work_assessment.complexity_level.value.title()}"
            )
        
        with assess_col2:
            st.metric("Geschätzter Aufwand", f"{plan.work_assessment.estimated_hours}h")
        
        # Detailed reasoning (exactly like planning stage)
        st.markdown("**Begründung:**")
        st.markdown(plan.work_assessment.reasoning)
        
        # Risk factors (exactly like planning stage)
        if plan.work_assessment.risk_factors:
            st.markdown("**🚨 " + get_text('risk_factors') + ":**")
            for risk in plan.work_assessment.risk_factors:
                st.markdown(f"• {risk}")


def render_customer_and_questions_section(plan):
    """Section 2: Customer actions and clarification questions"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 👥 Kunden-Aufgaben")
        if plan.customer_actions:
            for action in plan.customer_actions:
                priority_labels = {1: "Priorität 1", 2: "Priorität 2", 3: "Priorität 3"}
                priority_label = priority_labels.get(action.priority, "Standard")
                
                st.markdown(f"• **{action.id}:** {action.description}")
                st.caption(f"{priority_label}")
                if action.dependencies:
                    st.caption(f"📋 Abhängig von: {', '.join(action.dependencies)}")
        else:
            st.info("Keine Kunden-Aufgaben erforderlich")
    
    with col2:
        st.markdown("#### ❓ Verständnisfragen")
        if plan.clarification_questions:
            for i, question in enumerate(plan.clarification_questions, 1):
                importance_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                category_icons = {"technical": "🔧", "business": "💼", "customer": "👥"}
                
                importance_color = importance_colors.get(question.importance.value, "⚪")
                category_icon = category_icons.get(question.category.value, "❓")
                
                st.markdown(f"**{i}. {importance_color} {category_icon} {question.question}**")
        else:
            st.info("Keine Verständnisfragen erforderlich")


def render_technical_tasks_section(plan, execution_state):
    """Section 3: Technical staff tasks with system integration"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 👨‍💼 Technische Fachkraft Aufgaben")
        if plan.technical_assistant_actions:
            for action in plan.technical_assistant_actions:
                priority_labels = {1: "Priorität 1", 2: "Priorität 2", 3: "Priorität 3"}
                priority_label = priority_labels.get(action.priority, "Standard")
                
                st.markdown(f"• **{action.id}:** {action.description}")
                st.caption(f"{priority_label}")
                if action.dependencies:
                    st.caption(f"📋 Abhängig von: {', '.join(action.dependencies)}")
        else:
            st.info("Keine Aufgaben für technische Fachkraft")
    
    with col2:
        st.markdown("#### 🔗 System-Integration")
        
        if execution_state.get('tasks_added_to_system', False):
            st.success("✅ Aufgaben erfolgreich hinzugefügt")
        else:
            if st.button(
                "Zum Aufgabensystem hinzufügen",
                type="secondary",
                help="Fügt die Aufgaben der technischen Fachkraft zum Aufgabensystem hinzu"
            ):
                # Simulate system integration
                with st.spinner("Füge Aufgaben zum System hinzu..."):
                    time.sleep(1.5)
                
                execution_state['tasks_added_to_system'] = True
                st.success("✅ Aufgaben erfolgreich hinzugefügt")
                time.sleep(1)
                st.rerun()


def render_ai_execution_section(plan, execution_state, selected_ticket, research_results):
    """Section 4: AI task execution with real GPT-4o integration"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 🤖 KI-Agent Aufgaben")
        if plan.ai_actions:
            for action in plan.ai_actions:
                priority_labels = {1: "Priorität 1", 2: "Priorität 2", 3: "Priorität 3"}
                priority_label = priority_labels.get(action.priority, "Standard")
                
                st.markdown(f"• **{action.id}:** {action.description}")
                st.caption(f"{priority_label}")
                if action.dependencies:
                    st.caption(f"📋 Abhängig von: {', '.join(action.dependencies)}")
    
    with col2:
        st.markdown("#### ⚡ KI-Ausführung")
        
        # Task 1: Email Generation
        if not execution_state.get('email_generated', False):
            if st.button(
                "📧 E-Mail erstellen",
                type="primary",
                help="KI erstellt eine professionelle Kunden-E-Mail"
            ):
                generate_customer_email(plan, selected_ticket, research_results, execution_state)
        
        elif not execution_state.get('email_approved', False):
            if st.button(
                "📧 E-Mail überarbeiten", 
                type="secondary",
                help="E-Mail basierend auf Feedback überarbeiten"
            ):
                revise_customer_email(plan, selected_ticket, research_results, execution_state)
        
        # Task 2: Documentation Generation (only after email is approved)
        if execution_state.get('email_approved', False) and not execution_state.get('documentation_generated', False):
            if st.button(
                "📝 Dokumentation erstellen",
                type="primary", 
                help="KI erstellt interne Dokumentation"
            ):
                generate_documentation(plan, selected_ticket, research_results, execution_state)
        
        elif execution_state.get('documentation_generated', False) and not execution_state.get('documentation_approved', False):
            if st.button(
                "📝 Dokumentation überarbeiten",
                type="secondary",
                help="Dokumentation basierend auf Feedback überarbeiten"
            ):
                revise_documentation(plan, selected_ticket, research_results, execution_state)
        
        # Final system update (only after both tasks are generated)
        if (execution_state.get('email_generated', False) and 
            execution_state.get('documentation_generated', False) and
            not execution_state.get('systems_updated', False)):
            
            if st.button(
                "✅ Systeme aktualisieren",
                type="primary",
                help="Dokumentation in CRM und Ticket-System übertragen"
            ):
                update_systems(execution_state)
    
    # Display generated content sections
    render_generated_content_sections(execution_state, plan, selected_ticket, research_results)


def generate_customer_email(plan, selected_ticket, research_results, execution_state):
    """Generate customer email using AI agent"""
    
    with st.spinner("🤖 KI berücksichtigt Kommunikationsrichtlinien und erstellt E-Mail..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Load communication guidelines
            status_text.text("Lade Kommunikationsrichtlinien...")
            progress_bar.progress(0.2)
            
            guidelines_path = Path(__file__).parent.parent.parent.parent / "data" / "sops" / "communication.md"
            with open(guidelines_path, 'r', encoding='utf-8') as f:
                communication_guidelines = f.read()
            
            # Initialize execution agent
            status_text.text("Initialisiere KI-Execution Agent...")
            progress_bar.progress(0.4)
            
            execution_agent = ExecutionAgent()
            
            # Generate email
            status_text.text("Generiere professionelle Kunden-E-Mail...")
            progress_bar.progress(0.8)
            
            email_content = execution_agent.generate_customer_email(
                selected_ticket,
                research_results,
                plan,
                communication_guidelines
            )
            
            # Store results
            execution_state['email_content'] = email_content
            execution_state['email_generated'] = True
            
            progress_bar.progress(1.0)
            status_text.text("✅ E-Mail erfolgreich generiert!")
            
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Fehler bei E-Mail-Generierung: {str(e)}")


def revise_customer_email(plan, selected_ticket, research_results, execution_state):
    """Revise customer email based on feedback"""
    
    st.markdown("#### 📝 E-Mail Feedback")
    
    feedback = st.text_area(
        "Feedback zur E-Mail",
        placeholder="z.B. 'Mehr technische Details hinzufügen' oder 'Formeller formulieren'",
        help="Ihr Feedback wird von der KI analysiert und in die überarbeitete E-Mail integriert",
        key="email_feedback"
    )
    
    if st.button("🤖 E-Mail überarbeiten", disabled=not feedback.strip()):
        if feedback.strip():
            with st.spinner("🤖 KI überarbeitet E-Mail basierend auf Feedback..."):
                try:
                    # Load communication guidelines
                    guidelines_path = Path(__file__).parent.parent.parent.parent / "data" / "sops" / "communication.md"
                    with open(guidelines_path, 'r', encoding='utf-8') as f:
                        communication_guidelines = f.read()
                    
                    execution_agent = ExecutionAgent()
                    
                    # Build context for revision
                    context = execution_agent._build_email_context(selected_ticket, research_results, plan)
                    
                    revised_email = execution_agent.revise_email_with_feedback(
                        execution_state['email_content'],
                        feedback,
                        context,
                        communication_guidelines
                    )
                    
                    execution_state['email_content'] = revised_email
                    st.success("✅ E-Mail erfolgreich überarbeitet!")
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Fehler bei E-Mail-Überarbeitung: {str(e)}")


def generate_documentation(plan, selected_ticket, research_results, execution_state):
    """Generate internal documentation using AI agent"""
    
    with st.spinner("🤖 KI erstellt interne Dokumentation für CRM und Ticket-System..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Initialize execution agent
            status_text.text("Initialisiere KI-Documentation Agent...")
            progress_bar.progress(0.3)
            
            execution_agent = ExecutionAgent()
            
            # Generate documentation
            status_text.text("Erstelle strukturierte interne Dokumentation...")
            progress_bar.progress(0.8)
            
            doc_content = execution_agent.generate_documentation_summary(
                selected_ticket,
                research_results,
                plan,
                execution_state['email_content']
            )
            
            # Store results
            execution_state['documentation_content'] = doc_content
            execution_state['documentation_generated'] = True
            
            progress_bar.progress(1.0)
            status_text.text("✅ Dokumentation erfolgreich erstellt!")
            
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Fehler bei Dokumentations-Erstellung: {str(e)}")


def revise_documentation(plan, selected_ticket, research_results, execution_state):
    """Revise documentation based on feedback"""
    
    st.markdown("#### 📝 Dokumentations-Feedback")
    
    feedback = st.text_area(
        "Feedback zur Dokumentation",
        placeholder="z.B. 'Mehr Details zur Ursache' oder 'Eskalationsstatus ändern'",
        help="Ihr Feedback wird von der KI analysiert und in die überarbeitete Dokumentation integriert",
        key="documentation_feedback"
    )
    
    if st.button("🤖 Dokumentation überarbeiten", disabled=not feedback.strip()):
        if feedback.strip():
            with st.spinner("🤖 KI überarbeitet Dokumentation basierend auf Feedback..."):
                try:
                    execution_agent = ExecutionAgent()
                    
                    # Build context for revision
                    context = execution_agent._build_documentation_context(
                        selected_ticket, research_results, plan, execution_state['email_content']
                    )
                    
                    revised_doc = execution_agent.revise_documentation_with_feedback(
                        execution_state['documentation_content'],
                        feedback,
                        context
                    )
                    
                    execution_state['documentation_content'] = revised_doc
                    st.success("✅ Dokumentation erfolgreich überarbeitet!")
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Fehler bei Dokumentations-Überarbeitung: {str(e)}")


def update_systems(execution_state):
    """Mock system update for CRM and ticket systems"""
    
    with st.spinner("Übertrage Daten in CRM und Ticket-System..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Verbinde mit CRM-System...")
        progress_bar.progress(0.3)
        time.sleep(1)
        
        status_text.text("Aktualisiere Kundendaten...")
        progress_bar.progress(0.6)
        time.sleep(1)
        
        status_text.text("Schließe Ticket-Dokumentation ab...")
        progress_bar.progress(0.9)
        time.sleep(1)
        
        execution_state['systems_updated'] = True
        
        progress_bar.progress(1.0)
        status_text.text("✅ Alle Systeme erfolgreich aktualisiert!")
        
        time.sleep(1)
        st.success("✅ CRM und Ticket-System erfolgreich aktualisiert!")
        st.rerun()


def render_generated_content_sections(execution_state, plan, selected_ticket, research_results):
    """Display generated email and documentation content with improved UX"""
    
    # Email content section - Now editable and with auto-feedback form
    if execution_state.get('email_generated', False):
        st.markdown("---")
        st.markdown("### 📧 Generierte Kunden-E-Mail")
        
        # Editable email content
        edited_email = st.text_area(
            "E-Mail-Inhalt (editierbar)",
            value=execution_state['email_content'],
            height=400,
            help="Sie können die E-Mail direkt hier bearbeiten"
        )
        
        # Update email content if edited
        if edited_email != execution_state['email_content']:
            execution_state['email_content'] = edited_email
        
        # Auto-show feedback form for revisions
        st.markdown("#### 🔄 E-Mail überarbeiten")
        email_feedback = st.text_area(
            "Überarbeitungsanfrage",
            placeholder="z.B. 'Mehr technische Details hinzufügen' oder 'Formeller formulieren'",
            help="Ihre Überarbeitungsanfrage wird von der KI analysiert und in die E-Mail integriert",
            key="email_revision_feedback",
            height=80
        )
        
        if st.button("🤖 E-Mail überarbeiten", disabled=not email_feedback.strip(), key="email_revise_btn"):
            if email_feedback.strip():
                revise_email_with_ai(plan, selected_ticket, research_results, execution_state, email_feedback)
    
    # Documentation workflow - appears immediately after email generation
    if execution_state.get('email_generated', False) and not execution_state.get('documentation_generated', False):
        st.markdown("---")
        st.markdown("### 📝 Schritt 2: Interne Dokumentation")
        
        if st.button("📝 Dokumentation erstellen", type="primary", key="doc_generate_btn"):
            generate_documentation_direct(plan, selected_ticket, research_results, execution_state)
    
    # Documentation content section - editable with feedback
    if execution_state.get('documentation_generated', False):
        st.markdown("### 📝 Generierte Interne Dokumentation")
        
        # Editable documentation content
        edited_doc = st.text_area(
            "Dokumentation (editierbar)",
            value=execution_state['documentation_content'],
            height=300,
            help="Sie können die Dokumentation direkt hier bearbeiten"
        )
        
        # Update documentation if edited
        if edited_doc != execution_state['documentation_content']:
            execution_state['documentation_content'] = edited_doc
        
        # Auto-show feedback form for revisions
        st.markdown("#### 🔄 Dokumentation überarbeiten")
        doc_feedback = st.text_area(
            "Überarbeitungsanfrage",
            placeholder="z.B. 'Mehr Details zur Ursache' oder 'Eskalationsstatus ändern'",
            help="Ihre Überarbeitungsanfrage wird von der KI analysiert und in die Dokumentation integriert",
            key="doc_revision_feedback",
            height=80
        )
        
        if st.button("🤖 Dokumentation überarbeiten", disabled=not doc_feedback.strip(), key="doc_revise_btn"):
            if doc_feedback.strip():
                revise_documentation_with_ai(plan, selected_ticket, research_results, execution_state, doc_feedback)
        
        # Add documentation to ticket system
        if st.button("📝 Dokumentation dem Ticketsystem hinzufügen", type="primary", key="doc_done_btn"):
            add_documentation_to_system(execution_state)


def revise_email_with_ai(plan, selected_ticket, research_results, execution_state, feedback):
    """Revise email using AI with feedback"""
    
    with st.spinner("🤖 KI überarbeitet E-Mail basierend auf Überarbeitungsanfrage..."):
        try:
            # Load communication guidelines
            guidelines_path = Path(__file__).parent.parent.parent.parent / "data" / "sops" / "communication.md"
            with open(guidelines_path, 'r', encoding='utf-8') as f:
                communication_guidelines = f.read()
            
            execution_agent = ExecutionAgent()
            
            # Build context for revision
            context = execution_agent._build_email_context(selected_ticket, research_results, plan)
            
            revised_email = execution_agent.revise_email_with_feedback(
                execution_state['email_content'],
                feedback,
                context,
                communication_guidelines
            )
            
            execution_state['email_content'] = revised_email
            st.success("✅ E-Mail erfolgreich überarbeitet!")
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Fehler bei E-Mail-Überarbeitung: {str(e)}")


def generate_documentation_direct(plan, selected_ticket, research_results, execution_state):
    """Generate documentation directly from the new workflow"""
    
    with st.spinner("🤖 KI erstellt interne Dokumentation für CRM und Ticket-System..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Initialize execution agent
            status_text.text("Initialisiere KI-Documentation Agent...")
            progress_bar.progress(0.3)
            
            execution_agent = ExecutionAgent()
            
            # Generate documentation
            status_text.text("Erstelle strukturierte interne Dokumentation...")
            progress_bar.progress(0.8)
            
            doc_content = execution_agent.generate_documentation_summary(
                selected_ticket,
                research_results,
                plan,
                execution_state['email_content']
            )
            
            # Store results
            execution_state['documentation_content'] = doc_content
            execution_state['documentation_generated'] = True
            
            progress_bar.progress(1.0)
            status_text.text("✅ Dokumentation erfolgreich erstellt!")
            
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Fehler bei Dokumentations-Erstellung: {str(e)}")


def revise_documentation_with_ai(plan, selected_ticket, research_results, execution_state, feedback):
    """Revise documentation using AI with feedback"""
    
    with st.spinner("🤖 KI überarbeitet Dokumentation basierend auf Überarbeitungsanfrage..."):
        try:
            execution_agent = ExecutionAgent()
            
            # Build context for revision
            context = execution_agent._build_documentation_context(
                selected_ticket, research_results, plan, execution_state['email_content']
            )
            
            revised_doc = execution_agent.revise_documentation_with_feedback(
                execution_state['documentation_content'],
                feedback,
                context
            )
            
            execution_state['documentation_content'] = revised_doc
            st.success("✅ Dokumentation erfolgreich überarbeitet!")
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Fehler bei Dokumentations-Überarbeitung: {str(e)}")


def add_documentation_to_system(execution_state):
    """Mock documentation integration to ticket system"""
    
    with st.spinner("Übertrage Dokumentation in Ticket-System..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Verbinde mit Ticket-System...")
        progress_bar.progress(0.25)
        time.sleep(1)
        
        status_text.text("Übertrage Dokumentation...")
        progress_bar.progress(0.5)
        time.sleep(1)
        
        status_text.text("Aktualisiere Ticket-Status...")
        progress_bar.progress(0.75)
        time.sleep(1)
        
        execution_state['systems_updated'] = True
        
        progress_bar.progress(1.0)
        status_text.text("✅ Dokumentation erfolgreich im Ticketsystem gespeichert!")
        
        time.sleep(1)
        st.success("✅ Dokumentation erfolgreich im Ticketsystem gespeichert!")
        st.rerun()


def render_ticket_completion_section():
    """Final section to complete the ticket"""
    
    st.markdown("---")
    st.markdown("### 🎯 Ticket-Abschluss")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button(
            "🎉 Ticket schließen",
            type="primary",
            width='stretch',
            help="Schließt das Ticket ab und geht zum finalen Schritt"
        ):
            advance_to_stage('closing')
            st.success("✅ Weiterleitung zum Ticket-Abschluss...")
            time.sleep(1)
            st.rerun()
