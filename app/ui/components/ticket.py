"""
Ticket input component
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from app.core.data import load_all_data
from app.core.models import Ticket, TicketStatus, TicketPriority
from app.ui.utils.state import get_workflow_state, advance_to_stage, set_selected_ticket
from app.ui.utils.german import get_text


def render_ticket_section():
    """Render the ticket input section"""
    
    st.markdown("## 📋 " + get_text('stage_ticket_input'))
    
    # Brief explanation paragraph
    st.markdown(get_text('ticket_simulation_description'))
    
    # Unified form with example selection
    render_unified_ticket_form()


def render_unified_ticket_form():
    """Render unified ticket form with example selection"""
    
    demo_data = load_demo_data()
    if not demo_data:
        return
    
    # Example ticket selection above the form
    st.markdown("### 🎯 " + get_text('use_example_ticket'))
    
    # Get open demo tickets
    open_tickets = [t for t in demo_data['tickets'] if t.status == TicketStatus.OPEN]
    
    # Create options
    example_options = ['-- Eigenes Ticket schreiben --']
    ticket_map = {}
    
    if open_tickets:
        for ticket in open_tickets:
            if ticket.ticket_id == "T-EX1":
                label = get_text('demo_ticket_1')
            elif ticket.ticket_id == "T-EX2":
                label = get_text('demo_ticket_2')
            else:
                label = f"{ticket.ticket_id}: {ticket.title[:30]}..."
            
            example_options.append(label)
            ticket_map[label] = ticket
    
    selected_example = st.selectbox(
        "Beispiel auswählen oder eigenes Ticket schreiben",
        example_options,
        help="Wählen Sie ein vorkonfiguriertes Demo-Ticket aus oder schreiben Sie ein eigenes",
        key="example_ticket_select"
    )
    
    # Get selected ticket for auto-population
    selected_ticket = None
    if selected_example != '-- Eigenes Ticket schreiben --' and selected_example in ticket_map:
        selected_ticket = ticket_map[selected_example]
    
    st.markdown("### ✏️ " + get_text('manual_ticket_input'))
    
    with st.form("ticket_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Title input (auto-populated if example selected)
            title_value = selected_ticket.title if selected_ticket else ""
            title = st.text_input(
                get_text('ticket_title') + " *",
                value=title_value,
                placeholder="z.B. Pumpe GW-300 läuft nicht an",
                help="Kurze Beschreibung des Problems"
            )
            
            # Company name (auto-populated if example selected)
            company_value = ""
            if selected_ticket:
                company_value = get_company_name_from_customer_id(selected_ticket.customer_id, demo_data['crm'])
            
            company_name = st.text_input(
                get_text('company_name') + " *",
                value=company_value,
                placeholder="z.B. Musterfirma GmbH",
                help="Name des Unternehmens"
            )
            
            # Contact person name (auto-populated if example selected)
            contact_name_value = ""
            if selected_ticket:
                contact_name_value = get_contact_name_from_customer_id(selected_ticket.customer_id, demo_data['crm'])
            
            contact_name = st.text_input(
                get_text('contact_person_name') + " *",
                value=contact_name_value,
                placeholder="z.B. Max Mustermann",
                help="Name der Kontaktperson"
            )
            
            # Priority selection (auto-populated if example selected)
            priority_options = ['medium', 'low', 'high', 'critical']
            priority_index = 0
            if selected_ticket:
                try:
                    priority_index = priority_options.index(selected_ticket.priority.value)
                except ValueError:
                    priority_index = 0
            
            priority = st.selectbox(
                get_text('select_priority'),
                options=priority_options,
                format_func=lambda x: get_text(f'priority_{x}'),
                index=priority_index
            )
        
        with col2:
            # Contact email (auto-populated if example selected)
            contact_email_value = ""
            if selected_ticket:
                contact_email_value = get_contact_email_from_customer_id(selected_ticket.customer_id, demo_data['crm'])
            
            contact_email = st.text_input(
                get_text('contact_email') + " *",
                value=contact_email_value,
                placeholder="z.B. max.mustermann@musterfirma.de",
                help="E-Mail-Adresse der Kontaktperson"
            )
            
            # Description input (auto-populated if example selected)
            description_value = selected_ticket.body if selected_ticket else ""
            description = st.text_area(
                get_text('ticket_description') + " *",
                value=description_value,
                placeholder="Detaillierte Beschreibung des Problems...",
                height=100,
                help="Ausführliche Problembeschreibung"
            )
            
            # Product selection with "Sonstiges" option (auto-populated if example selected)
            products = demo_data['crm'].products
            product_options = [f"{p.sku} - {p.name}" for p in products]
            product_options.append("Sonstiges")
            
            default_products = []
            if selected_ticket:
                for sku in selected_ticket.related_skus:
                    for option in product_options:
                        if option.startswith(sku):
                            default_products.append(option)
                            break
            
            selected_products = st.multiselect(
                get_text('select_products'),
                product_options,
                default=default_products,
                help="Betroffene Produkte auswählen (einschließlich 'Sonstiges' für unbekannte Produkte)"
            )
        
        # Form submission
        submitted = st.form_submit_button(
            f"🔍 {get_text('start_research')}",
            type="primary",
            width='stretch'
        )
        
        if submitted:
            # Validate required fields
            if not title or not description or not company_name or not contact_name or not contact_email:
                st.error(get_text('form_validation_error'))
            # Validate email format
            elif not is_valid_email(contact_email):
                st.error(get_text('email_validation_error'))
            else:
                # Create ticket from form data
                product_skus = []
                for p in selected_products:
                    if p == "Sonstiges":
                        product_skus.append("Sonstiges")
                    else:
                        product_skus.append(p.split(' - ')[0])
                
                ticket = create_ticket_from_form(
                    title, description, company_name, contact_name, contact_email, priority, product_skus
                )
                
                set_selected_ticket(ticket)
                advance_to_stage('research')
                st.rerun()


def render_ticket_display(ticket):
    """Render ticket information display"""
    
    # Get customer information
    demo_data = st.session_state.get('demo_data', {})
    crm_data = demo_data.get('crm')
    customer = None
    
    if crm_data:
        for cust in crm_data.customers:
            if cust.id == ticket.customer_id:
                customer = cust
                break
    
    # Main ticket info in columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Ticket details
        st.info(f"""
        **{get_text('ticket_id')}:** {ticket.ticket_id}
        
        **{get_text('customer')}:** {customer.name if customer else ticket.customer_id}
        
        **{get_text('priority')}:** {get_priority_badge(ticket.priority.value)}
        
        **Erstellt:** {format_datetime(ticket.created_date)}
        
        **{get_text('description')}:**
        
        {ticket.body}
        """)
        
        # Related products
        if ticket.related_skus:
            st.markdown("**Betroffene Produkte:**")
            for sku in ticket.related_skus:
                product_info = get_product_info(sku)
                st.markdown(f"- **{sku}**: {product_info}")
    
    with col2:
        # Customer context card
        if customer:
            render_customer_context(customer)
        
        # Ticket metadata
        render_ticket_metadata(ticket)


def render_customer_context(customer):
    """Render customer context information"""
    
    st.markdown("**👥 Kunde**")
    
    support_tier_color = "🟢" if customer.support_tier.value == "Premium" else "🟡"
    
    st.markdown(f"""
    {support_tier_color} **{customer.name}**
    
    📧 {customer.contact_person.email}
    
    📞 {customer.contact_person.phone}
    
    🏷️ {customer.support_tier.value}-Kunde
    
    📅 Kunde seit {customer.customer_since}
    
    **Produkte:**
    """)
    
    for purchase in customer.purchases:
        st.markdown(f"• {purchase.sku} ({purchase.installation_location})")
    
    if customer.notes:
        with st.expander("📝 Notizen"):
            st.markdown(customer.notes)


def render_ticket_metadata(ticket):
    """Render additional ticket metadata"""
    
    st.markdown("**📊 Ticket-Details**")
    
    # Status badge
    status_color = {
        'open': '🔴',
        'in_progress': '🟡',
        'closed': '🟢'
    }.get(ticket.status.value, '⚪')
    
    st.markdown(f"""
    {status_color} {get_status_text(ticket.status.value)}
    
    📧 {ticket.created_by}
    """)
    
    # Show resolution if closed
    if hasattr(ticket, 'resolution') and ticket.resolution:
        with st.expander("✅ Lösung"):
            st.markdown(ticket.resolution)


def get_priority_badge(priority: str) -> str:
    """Get priority badge with appropriate color"""
    priority_badges = {
        'low': '🟢 Niedrig',
        'medium': '🟡 Mittel',
        'high': '🟠 Hoch',
        'critical': '🔴 Kritisch'
    }
    return priority_badges.get(priority.lower(), f"⚪ {priority}")


def get_product_info(sku: str) -> str:
    """Get product information by SKU"""
    demo_data = st.session_state.get('demo_data', {})
    crm_data = demo_data.get('crm')
    
    if crm_data:
        for product in crm_data.products:
            if product.sku == sku:
                return f"{product.name} ({product.type})"
    
    return "Unbekanntes Produkt"


def format_datetime(datetime_str: str) -> str:
    """Format datetime string for display"""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return dt.strftime('%d.%m.%Y %H:%M')
    except:
        return datetime_str


def get_company_name_from_customer_id(customer_id: str, crm_data) -> str:
    """Get company name from customer ID"""
    for customer in crm_data.customers:
        if customer.id == customer_id:
            return customer.name
    return ""


def get_contact_name_from_customer_id(customer_id: str, crm_data) -> str:
    """Get contact person name from customer ID"""
    for customer in crm_data.customers:
        if customer.id == customer_id:
            return customer.contact_person.name
    return ""


def get_contact_email_from_customer_id(customer_id: str, crm_data) -> str:
    """Get contact email from customer ID"""
    for customer in crm_data.customers:
        if customer.id == customer_id:
            return customer.contact_person.email
    return ""


def is_valid_email(email: str) -> bool:
    """Simple email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def create_ticket_from_form(title: str, description: str, company_name: str, contact_name: str, contact_email: str, priority: str, product_skus: list) -> Ticket:
    """Create a ticket object from form data"""
    ticket = Ticket(
        ticket_id="MANUAL",
        customer_id=company_name,  # Using company name as customer ID for manual tickets
        title=title,
        body=description,
        related_skus=product_skus,
        status=TicketStatus.OPEN,
        priority=TicketPriority(priority),
        created_date=datetime.now().isoformat(),
        created_by=contact_email
    )
    return ticket


def load_demo_data():
    """Load demo data with error handling"""
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
        return st.session_state.demo_data
    except Exception as e:
        st.error(f"Fehler beim Laden der Demo-Daten: {e}")
        return None


def get_status_text(status: str) -> str:
    """Get German status text"""
    status_map = {
        'open': get_text('status_open'),
        'closed': get_text('status_closed'),
        'in_progress': get_text('status_in_progress')
    }
    return status_map.get(status.lower(), status)
