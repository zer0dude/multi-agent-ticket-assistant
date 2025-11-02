"""
Planning and human approval component
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from app.ui.utils.state import get_workflow_state, advance_to_stage, update_workflow_state
from app.ui.utils.german import get_text, get_difficulty_text


def render_planning_section():
    """Render the planning and approval section"""
    
    workflow_state = get_workflow_state()
    
    st.markdown("## 📝 " + get_text('action_plan'))
    
    # Mock planning results for now
    render_mock_planning_results()
    
    # Human approval section
    render_human_approval_section()


def render_mock_planning_results():
    """Render mock planning results for UI testing"""
    
    # Difficulty assessment
    st.markdown("### 🎯 " + get_text('difficulty_level'))
    
    difficulty_col1, difficulty_col2 = st.columns([1, 3])
    with difficulty_col1:
        st.markdown("🟡 **Mittelschwer**")
    with difficulty_col2:
        st.markdown("Technische Lösung identifiziert, Kundenberatung erforderlich")
    
    st.markdown("---")
    
    # Planned steps
    st.markdown("### 📋 " + get_text('planned_steps'))
    
    # Group steps by owner
    render_steps_by_owner()
    
    st.markdown("---")


def render_steps_by_owner():
    """Render steps grouped by owner (AI, Human, Customer)"""
    
    # AI Steps
    st.markdown("#### 🤖 " + get_text('ai_steps'))
    ai_steps = [
        {"id": 1, "desc": "Technische E-Mail-Antwort an Kunden erstellen", "status": "pending"},
        {"id": 2, "desc": "Interne Dokumentation für Ticket erstellen", "status": "pending"}
    ]
    
    for step in ai_steps:
        render_step_item(step, "🤖", "blue")
    
    # Human Steps
    st.markdown("#### 👨‍💼 " + get_text('human_steps'))
    human_steps = [
        {"id": 3, "desc": "Kunden-E-Mail vor Versand prüfen", "status": "pending"},
        {"id": 4, "desc": "Bei Bedarf Vor-Ort-Service koordinieren", "status": "pending"}
    ]
    
    for step in human_steps:
        render_step_item(step, "👨‍💼", "green")
    
    # Customer Steps  
    st.markdown("#### 🏭 " + get_text('customer_steps'))
    customer_steps = [
        {"id": 5, "desc": "Saughöhe auf maximal 1,5m reduzieren", "status": "pending"},
        {"id": 6, "desc": "Nach Anpassung: Betrieb für 10 Minuten testen", "status": "pending"}
    ]
    
    for step in customer_steps:
        render_step_item(step, "🏭", "orange")


def render_step_item(step, icon, color):
    """Render individual step item"""
    
    col1, col2 = st.columns([0.1, 0.9])
    
    with col1:
        st.markdown(icon)
    
    with col2:
        status_icon = "⏳" if step["status"] == "pending" else "✅"
        st.markdown(f"{status_icon} **Schritt {step['id']}:** {step['desc']}")


def render_human_approval_section():
    """Render human-in-the-loop approval interface"""
    
    st.markdown("### 💭 " + get_text('feedback_area'))
    
    workflow_state = get_workflow_state()
    plan_approved = workflow_state.get('plan_approved', False)
    
    if not plan_approved:
        feedback_col1, feedback_col2 = st.columns([2, 1])
        
        with feedback_col1:
            human_feedback = st.text_area(
                get_text('plan_feedback'),
                placeholder="z.B. 'Zusätzlich Backup-Pumpe während Umbau vorschlagen'",
                help="Ihr Feedback wird in den überarbeiteten Plan integriert",
                key="human_feedback"
            )
        
        with feedback_col2:
            st.markdown("**Prüf-Checkliste:**")
            st.markdown("✅ Technische Genauigkeit")
            st.markdown("✅ Kunden-Kommunikation")  
            st.markdown("✅ Realistische Zeitleiste")
            st.markdown("❔ Weitere Überlegungen?")
        
        # Action buttons
        button_col1, button_col2 = st.columns(2)
        
        with button_col1:
            if st.button(
                f"🔄 {get_text('revise_plan')}", 
                help="KI wird Ihr Feedback einarbeiten",
                width='stretch'
            ):
                st.info("Plan wird überarbeitet... (Demo-Modus)")
                # In real implementation, this would trigger plan revision
        
        with button_col2:
            if st.button(
                f"✅ {get_text('approve_plan')}",
                type="primary",
                width='stretch'
            ):
                # Mark plan as approved and advance to execution
                update_workflow_state({'plan_approved': True})
                advance_to_stage('execution')
                st.rerun()
    
    else:
        # Plan already approved
        st.success("✅ Plan genehmigt und bereit zur Ausführung")
        
        if st.button("🚀 Zur Ausführung", type="primary"):
            advance_to_stage('execution')
            st.rerun()


def render_plan_briefing():
    """Render operator briefing"""
    
    st.markdown("### 📄 Operator-Briefing")
    
    with st.expander("Zusammenfassung für Support-Team", expanded=False):
        st.markdown("""
        **Situation:** GW-300 bei Acme Maschinenbau zeigt reduzierte Leistung und Kavitation
        
        **Grundursache:** Saughöhe (2m) überschreitet Spezifikation (max. 1,5m)
        
        **Empfohlene Lösung:** Saughöhen-Reduzierung oder Zulaufpumpe
        
        **Kunde-Kontext:** Premium-Kunde, technikerfahren, frühere ähnliche Probleme
        
        **Erwartete Lösung:** Technische Beratung mit klaren Handlungsanweisungen
        """)
