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
from app.ui.utils.state import get_config, update_config, reset_workflow, get_workflow_state
from app.ui.utils.german import get_text


def render_sidebar():
    """Render the minimal configuration sidebar"""
    
    st.sidebar.markdown("## ⚙️ Konfiguration")
    
    # AI configuration section  
    render_ai_configuration()
    
    st.sidebar.markdown("---")
    
    # Minimal demo controls
    render_minimal_controls()
    
    # Debug section (collapsible)
    render_debug_section()


def render_ticket_selection():
    """Render ticket selection controls"""
    st.sidebar.markdown("### 📋 " + get_text('ticket_selection'))
    
    # Get available demo tickets
    demo_tickets = get_demo_tickets()
    
    if demo_tickets:
        ticket_options = []
        ticket_map = {}
        
        for ticket in demo_tickets:
            if ticket.ticket_id == "T-EX1":
                label = get_text('demo_ticket_1')
            elif ticket.ticket_id == "T-EX2":
                label = get_text('demo_ticket_2')
            else:
                label = f"{ticket.ticket_id}: {ticket.title[:30]}..."
            
            ticket_options.append(label)
            ticket_map[label] = ticket
        
        # Add custom ticket option
        ticket_options.append(get_text('custom_ticket'))
        
        # Ticket selection
        selected_option = st.sidebar.selectbox(
            get_text('ticket_selection'),
            ticket_options,
            help=get_text('help_ticket_selection')
        )
        
        # Update configuration
        config = get_config()
        if selected_option != get_text('custom_ticket'):
            selected_ticket = ticket_map[selected_option]
            update_config({'selected_ticket_id': selected_ticket.ticket_id})
            
            # Store selected ticket in workflow state
            workflow_state = get_workflow_state()
            workflow_state['selected_ticket'] = selected_ticket
        else:
            # Custom ticket input
            st.sidebar.markdown("#### Eigenes Ticket")
            custom_title = st.sidebar.text_input("Titel")
            custom_body = st.sidebar.text_area("Beschreibung")
            custom_customer = st.sidebar.selectbox(
                "Kunde", 
                ["C-ACME", "C-BIOV"]
            )
            
            if custom_title and custom_body:
                # Create custom ticket object
                from app.core.models import Ticket, TicketPriority
                custom_ticket = Ticket(
                    ticket_id="CUSTOM",
                    customer_id=custom_customer,
                    title=custom_title,
                    body=custom_body,
                    related_skus=[],
                    status=TicketStatus.OPEN,
                    priority=TicketPriority.MEDIUM,
                    created_date="2024-11-02T13:00:00",
                    created_by="demo@example.com"
                )
                
                workflow_state = get_workflow_state()
                workflow_state['selected_ticket'] = custom_ticket


def render_ai_configuration():
    """Render AI model configuration"""
    st.sidebar.markdown("### 🤖 " + get_text('ai_configuration'))
    
    config = get_config()
    
    # Model selection
    model = st.sidebar.selectbox(
        get_text('model'),
        ["gpt-4", "gpt-3.5-turbo", "claude-3-sonnet", "claude-3-haiku"],
        index=0 if config['llm_model'] == 'gpt-4' else 0
    )
    
    # Temperature slider
    temperature = st.sidebar.slider(
        get_text('temperature'),
        min_value=0.0,
        max_value=1.0,
        value=config['temperature'],
        step=0.1,
        help=get_text('help_temperature')
    )
    
    # Debug mode toggle
    debug_mode = st.sidebar.toggle(
        get_text('debug_mode'),
        value=config['debug_mode'],
        help=get_text('help_debug')
    )
    
    # Update configuration
    update_config({
        'llm_model': model,
        'temperature': temperature,
        'debug_mode': debug_mode
    })


def render_minimal_controls():
    """Render minimal demo control buttons"""
    if st.sidebar.button(
        "🔄 " + get_text('reset_workflow'),
        help="Demo zurücksetzen und von vorne beginnen",
        width='stretch'
    ):
        reset_workflow()
        st.rerun()


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
            st.session_state.demo_data = {
                'crm': crm_data,
                'tickets': tickets,
                'manuals': manuals,
                'sops': sops
            }
        
        tickets = st.session_state.demo_data['tickets']
        return [t for t in tickets if t.status == TicketStatus.OPEN]
        
    except Exception as e:
        st.sidebar.error(f"Error loading tickets: {e}")
        return []
