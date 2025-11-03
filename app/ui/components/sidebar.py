"""
Sidebar component for demo configuration and controls
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from app.core.data import load_all_data
from app.core.models import TicketStatus
from app.ui.utils.state import get_config, update_config, complete_workflow_reset, get_workflow_state
from app.ui.utils.german import get_text


def render_sidebar():
    """Render the simplified demo control sidebar"""
    
    st.sidebar.markdown("## ⚙️ Demo-Steuerung")
    
    # Debug mode toggle (prominent at top)
    config = get_config()
    debug_mode = st.sidebar.toggle(
        "🔧 Debug-Modus",
        value=config.get('debug_mode', False),
        help="Zeigt technische Debug-Informationen an"
    )
    
    # Update configuration
    update_config({'debug_mode': debug_mode})
    
    st.sidebar.markdown("---")
    
    # Reset button (prominent)
    if st.sidebar.button(
        "🔄 Workflow zurücksetzen",
        help="Demo komplett zurücksetzen und von vorne beginnen",
        type="primary",
        width='stretch'
    ):
        complete_workflow_reset()
        st.rerun()
    
    # Debug section (if enabled)
    if debug_mode:
        render_debug_section()


# Obsolete functions removed:
# - render_ticket_selection() - ticket selection now handled in main workflow
# - render_ai_configuration() - model/temperature controls no longer needed  
# - render_minimal_controls() - replaced by integrated reset button


def render_debug_section():
    """Render debug information (collapsible)"""
    config = get_config()
    
    if config['debug_mode']:
        with st.sidebar.expander("🔧 Debug Info", expanded=False):
            st.json({
                'workflow_state': dict(get_workflow_state()),
                'config': config,
                'session_keys': list(st.session_state.keys())
            })


def get_demo_tickets():
    """Get available demo tickets for selection"""
    try:
        if 'demo_data' not in st.session_state:
            crm_data, tickets, manuals, sops = load_all_data()
            from app.core.data import load_closing_notes
            closing_notes = load_closing_notes()
            st.session_state.demo_data = {
                'crm': crm_data,
                'tickets': tickets,
                'manuals': manuals,
                'sops': sops,
                'closing_notes': closing_notes
            }
        
        tickets = st.session_state.demo_data['tickets']
        return [t for t in tickets if t.status == TicketStatus.OPEN]
        
    except Exception as e:
        st.sidebar.error(f"Error loading tickets: {e}")
        return []
