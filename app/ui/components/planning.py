"""
Intelligent planning component with AI-powered plan generation
"""

import streamlit as st
import sys
from pathlib import Path
import time

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from app.ui.utils.state import get_workflow_state, advance_to_stage, update_workflow_state
from app.ui.utils.german import get_text
from app.core.planning_agents import PlanningAgent
from app.core.planning_models import PlanRecommendation, PlanningWorkflowState


def render_planning_section():
    """Render the intelligent planning section"""
    
    workflow_state = get_workflow_state()
    selected_ticket = workflow_state.get('selected_ticket')
    
    st.markdown("## 📝 " + get_text('action_plan'))
    
    if not selected_ticket:
        st.error("Kein Ticket ausgewählt")
        return
    
    # Get research results from previous step
    research_results = st.session_state.get('research_results')
    if not research_results:
        st.error("Keine Recherche-Ergebnisse gefunden. Bitte führen Sie zuerst die KI-Recherche durch.")
        return
    
    # Initialize planning state if needed
    if 'planning_workflow_state' not in st.session_state:
        st.session_state.planning_workflow_state = PlanningWorkflowState()
    
    # 1. Expandable Research Review Section
    render_research_review_section(research_results)
    
    st.markdown("---")
    
    # 2. Plan Generation or Display
    planning_state = st.session_state.planning_workflow_state
    
    if not planning_state.current_plan:
        render_plan_generation_section(research_results, selected_ticket)
    else:
        render_plan_recommendation_section(planning_state.current_plan)
        render_plan_revision_section(planning_state, research_results)
        render_human_approval_section(planning_state)


def render_research_review_section(research_results):
    """Render expandable research review section"""
    
    st.markdown("### 📋 " + get_text('research_review'))
    
    with st.expander("🔍 Recherche-Ergebnisse zur Überprüfung", expanded=False):
        # Display key research findings
        research_summary = research_results.research_summary
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**👥 Kundenstatus:**")
            st.markdown(research_summary.customer_status)
            
            st.markdown("**📊 Historischer Kontext:**")
            st.markdown(research_summary.historical_context)
        
        with col2:
            st.markdown("**🔧 Technische Erkenntnisse:**")
            st.markdown(research_summary.technical_findings)
            
            if hasattr(research_summary, 'initial_cause_assessment') and research_summary.initial_cause_assessment:
                st.markdown("**🎯 Erste Ursacheneinschätzung:**")
                st.info(research_summary.initial_cause_assessment)
        
        # Assessment summary
        st.markdown("**📊 Bewertung:**")
        assess_col1, assess_col2 = st.columns(2)
        
        with assess_col1:
            confidence_colors = {
                "high": "🟢",
                "medium": "🟡", 
                "low": "🔴"
            }
            confidence_color = confidence_colors.get(research_summary.confidence_assessment.value, "⚪")
            st.markdown(f"**Einschätzungskonfidenz:** {confidence_color} {research_summary.confidence_assessment.value.title()}")
        
        with assess_col2:
            urgency_colors = {
                "low": "🟢",
                "medium": "🟡",
                "high": "🟠", 
                "critical": "🔴"
            }
            urgency_color = urgency_colors.get(research_summary.urgency_level, "⚪")
            st.markdown(f"**Dringlichkeit:** {urgency_color} {research_summary.urgency_level.title()}")


def render_plan_generation_section(research_results, selected_ticket):
    """Render plan generation interface"""
    
    st.markdown("### 🤖 " + get_text('plan_recommendation'))
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button(
            "🧠 Plan erstellen",
            type="primary",
            width='stretch',
            help="KI analysiert die Recherche-Ergebnisse und erstellt einen intelligenten Aktionsplan"
        ):
            generate_intelligent_plan(research_results, selected_ticket)


def generate_intelligent_plan(research_results, selected_ticket):
    """Generate intelligent plan using AI"""
    
    # Show progress indicator
    with st.spinner("🤖 KI generiert intelligenten Aktionsplan..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Initialize planning agent
            status_text.text("Initialisiere KI-Planning Agent...")
            progress_bar.progress(0.2)
            
            planning_agent = PlanningAgent()
            
            # Generate plan
            status_text.text("Analysiere Recherche-Ergebnisse...")
            progress_bar.progress(0.5)
            
            plan = planning_agent.generate_initial_plan(research_results, selected_ticket)
            
            status_text.text("Erstelle strukturierten Aktionsplan...")
            progress_bar.progress(0.8)
            
            # Store plan in session state
            planning_state = st.session_state.planning_workflow_state
            planning_state.add_plan(plan)
            
            progress_bar.progress(1.0)
            status_text.text("✅ Plan erfolgreich generiert!")
            
            time.sleep(0.5)
            st.rerun()
            
        except Exception as e:
            # Streamlit-visible error debugging
            st.error(f"🐛 **Exact Error:** {str(e)}")
            st.code(f"Error Type: {type(e).__name__}")
            
            # Show detailed traceback in Streamlit
            import traceback
            error_trace = traceback.format_exc()
            with st.expander("🔍 Full Error Traceback", expanded=False):
                st.code(error_trace)
            
            # Debug research results structure in Streamlit
            with st.expander("🔍 Research Results Debug Info", expanded=False):
                st.write("**Research Summary Type:**", type(research_results.research_summary))
                st.write("**Confidence Assessment Type:**", type(research_results.research_summary.confidence_assessment))
                st.write("**Confidence Assessment Value:**", research_results.research_summary.confidence_assessment)
                st.write("**Urgency Level Type:**", type(research_results.research_summary.urgency_level))  
                st.write("**Urgency Level Value:**", research_results.research_summary.urgency_level)
            
            st.info("Verwende Fallback-Plan für Demo-Zwecke")


def render_plan_recommendation_section(plan: PlanRecommendation):
    """Render the generated plan recommendation"""
    
    st.markdown("### 💡 " + get_text('plan_recommendation'))
    
    # 1. Clarification Questions (no expandables, display directly)
    render_clarification_questions(plan.clarification_questions)
    
    st.markdown("---")
    
    # 2. Action Breakdown (simple lists by role)
    render_action_breakdown(plan)
    
    st.markdown("---")
    
    # 3. Work Assessment (simplified)
    render_work_assessment(plan.work_assessment)


def render_clarification_questions(questions):
    """Render clarification questions section"""
    
    st.markdown("#### ❓ " + get_text('clarification_questions'))
    
    if not questions:
        st.info("Keine Verständnisfragen erforderlich - Situation ist klar analysiert.")
        return
    
    for i, question in enumerate(questions, 1):
        importance_colors = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢"
        }
        
        category_icons = {
            "technical": "🔧",
            "business": "💼",
            "customer": "👥"
        }
        
        importance_color = importance_colors.get(question.importance.value, "⚪")
        category_icon = category_icons.get(question.category.value, "❓")
        
        # Display questions directly without expandables
        st.markdown(f"**{i}. {importance_color} {category_icon} {question.question}**")
        st.markdown(f"*{question.reasoning}*")
        if i < len(questions):  # Add separator between questions
            st.markdown("---")


def render_action_breakdown(plan: PlanRecommendation):
    """Render action items grouped by owner"""
    
    st.markdown("#### 📋 " + get_text('action_breakdown'))
    
    # Three columns for different owners
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_action_category("🤖 " + get_text('ai_steps'), plan.ai_actions, "blue")
    
    with col2:
        render_action_category("👨‍💼 " + get_text('human_steps'), plan.technical_assistant_actions, "green")
    
    with col3:
        render_action_category("🏭 " + get_text('customer_steps'), plan.customer_actions, "orange")


def render_action_category(title, actions, color):
    """Render actions for a specific category as professional list"""
    
    st.markdown(f"**{title}**")
    
    if not actions:
        st.info("Keine Aktionen erforderlich")
        return
    
    # Professional bullet point list format
    for action in actions:
        # Priority indicators without excessive emojis
        priority_labels = {1: "Priorität 1", 2: "Priorität 2", 3: "Priorität 3"}
        priority_label = priority_labels.get(action.priority, "Standard")
        
        # Clean bullet point format
        st.markdown(f"• **{action.id}:** {action.description}")
        st.caption(f"{priority_label}")
        
        # Add dependencies if they exist
        if action.dependencies:
            st.caption(f"📋 Abhängig von: {', '.join(action.dependencies)}")


def render_work_assessment(assessment):
    """Render simplified work complexity assessment"""
    
    st.markdown("#### 📊 " + get_text('work_assessment'))
    
    # Simplified assessment overview - only complexity and hours
    assess_col1, assess_col2 = st.columns(2)
    
    with assess_col1:
        complexity_colors = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🔴"
        }
        complexity_color = complexity_colors.get(assessment.complexity_level.value, "⚪")
        st.metric(
            get_text('complexity_assessment'), 
            f"{complexity_color} {assessment.complexity_level.value.title()}"
        )
    
    with assess_col2:
        st.metric("Geschätzter Aufwand", f"{assessment.estimated_hours}h")
    
    # Detailed reasoning (now more prominent)
    st.markdown("**Begründung:**")
    st.markdown(assessment.reasoning)
    
    # Risk factors
    if assessment.risk_factors:
        st.markdown("**🚨 " + get_text('risk_factors') + ":**")
        for risk in assessment.risk_factors:
            st.markdown(f"• {risk}")


def render_plan_revision_section(planning_state: PlanningWorkflowState, research_results):
    """Render plan revision interface"""
    
    if planning_state.plan_approved:
        return  # Don't show revision if already approved
    
    st.markdown("---")
    st.markdown("### 🔄 " + get_text('feedback_area'))
    
    # Feedback input
    feedback_col1, feedback_col2 = st.columns([2, 1])
    
    with feedback_col1:
        human_feedback = st.text_area(
            get_text('plan_feedback'),
            placeholder="z.B. 'Zusätzlich Backup-Pumpe während Umbau vorschlagen' oder 'Zeitschätzung zu optimistisch'",
            help="Ihr Feedback wird von der KI analysiert und in den überarbeiteten Plan integriert",
            key="plan_revision_feedback",
            height=100
        )
    
    with feedback_col2:
        st.markdown("**Überarbeitungs-Optionen:**")
        st.markdown("🔧 Technische Anpassungen")
        st.markdown("⏱️ Zeitschätzung korrigieren")  
        st.markdown("👥 Verantwortlichkeiten ändern")
        st.markdown("📋 Schritte hinzufügen/entfernen")
        
        if st.button(
            f"🤖 {get_text('revise_plan')}",
            disabled=not human_feedback.strip(),
            help="KI überarbeitet den Plan basierend auf Ihrem Feedback",
            width='stretch'
        ):
            if human_feedback.strip():
                revise_plan_with_feedback(planning_state, human_feedback, research_results)


def revise_plan_with_feedback(planning_state: PlanningWorkflowState, feedback: str, research_results):
    """Revise plan based on human feedback"""
    
    with st.spinner("🤖 KI überarbeitet Plan basierend auf Ihrem Feedback..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Initialize planning agent
            status_text.text("Analysiere menschliches Feedback...")
            progress_bar.progress(0.3)
            
            planning_agent = PlanningAgent()
            
            status_text.text("Überarbeite Plan mit KI...")
            progress_bar.progress(0.7)
            
            # Revise the plan
            revised_plan = planning_agent.revise_plan(
                planning_state.current_plan,
                feedback,
                research_results
            )
            
            # Update planning state
            planning_state.add_plan(revised_plan)
            
            progress_bar.progress(1.0)
            status_text.text("✅ Plan erfolgreich überarbeitet!")
            
            time.sleep(0.5)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Fehler bei der Plan-Überarbeitung: {str(e)}")


def render_human_approval_section(planning_state: PlanningWorkflowState):
    """Render final human approval interface"""
    
    if planning_state.plan_approved:
        st.success("✅ Plan genehmigt und bereit zur Ausführung")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 Zur Ausführung", type="primary", width='stretch'):
                advance_to_stage('execution')
                st.rerun()
    else:
        st.markdown("---")
        st.markdown("### ✅ Plan-Genehmigung")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Überprüfungs-Checkliste:**")
            st.markdown("✅ Verständnisfragen angemessen")
            st.markdown("✅ Aufgabenverteilung realistisch")
            st.markdown("✅ Zeitschätzungen plausibel")
            st.markdown("✅ Risikofaktoren berücksichtigt")
        
        with col2:
            if st.button(
                f"✅ {get_text('approve_plan')}",
                type="primary",
                width='stretch',
                help="Plan für Ausführung freigeben"
            ):
                # Approve plan and advance to execution
                planning_state.approve_current_plan()
                update_workflow_state({'plan_approved': True})
                st.success("✅ Plan genehmigt!")
                time.sleep(1)
                advance_to_stage('execution')
                st.rerun()
