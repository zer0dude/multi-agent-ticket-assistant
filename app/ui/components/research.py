"""
Research results display component
"""

import streamlit as st
import sys
from pathlib import Path
import time

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from app.ui.utils.state import get_workflow_state, advance_to_stage
from app.ui.utils.german import get_text
from app.core.research_agents import ResearchOrchestrator
from app.core.research_models import FullResearchResult


def render_research_section():
    """Render the research results section"""
    
    workflow_state = get_workflow_state()
    selected_ticket = workflow_state.get('selected_ticket')
    
    st.markdown("## 🔍 " + get_text('research_results'))
    
    if not selected_ticket:
        st.error("Kein Ticket ausgewählt")
        return
    
    # Check if research has been completed
    if 'research_results' not in st.session_state:
        # Run research process
        conduct_research(selected_ticket)
    else:
        # Display completed research results
        research_results = st.session_state.research_results
        render_research_results(research_results)
        
        # Progress to next stage button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(
                f"📝 {get_text('create_plan')}",
                type="primary",
                width='stretch'
            ):
                advance_to_stage('planning')
                st.rerun()


def conduct_research(ticket):
    """Conduct the 4-step research process with real-time updates"""
    
    # Initialize progress tracking
    progress_container = st.container()
    status_container = st.container()
    
    with progress_container:
        st.markdown("### 🔄 KI-Recherche läuft...")
        
        # Create progress bars for each step
        step1_progress = st.progress(0.0, text="Schritt 1: Kundenidentifikation...")
        step2_progress = st.progress(0.0, text="Schritt 2: Handbuch-Suche...")
        step3_progress = st.progress(0.0, text="Schritt 3: Ähnliche Tickets...")
        step4_progress = st.progress(0.0, text="Schritt 4: Recherche-Zusammenfassung...")
        
        status_text = st.empty()
    
    try:
        # Initialize research orchestrator
        with status_container:
            with st.spinner("Initialisiere KI-Agenten..."):
                research_orchestrator = ResearchOrchestrator()
            
        # Step 1: Customer Identification
        status_text.text("🔍 Schritt 1: Suche Kunde in CRM-System...")
        step1_progress.progress(0.5, text="Schritt 1: Fuzzy-Suche läuft...")
        
        customer_result = research_orchestrator._identify_customer(ticket)
        step1_progress.progress(1.0, text="✅ Schritt 1: Kundenidentifikation abgeschlossen")
        time.sleep(0.5)
        
        # Step 2: Manual Search
        status_text.text("📖 Schritt 2: Durchsuche technische Handbücher...")
        step2_progress.progress(0.3, text="Schritt 2: Handbuch-Analyse mit KI...")
        
        manual_results = research_orchestrator._search_manuals(ticket)
        step2_progress.progress(1.0, text="✅ Schritt 2: Handbuch-Suche abgeschlossen")
        time.sleep(0.5)
        
        # Step 3: Ticket Similarity
        status_text.text("🎯 Schritt 3: Suche ähnliche Tickets...")
        step3_progress.progress(0.4, text="Schritt 3: Erstelle Embeddings...")
        
        similarity_result = research_orchestrator._find_similar_tickets(ticket)
        step3_progress.progress(1.0, text="✅ Schritt 3: Ähnlichkeits-Suche abgeschlossen")
        time.sleep(0.5)
        
        # Step 4: Research Summary
        status_text.text("📊 Schritt 4: Erstelle Recherche-Zusammenfassung...")
        step4_progress.progress(0.6, text="Schritt 4: KI-Analyse...")
        
        research_summary = research_orchestrator._generate_research_summary(
            ticket, customer_result, manual_results, similarity_result
        )
        step4_progress.progress(1.0, text="✅ Schritt 4: Zusammenfassung erstellt")
        
        # Create full research result
        research_results = FullResearchResult(
            customer_identification=customer_result,
            manual_search=manual_results,
            ticket_similarity=similarity_result,
            research_summary=research_summary,
            processing_time_seconds=time.time(),
            errors_encountered=[]
        )
        
        # Store results in session state
        st.session_state.research_results = research_results
        
        # Clear progress indicators and show results
        progress_container.empty()
        status_container.empty()
        
        st.success("✅ Recherche erfolgreich abgeschlossen!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Fehler während der Recherche: {str(e)}")
        st.info("Verwende Fallback-Ergebnisse für Demo-Zwecke")
        
        # Fallback to mock results if real research fails
        render_mock_research_results()


def render_research_results(research_results: FullResearchResult):
    """Render the completed research results"""
    
    # Overall progress indicator
    st.progress(1.0, text="✅ Recherche abgeschlossen")
    
    # Three column layout for results
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_customer_results(research_results.customer_identification)
    
    with col2:
        render_manual_results(research_results.manual_search)
    
    with col3:
        render_similarity_results(research_results.ticket_similarity)
    
    # Research summary
    st.markdown("---")
    render_research_summary(research_results.research_summary)
    
    # Show processing time and errors if any
    if research_results.processing_time_seconds:
        st.caption(f"Verarbeitungszeit: {research_results.processing_time_seconds:.1f} Sekunden")
    
    if research_results.errors_encountered:
        with st.expander("⚠️ Warnungen", expanded=False):
            for error in research_results.errors_encountered:
                st.warning(error)


def render_customer_results(customer_result):
    """Render customer identification results"""
    st.markdown("### 👥 " + get_text('crm_data'))
    
    if customer_result.customer_id:
        st.success(get_text('customer_identified'))
        
        with st.expander("🔍 Details anzeigen", expanded=True):
            st.markdown(f"**Kunde:** {customer_result.customer_name}")
            st.markdown(f"**Vertrauen:** {customer_result.confidence_score:.1%}")
            st.markdown(f"**Grund:** {customer_result.match_reason}")
            
            if customer_result.relevant_data:
                data = customer_result.relevant_data
                st.markdown(f"**Support-Tier:** {data.get('support_tier', 'Unknown')}")
                
                if 'purchased_products' in data:
                    products = [p['sku'] for p in data['purchased_products']]
                    st.markdown(f"**Produkte:** {', '.join(products)}")
                
                if 'contact_person' in data:
                    contact = data['contact_person']
                    st.markdown(f"**Kontakt:** {contact.get('name', '')} ({contact.get('email', '')})")
    else:
        st.warning("Kunde nicht identifiziert")
        st.caption(customer_result.match_reason)


def render_manual_results(manual_results):
    """Render manual search results"""
    st.markdown("### 📖 " + get_text('manuals'))
    
    total_sections = sum(len(result.relevant_sections) for result in manual_results)
    
    if total_sections > 0:
        st.info(f"{total_sections} {get_text('sections')} gefunden")
        
        with st.expander("📖 Relevante Abschnitte", expanded=True):
            for manual_result in manual_results:
                if manual_result.relevant_sections:
                    st.markdown(f"**{manual_result.product_sku} Manual:**")
                    for section in manual_result.relevant_sections:
                        st.markdown(f"**{section.section_title}** ({section.relevance_score:.1%})")
                        st.markdown(f"> {section.content_excerpt[:150]}...")
                        st.caption(section.relevance_reason)
                        st.markdown("---")
    else:
        st.warning("Keine relevanten Abschnitte gefunden")
        for result in manual_results:
            st.caption(f"{result.product_sku}: {result.summary}")


def render_similarity_results(similarity_result):
    """Render ticket similarity results"""
    st.markdown("### 📋 " + get_text('previous_tickets'))
    
    if similarity_result.similar_tickets_found:
        count = len(similarity_result.similar_tickets)
        st.warning(f"{count} {get_text('similar')} Ticket{'s' if count > 1 else ''}")
        
        for i, similar_ticket in enumerate(similarity_result.similar_tickets):
            with st.expander(f"🗂️ {similar_ticket.ticket_id}: {similar_ticket.title[:30]}...", expanded=i == 0):
                st.markdown(f"**Ähnlichkeit:** {similar_ticket.similarity_score:.1%}")
                st.markdown(f"**Lösung:** {similar_ticket.resolution_summary}")
                st.markdown(f"**Erkenntnisse:** {similar_ticket.key_learnings}")
    else:
        st.info("Keine ähnlichen Tickets gefunden")
        st.caption(similarity_result.search_summary)


def render_research_summary(research_summary):
    """Render the comprehensive research summary with ticket context"""
    
    # Get current ticket for context display
    workflow_state = get_workflow_state()
    selected_ticket = workflow_state.get('selected_ticket')
    
    # Ticket Context Section
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
    
    # Research Findings Section
    st.markdown("### 🎯 Recherche-Ergebnisse")
    
    # Customer status
    st.markdown("**👥 Kundenstatus:**")
    st.markdown(research_summary.customer_status)
    
    # Technical findings with manual modal support
    technical_col1, technical_col2 = st.columns([4, 1])
    with technical_col1:
        st.markdown("**🔧 Technische Erkenntnisse:**")
        st.markdown(research_summary.technical_findings)
    
    with technical_col2:
        # Show handbook button for each product in ticket
        if selected_ticket and hasattr(selected_ticket, 'related_skus'):
            # Load complete manuals
            complete_manuals = get_complete_manuals_for_research()
            
            for sku in selected_ticket.related_skus:
                if st.button(f"📖 Handbuch {sku}", key=f"handbook_{sku}"):
                    render_complete_handbook_modal(
                        complete_manuals, 
                        sku, 
                        f"{sku} Handbuch"
                    )
    
    # Historical context
    st.markdown("**📊 Historischer Kontext:**")
    st.markdown(research_summary.historical_context)
    
    # Initial cause assessment (softened language)
    if hasattr(research_summary, 'initial_cause_assessment') and research_summary.initial_cause_assessment:
        st.markdown("**🎯 Erste Ursacheneinschätzung:**")
        st.info(research_summary.initial_cause_assessment)
    elif hasattr(research_summary, 'probable_root_cause') and research_summary.probable_root_cause:
        # Fallback for old model structure
        st.markdown("**🎯 Erste Ursacheneinschätzung:**")
        st.info(research_summary.probable_root_cause)
    
    st.markdown("---")
    
    # Assessment Section (moved to bottom with explanations)
    st.markdown("### 📊 Bewertung")
    
    assess_col1, assess_col2 = st.columns(2)
    
    with assess_col1:
        # Confidence assessment with direct explanation display
        confidence_colors = {
            "high": "🟢",
            "medium": "🟡", 
            "low": "🔴"
        }
        confidence_color = confidence_colors.get(research_summary.confidence_assessment.value, "⚪")
        
        st.markdown("**Einschätzungskonfidenz:**")
        st.markdown(f"{confidence_color} **{research_summary.confidence_assessment.value.title()}**")
        
        # Show explanation directly as paragraph
        if hasattr(research_summary, 'confidence_explanation'):
            st.markdown(research_summary.confidence_explanation)
    
    with assess_col2:
        # Urgency assessment with direct explanation display
        urgency_colors = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🟠", 
            "critical": "🔴"
        }
        urgency_color = urgency_colors.get(research_summary.urgency_level, "⚪")
        
        st.markdown("**Dringlichkeit:**")
        st.markdown(f"{urgency_color} **{research_summary.urgency_level.title()}**")
        
        # Show explanation directly as paragraph
        if hasattr(research_summary, 'urgency_explanation'):
            st.markdown(research_summary.urgency_explanation)


def get_complete_manuals_for_research():
    """Load complete manuals - same pattern as context.py"""
    from app.core.data import load_all_data
    _, _, manuals, _ = load_all_data()
    return manuals


@st.dialog("Technisches Handbuch")
def render_complete_handbook_modal(manuals, product_sku, title):
    """Render complete handbook content in modal - identical to context.py pattern"""
    st.markdown(f"## {title}")
    
    # Find and display ALL manual content for this product
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


def render_manual_modal(relevant_manuals):
    """Render manual content in a modal dialog (DEPRECATED - kept for compatibility)"""
    st.markdown("### 📖 Relevante Handbuch-Abschnitte")
    
    if not relevant_manuals:
        st.info("Keine Handbücher zur Anzeige verfügbar")
        return
    
    # Create tabs for multiple manuals if needed
    if len(relevant_manuals) > 1:
        manual_tabs = st.tabs([f"{manual.get('sku', 'Unknown')} Manual" for manual in relevant_manuals])
        for i, manual_data in enumerate(relevant_manuals):
            with manual_tabs[i]:
                _render_single_manual(manual_data)
    else:
        _render_single_manual(relevant_manuals[0])


def _render_single_manual(manual_data):
    """Render a single manual's content (DEPRECATED - kept for compatibility)"""
    sku = manual_data.get('sku', 'Unknown')
    sections = manual_data.get('sections', [])
    
    st.markdown(f"**Produkt:** {sku}")
    
    if not sections:
        st.warning("Keine relevanten Abschnitte verfügbar")
        return
    
    for section in sections:
        with st.expander(f"📄 {section.get('title', 'Unknown Section')}", expanded=True):
            st.markdown(f"**Relevanz:** {section.get('relevance_score', 0):.1%}")
            st.markdown(f"**Grund:** {section.get('relevance_reason', 'No reason provided')}")
            st.markdown("**Inhalt:**")
            st.markdown(f"> {section.get('content', 'No content available')}")


def render_mock_research_results():
    """Render mock research results for UI testing"""
    
    # Progress indicator
    progress_bar = st.progress(1.0)
    st.success("✅ Recherche abgeschlossen")
    
    # Three column layout for search results
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 👥 " + get_text('crm_data'))
        st.success(get_text('customer_identified'))
        
        with st.expander("🔍 Details anzeigen", expanded=True):
            st.markdown("""
            **Kunde:** Acme Maschinenbau GmbH  
            **Vertrauen:** 95%  
            **Produkte:** KW-100 ✅, GW-300 ✅  
            **Support-Historie:** 2 frühere Tickets  
            """)
    
    with col2:
        st.markdown("### 📖 " + get_text('manuals'))
        st.info(f"4 {get_text('sections')} gefunden")
        
        with st.expander("📖 Relevante Abschnitte", expanded=True):
            st.markdown("""
            **GW-300 Manual - Installation:**
            > Maximale Saughöhe: 1,5m für optimale Leistung
            
            **GW-300 Manual - Troubleshooting:**  
            > Pfeifgeräusch deutet auf Kavitation durch unzureichenden Eingangsdruck hin
            """)
    
    with col3:
        st.markdown("### 📋 " + get_text('previous_tickets'))
        st.warning(f"1 {get_text('similar')} Ticket")
        
        with st.expander("🗂️ T-OLD1: Ähnliches Problem", expanded=True):
            st.markdown("""
            **Vorheriges Ticket:** T-OLD1 (Gelöst)  
            **Problem:** KW-100 Anlaufprobleme  
            **Lösung:** Saughöhe-Anpassung  
            **Relevanz:** 78% (Pumpen-Positionierung)
            """)
    
    # Research summary
    st.markdown("---")
    summary_col1, summary_col2 = st.columns([3, 1])
    
    with summary_col1:
        st.markdown("### 🎯 Recherche-Zusammenfassung")
        st.success("""
        **Wahrscheinliche Grundursache identifiziert:** Saughöhe (2m) überschreitet GW-300 Spezifikation (1,5m max), verursacht Kavitation und reduzierten Ausgangsdruck. Kunde hat Verlauf ähnlicher Positionierungsprobleme.
        """)
    
    with summary_col2:
        st.metric("Vertrauen", "87%", delta="Hoch")
    
    # Open questions
    st.markdown("### ❓ " + get_text('open_questions'))
    questions = [
        "Ist eine Saughöhen-Reduzierung baulich möglich?",
        "Sollte eine Zulaufpumpe als Alternative vorgeschlagen werden?",
        "Sind weitere GW-300 Einheiten betroffen?"
    ]
    
    for i, question in enumerate(questions, 1):
        st.markdown(f"{i}. {question}")
