"""
Multi-Agent Ticketing Assistant - Streamlit UI
Main application entry point
"""

import streamlit as st
from typing import Dict, Any

# Import our core data functions
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.data import load_all_data, DataLoader
from app.core.models import Ticket, TicketStatus

# Import UI components
from components.sidebar import render_sidebar
from components.context import render_context_section
from components.ticket import render_ticket_section
from components.research import render_research_section
from components.planning import render_planning_section
from components.execution import render_execution_section
from utils.state import initialize_session_state, get_workflow_state, navigate_to_stage, get_stage_status
from utils.german import GERMAN_TEXT


def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="Pumpen GmbH - Agentischer Ticket Assistent",
        page_icon="🔧",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2e6da4 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .workflow-step {
        border: 2px solid #e1e5e9;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .workflow-step.active {
        border-color: #007bff;
        background-color: #f8f9fa;
    }
    .workflow-step.complete {
        border-color: #28a745;
        background-color: #d4edda;
    }
    .german-business {
        font-family: 'Segoe UI', system-ui, sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    render_header()
    
    # Sidebar configuration
    render_sidebar()
    
    # Main content area
    render_main_content()


def render_header():
    """Render the main application header"""
    st.markdown("""
    <div class="main-header">
        <h1 style="color: white; margin: 0;">
            🔧 Agentischer Ticket Assistent
        </h1>
        <p style="color: #e3f2fd; margin: 0; font-size: 1.1rem;">
            Pumpen GmbH
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_main_content():
    """Render the main workflow content"""
    workflow_state = get_workflow_state()
    
    # Workflow progress indicator
    render_workflow_progress(workflow_state)
    
    # Main content based on current stage
    if workflow_state.get('current_stage') == 'context':
        render_context_section()
    elif workflow_state.get('current_stage') == 'ticket_input':
        render_ticket_section()
    elif workflow_state.get('current_stage') == 'research':
        render_research_section()
    elif workflow_state.get('current_stage') == 'planning':
        render_planning_section()
    elif workflow_state.get('current_stage') == 'execution':
        render_execution_section()
    else:
        # Default: context stage
        render_context_section()


def render_workflow_progress(workflow_state: Dict[str, Any]):
    """Render interactive workflow progress indicator"""
    st.markdown("### 📋 Workflow-Fortschritt")
    
    # Progress steps (6-step workflow: 0-5)
    steps = [
        ("context", "0. Demo-Kontext", "📚"),
        ("ticket_input", "1. Ticket-Eingabe", "📋"),
        ("research", "2. KI-Recherche", "🔍"),
        ("planning", "3. Aktionsplanung", "📝"),
        ("execution", "4. Ausführung", "🚀"),
        ("closing", "5. Abschluss", "✅")
    ]
    
    current_stage = workflow_state.get('current_stage', 'context')
    
    # Create progress columns
    cols = st.columns(len(steps))
    
    for i, (stage_id, stage_name, icon) in enumerate(steps):
        with cols[i]:
            status = get_stage_status(stage_id)
            
            if status == 'completed':
                # Completed stages are clickable
                if st.button(f"{icon} {stage_name}", key=f"nav_{stage_id}", help="Zurück zu diesem Schritt"):
                    if navigate_to_stage(stage_id):
                        st.rerun()
                st.success("✅ Abgeschlossen")
                
            elif status == 'current':
                # Current stage is highlighted but not clickable
                st.info(f"{icon} {stage_name}")
                
            elif status == 'available':
                # Next available stage (only next in sequence)
                if st.button(f"{icon} {stage_name}", key=f"nav_next_{stage_id}", help="Zu diesem Schritt"):
                    if navigate_to_stage(stage_id):
                        st.rerun()
                        
            else:
                # Locked stages
                st.write(f"⭕ {stage_name}")
    
    # Add navigation help text
    st.markdown("💡 *Klicken Sie auf abgeschlossene Schritte, um zurückzugehen*")
    st.markdown("---")


def load_demo_data():
    """Load demo data with error handling"""
    try:
        if 'demo_data' not in st.session_state:
            crm_data, tickets, manuals, sops = load_all_data()
            st.session_state.demo_data = {
                'crm': crm_data,
                'tickets': tickets,
                'manuals': manuals,
                'sops': sops
            }
        return st.session_state.demo_data
    except Exception as e:
        st.error(f"Fehler beim Laden der Demo-Daten: {e}")
        return None


def get_demo_tickets():
    """Get available demo tickets"""
    demo_data = load_demo_data()
    if demo_data:
        return [t for t in demo_data['tickets'] if t.status == TicketStatus.OPEN]
    return []


if __name__ == "__main__":
    main()
