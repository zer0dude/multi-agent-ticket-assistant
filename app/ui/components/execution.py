"""
Execution results display component
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from app.ui.utils.state import get_workflow_state, advance_to_stage
from app.ui.utils.german import get_text


def render_execution_section():
    """Render the execution results section"""
    
    workflow_state = get_workflow_state()
    
    st.markdown("## 🚀 " + get_text('execution_results'))
    
    # Mock execution results for now
    render_mock_execution_results()
    
    # Final action button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button(
            f"✅ {get_text('mark_resolved')}",
            type="primary",
            width='stretch'
        ):
            advance_to_stage('closing')
            st.success("🎉 Ticket erfolgreich abgeschlossen!")
            st.balloons()


def render_mock_execution_results():
    """Render mock execution results for UI testing"""
    
    st.success("✅ Alle KI-Schritte erfolgreich ausgeführt")
    
    # Customer email draft
    st.markdown("### 📧 " + get_text('customer_email'))
    
    with st.expander("📧 E-Mail-Entwurf anzeigen", expanded=True):
        st.markdown("**Betreff:** [T-EX1] GW-300 - Technische Lösung für Förderleistung")
        
        st.markdown("""
        Sehr geehrter Herr Müller,
        
        vielen Dank für Ihre Anfrage bezüglich der GW-300 an Produktionslinie 3.
        
        **Problemanalyse:**
        Nach Ihrer Schilderung erreicht die Pumpe nur 0,8 bar statt der erwarteten 2,2 bar Ausgangsdruck, zusätzlich ist ein Pfeifgeräusch hörbar. Aufgrund der von Ihnen angegebenen Saughöhe von 2 Metern liegt hier sehr wahrscheinlich eine Kavitation vor.
        
        **Technische Ursache:**
        Die GW-300 ist für eine maximale Saughöhe von 1,5 Metern ausgelegt. Bei 2m Saughöhe entsteht unzureichender Eingangsdruck, was die Kavitation (Pfeifgeräusch) und die reduzierte Förderleistung verursacht.
        
        **Empfohlene Lösung:**
        1. **Sofortmaßnahme:** Saughöhe auf maximal 1,5 Meter reduzieren
        2. **Alternative:** Installation einer Zulaufpumpe, falls Höhenreduzierung nicht möglich
        3. **Kontrolle:** Nach der Anpassung Betrieb für 10 Minuten beobachten
        
        Die Pumpenkennlinie sollte sich dann normalisieren und die erwarteten 2,2 bar erreichen.
        
        **Nachfass-Terminierung:**
        Ich werde mich in 48 Stunden bei Ihnen melden, um zu überprüfen, ob das Problem behoben ist.
        
        Bei weiteren Fragen stehe ich Ihnen gerne zur Verfügung.
        
        Mit freundlichen Grüßen
        
        Technisches Support-Team  
        Pumpen GmbH  
        Tel: +49 89 555-8900
        """)
    
    # Internal documentation
    st.markdown("### 📝 " + get_text('internal_documentation'))
    
    with st.expander("📋 Interne Notiz anzeigen", expanded=True):
        st.code("""
TICKET: T-EX1 | KUNDE: Acme Maschinenbau GmbH | PRODUKT: GW-300

GRUNDURSACHE IDENTIFIZIERT:
• Saughöhe (2m) > max. Spezifikation (1,5m)
• Verursacht Kavitation und Druckverlust
• Bestätigt durch Handbuch-Referenz und Kundenhistorie

EVIDENZ:
• GW-300 Manual Sektion 4.2: "Max. Saughöhe 1,5m"
• Ähnliches Problem bei T-OLD1 (KW-100, gleicher Kunde)
• Technische Symptome konsistent mit Kavitation

EMPFOHLENE LÖSUNG:
• Primär: Saughöhen-Reduzierung auf <1,5m
• Sekundär: Zulaufpumpe als Alternative
• Nachfass in 48h geplant

ESKALATION: Nicht erforderlich (mittlere Schwierigkeit)
KUNDE-KONTEXT: Premium-Kunde, technikerfahren
        """)
    
    # Additional findings (optional)
    st.markdown("### 🔍 Zusätzliche Erkenntnisse")
    
    with st.expander("💡 Weitere relevante Informationen", expanded=False):
        st.info("""
        **Wartungsempfehlung:** Nach Saughöhen-Anpassung regelmäßige Kontrolle auf Kavitationsschäden empfohlen.
        
        **Präventivmaßnahme:** Kunde-Schulung zu Installationsrichtlinien für zukünftige GW-300 Installationen.
        """)


def render_execution_summary():
    """Render execution summary metrics"""
    
    st.markdown("---")
    st.markdown("### 📊 Ausführungs-Übersicht")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("KI-Schritte", "2", delta="Abgeschlossen")
    
    with col2:
        st.metric("Durchlaufzeit", "3 Min", delta="-2 Min vs. Standard")
    
    with col3:
        st.metric("Vertrauen", "87%", delta="Hoch")
    
    with col4:
        st.metric("Nachfass", "48h", delta="Geplant")
