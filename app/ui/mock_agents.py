"""
Mock agents for UI testing
"""

def mock_research_agent(ticket, crm_data, tickets, manuals):
    """Mock research agent that returns sample results"""
    return {
        'customer_summary': f'Kunde {ticket.customer_id} identifiziert als Premium-Kunde mit technischer Expertise.',
        'product_guess': ticket.related_skus[0] if ticket.related_skus else None,
        'findings': [
            {
                'type': 'crm',
                'source_id': ticket.customer_id,
                'section': 'Customer Profile',
                'quote': 'Premium-Kunde mit regelmäßigen Wartungsverträgen',
                'score': 0.95
            },
            {
                'type': 'manual',
                'source_id': 'GW-300',
                'section': 'Installation',
                'quote': 'Maximale Saughöhe: 1,5m für optimale Leistung',
                'score': 0.89
            }
        ],
        'open_questions': [
            'Ist eine Saughöhen-Reduzierung baulich möglich?',
            'Sollte eine Zulaufpumpe als Alternative vorgeschlagen werden?'
        ]
    }


def mock_planning_agent(ticket, research_results):
    """Mock planning agent that returns sample plan"""
    return {
        'difficulty': 'moderate',
        'steps': [
            {
                'id': 1,
                'owner': 'agent',
                'desc': 'Technische E-Mail-Antwort an Kunden erstellen'
            },
            {
                'id': 2,
                'owner': 'human',
                'desc': 'Kunden-E-Mail vor Versand prüfen'
            },
            {
                'id': 3,
                'owner': 'customer',
                'desc': 'Saughöhe auf maximal 1,5m reduzieren'
            }
        ],
        'briefing': 'Technische Lösung für Kavitationsproblem durch Saughöhen-Anpassung.'
    }


def mock_execution_agent(plan, research_results):
    """Mock execution agent that returns sample results"""
    return {
        'customer_email': {
            'subject': '[T-EX1] GW-300 - Technische Lösung für Förderleistung',
            'body': 'Sehr geehrter Herr Müller,\n\nvielen Dank für Ihre Anfrage...'
        },
        'internal_note': 'Kavitation durch zu hohe Saughöhe. Lösung: Reduzierung auf <1,5m.',
        'extra_findings': []
    }
