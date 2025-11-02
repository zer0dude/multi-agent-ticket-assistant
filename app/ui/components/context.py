"""
Context and demo overview component
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from app.core.data import load_all_data
from app.core.models import TicketStatus
from app.ui.utils.state import advance_to_stage
from app.ui.utils.german import get_text


def render_context_section():
    """Render the context and demo overview section"""
    
    st.markdown("## 📚 " + get_text('context_title'))
    
    # Load demo data
    demo_data = load_demo_data()
    if not demo_data:
        st.error("Fehler beim Laden der Demo-Daten")
        return
    
    # Main sections
    render_demo_overview()
    st.markdown("---")
    
    render_company_overview(demo_data)
    st.markdown("---")
    
    render_data_exploration(demo_data)
    st.markdown("---")
    
    render_start_demo_button()


def render_demo_overview():
    """Render demo explanation section"""
    st.markdown("### 🎯 " + get_text('demo_overview'))
    
    # First paragraph - Business context
    st.markdown(get_text('demo_intro_paragraph'))
    
    # Second paragraph - Technical details  
    st.markdown(get_text('demo_technical_paragraph'))


def render_company_overview(demo_data):
    """Render company and data overview"""
    st.markdown("### 🏭 " + get_text('company_overview'))
    
    # Expanded company description
    st.markdown("""
    **Pumpen GmbH** ist ein mittelständisches deutsches Unternehmen,
    das sich auf die Entwicklung und Produktion von Industriepumpen spezialisiert hat.
    """ + get_text('company_description_expanded'))
    
    # Products and manuals layout (70% products, 30% manual buttons)
    col1, col2 = st.columns([0.7, 0.3])
    
    with col1:
        st.markdown("#### 🔧 " + get_text('products_table'))
        render_products_table(demo_data['crm'])
    
    with col2:
        st.markdown("#### 📖 " + get_text('manual_buttons'))
        render_manual_buttons(demo_data['manuals'])
    
    # Customer description paragraph
    st.markdown(get_text('customer_description'))
    
    # Customer table with complete data
    st.markdown("#### 👥 " + get_text('customers_table'))
    render_enhanced_customers_table(demo_data['crm'])


def render_products_table(crm_data):
    """Render products as read-only table"""
    products_data = []
    
    for product in crm_data.products:
        products_data.append({
            'SKU': product.sku,
            'Name': product.name,
            'Typ': product.type,
            'Beschreibung': product.description
        })
    
    df_products = pd.DataFrame(products_data)
    st.dataframe(df_products, width='stretch', hide_index=True)


def render_manual_buttons(manuals):
    """Render manual buttons that open modals"""
    # Create buttons for each product manual
    if st.button("🔧 " + get_text('manual_kleinwasser'), width='stretch'):
        render_manual_modal(manuals, 'KW-100', get_text('manual_kleinwasser'))
    
    if st.button("💧 " + get_text('manual_grosswasser'), width='stretch'):
        render_manual_modal(manuals, 'GW-300', get_text('manual_grosswasser'))
    
    if st.button("🧪 " + get_text('manual_viskopro'), width='stretch'):
        render_manual_modal(manuals, 'VP-200', get_text('manual_viskopro'))


@st.dialog("Technisches Handbuch")
def render_manual_modal(manuals, product_sku, title):
    """Render manual content in modal"""
    st.markdown(f"## {title}")
    
    # Find and display manual content for this product
    manual_content = ""
    for manual in manuals:
        if manual.product_sku == product_sku:
            manual_content += f"### {manual.title}\n\n{manual.content}\n\n"
    
    if manual_content:
        st.markdown(manual_content)
    else:
        st.info(f"Handbuch für {product_sku} wird geladen...")
    
    if st.button("Schließen"):
        st.rerun()


def render_enhanced_customers_table(crm_data):
    """Render enhanced customers table with complete CRM data"""
    customers_data = []
    
    for customer in crm_data.customers:
        # Get purchased products
        purchased_skus = [p.sku for p in customer.purchases]
        
        customers_data.append({
            'ID': customer.id,
            'Name': customer.name,
            'Kontakt': customer.contact_person.name,
            'Position': customer.contact_person.title,
            'Support-Tier': customer.support_tier.value,
            'Kunde seit': customer.customer_since,
            'Produkte': ', '.join(purchased_skus),
            'Mitarbeiter': customer.company_info.employees
        })
    
    df_customers = pd.DataFrame(customers_data)
    st.dataframe(df_customers, width='stretch', hide_index=True)


def render_customers_table(crm_data):
    """Render customers as read-only table"""
    customers_data = []
    
    for customer in crm_data.customers:
        # Get purchased products
        purchased_skus = [p.sku for p in customer.purchases]
        
        customers_data.append({
            'ID': customer.id,
            'Name': customer.name,
            'Support': customer.support_tier.value,
            'Produkte': ', '.join(purchased_skus)
        })
    
    df_customers = pd.DataFrame(customers_data)
    st.dataframe(df_customers, width='stretch', hide_index=True)


def render_data_exploration(demo_data):
    """Render ticketing system overview section"""
    st.markdown("### 🎫 " + get_text('ticketing_system_title'))
    
    # First paragraph - Support system explanation
    st.markdown(get_text('support_system_description'))
    
    # Historical tickets section
    st.markdown("#### 🗂️ " + get_text('historical_tickets'))
    
    # Database explanation paragraph
    st.markdown(get_text('ticket_database_description'))
    
    # Full-width historical tickets table
    render_enhanced_historical_tickets_table(demo_data['tickets'])
    
    # Communication guidelines section
    st.markdown("#### 📄 " + get_text('communication_guidelines'))
    
    # Onboarding guidelines paragraph
    st.markdown(get_text('onboarding_guidelines_description'))
    
    # Communication guidelines button
    render_communication_guidelines_button(demo_data['sops'])


def render_enhanced_historical_tickets_table(tickets):
    """Render enhanced full-width historical tickets table with resolution details"""
    
    # Get closed tickets only
    closed_tickets = [t for t in tickets if t.status == TicketStatus.CLOSED]
    
    if closed_tickets:
        tickets_data = []
        
        for ticket in closed_tickets:
            tickets_data.append({
                'Ticket-ID': ticket.ticket_id,
                'Kunde': ticket.customer_id,
                'Produkt': ', '.join(ticket.related_skus),
                'Problem': ticket.title,
                'Erstellt': ticket.created_date,
                'Gelöst': ticket.resolved_date if ticket.resolved_date else 'N/A',
                'Lösung': ticket.resolution or 'Keine Lösung verfügbar',
                'Priorität': ticket.priority.value,
                'Status': '✅ Gelöst'
            })
        
        df_tickets = pd.DataFrame(tickets_data)
        st.dataframe(df_tickets, width='stretch', hide_index=True)
    else:
        st.info("Keine historischen Tickets gefunden")


def render_historical_tickets_table(tickets):
    """Render historical tickets as table"""
    st.markdown("#### 🗂️ " + get_text('historical_tickets'))
    
    # Get closed tickets only
    closed_tickets = [t for t in tickets if t.status == TicketStatus.CLOSED]
    
    if closed_tickets:
        tickets_data = []
        
        for ticket in closed_tickets:
            tickets_data.append({
                'Ticket': ticket.ticket_id,
                'Kunde': ticket.customer_id,
                'Produkt': ', '.join(ticket.related_skus),
                'Problem': ticket.title[:40] + '...' if len(ticket.title) > 40 else ticket.title,
                'Status': '✅ Gelöst'
            })
        
        df_tickets = pd.DataFrame(tickets_data)
        st.dataframe(df_tickets, width='stretch', hide_index=True)
    else:
        st.info("Keine historischen Tickets gefunden")


def render_communication_guidelines_button(sops):
    """Render communication guidelines button only"""
    if st.button("📄 " + get_text('view_guidelines'), width='stretch'):
        render_communication_modal(sops)


def render_communication_guidelines_section(sops):
    """Render communication guidelines with modal"""
    st.markdown("#### 📄 " + get_text('communication_guidelines'))
    
    st.markdown("""
    Die Demo verwendet authentische deutsche B2B-Kommunikationsstandards 
    für professionelle Kundenkorrespondenz.
    """)
    
    if st.button("📄 " + get_text('view_guidelines'), width='stretch'):
        render_communication_modal(sops)


@st.dialog("Kommunikationsrichtlinien - Pumpen GmbH")
def render_communication_modal(sops):
    """Render communication guidelines in modal"""
    
    # Display the SOPs content in a scrollable area
    st.markdown(sops)
    
    if st.button("Schließen"):
        st.rerun()


def render_manuals_overview(manuals):
    """Render technical manuals overview"""
    st.markdown("#### 📖 " + get_text('manuals_overview'))
    
    # Group manuals by product
    manual_counts = {}
    for manual in manuals:
        sku = manual.product_sku
        if sku not in manual_counts:
            manual_counts[sku] = 0
        manual_counts[sku] += 1
    
    manuals_data = []
    for sku, count in manual_counts.items():
        manuals_data.append({
            'Produkt': sku,
            'Abschnitte': count
        })
    
    df_manuals = pd.DataFrame(manuals_data)
    st.dataframe(df_manuals, width='stretch', hide_index=True)


def render_data_summary(demo_data):
    """Render summary statistics"""
    st.markdown("#### 📈 Daten-Übersicht")
    
    # Calculate stats
    total_tickets = len(demo_data['tickets'])
    open_tickets = len([t for t in demo_data['tickets'] if t.status == TicketStatus.OPEN])
    closed_tickets = len([t for t in demo_data['tickets'] if t.status == TicketStatus.CLOSED])
    
    st.metric("Gesamt-Tickets", total_tickets)
    st.metric("Offene Tickets", open_tickets, delta=f"+{open_tickets} für Demo")
    st.metric("Gelöste Tickets", closed_tickets, delta=f"{closed_tickets} als Wissensbasis")


def render_start_demo_button():
    """Render start demo button"""
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button(
            f"🚀 {get_text('start_demo')}",
            type="primary",
            width='stretch',
            help="Beginnen Sie mit der Ticket-Eingabe"
        ):
            advance_to_stage('ticket_input')
            st.rerun()


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
