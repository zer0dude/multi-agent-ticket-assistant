# Multi-Agent Ticketing Assistant

A portfolio demo showcasing intelligent technical support ticket handling through a multi-agent AI workflow for **Pumpen GmbH**, a fictional German pump manufacturer.

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run the demo:
```bash
streamlit run app/ui/main.py
```

## Project Structure

- `app/` - Main application code
  - `core/` - Data models and loading functions
  - `agents/` - AI agents for research, planning, execution, closing
  - `ui/` - Streamlit interface
- `data/` - Demo data files (German content)
  - `crm.json` - Company and customer data
  - `tickets.jsonl` - Support tickets and summaries
  - `manuals/` - Product documentation in German
  - `sops/` - Communication guidelines
- `tests/` - Unit tests

## Demo Workflow

1. **Research** - AI searches CRM, tickets, manuals
2. **Plan** - Generate action plan with human approval
3. **Execute** - Automated customer communication
4. **Close** - Create reusable summary

## German Localization

The demo interface and all customer-facing content is in German to authentically target German SMEs (small and medium enterprises).
