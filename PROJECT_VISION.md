# Multi-Agent Ticketing Assistant - Project Vision

## Overview
A portfolio-quality demo showcasing intelligent technical support ticket handling through a multi-agent AI workflow. Built for **Pumpen GmbH**, a fictional German pump manufacturer, this system demonstrates modern AI capabilities with human oversight and transparent decision-making.

## Core Workflow: Research → Plan → Execute → Close
1. **Research**: AI agents perform structured searches across CRM, ticket history, and product manuals
2. **Plan**: Generate actionable plans with difficulty assessment and human approval step  
3. **Execute**: Automated execution of agent-assigned tasks (customer communication, documentation)
4. **Close**: Create reusable summaries that enhance future ticket resolution

## Business Context
- **Company**: Pumpen GmbH (German pump manufacturer)
- **Products**: 3 pumps (KW-100 Kleinwasser, GW-300 Großwasser, VP-200 ViskoPro)
- **Customers**: 2 fictional companies (Acme Maschinenbau, Biovisco Labs)
- **Scope**: Technical support tickets with realistic engineering problems

## Localization & Target Audience

### **German Language Requirement**
**Critical**: While development happens in English, **the demo interface and all customer-facing content must be in German** to authentically target German SMEs (small and medium enterprises).

**German Elements Include:**
- **UI Labels & Buttons**: All Streamlit interface text in German
- **Customer Communications**: Emails and responses in professional German business language
- **Product Documentation**: Technical manuals written in German technical terminology
- **Ticket Content**: Realistic German engineering problem descriptions
- **Company Context**: Authentic German business names, locations, and cultural context

**English Elements (Development Only):**
- Code comments and variable names
- Internal system logs and traces
- Development documentation

## Technical Architecture

### **No Framework Approach**
- Custom Python agent classes without heavy frameworks
- Direct LLM API integration (OpenAI/Anthropic/etc.)
- Simple JSON schema validation with Pydantic
- Focus on transparency and maintainability

### **Simplified Search Strategy**
Three-stage search process:
1. **CRM Search**: Agent-generated keywords for customer/product identification
2. **Ticket Search**: Historical ticket analysis using same keywords  
3. **Manual Search**: Product-specific documentation retrieval

### **Data Architecture**
- `data/crm.json`: Company, products, customer data
- `data/tickets.jsonl`: Append-only ticket storage with summaries
- `data/manuals/*.md`: Concise product manuals (one per pump)
- `data/sops/communication.md`: Tone and style guidelines

## User Interface Design

### **Streamlit Single-Page Application**
**Design Philosophy**: Portfolio-grade demonstration tool that visually narrates the AI workflow in authentic German business context

**Key UI Features**:
- **Progressive Workflow Visualization**: Clear stages with visual progress indicators
- **Transparent Agent Decision-Making**: Expandable research details with source citations
- **Interactive Human-in-the-Loop**: Feedback collection and plan approval workflow
- **Professional Polish**: German business context with realistic technical scenarios
- **Demo-Friendly Controls**: Model selection, temperature adjustment, example tickets
- **German Interface**: All UI elements, labels, and instructions in German

**Layout Structure**:
1. **Header**: Company branding and context metrics (German)
2. **Sidebar**: Demo configuration and AI model controls (German labels)
3. **Main Workflow**: Progressive panels for each stage (German)
4. **Research Panel**: Three-column display (CRM/Tickets/Manuals) with German findings
5. **Planning Panel**: Difficulty assessment, step breakdown, German feedback collection
6. **Execution Panel**: German customer communications and internal documentation
7. **Trace Panel**: Technical details for demonstration purposes (can remain English)

## Success Criteria
- Complete end-to-end processing of seeded example tickets
- Sourced research findings with clear provenance
- Human approval workflow with meaningful feedback integration
- Professional customer communications in authentic German business language
- Reusable ticket summaries that improve future resolution quality
- Portfolio-quality presentation suitable for German SME demonstrations

## Key Differentiators
- **Authentic German Business Context**: Real German company scenarios, not translations
- **Human-Centric Design**: Emphasizes human oversight rather than full automation
- **Provenance Tracking**: Every AI finding cites its source for transparency
- **Cultural Authenticity**: German SME scenario with authentic technical problems and business communication style
- **Knowledge Building**: Closed tickets become searchable institutional knowledge
- **Demonstration Ready**: Designed specifically for portfolio and technical interviews with German companies

## Implementation Approach
Focus on simplicity, transparency, and demonstration value over production scalability. Build a working system that clearly communicates the multi-agent concept while remaining technically sound and culturally authentic for the German SME market.

### **German Content Strategy**
- Use authentic German technical terminology for pump engineering
- Follow German business communication conventions (formal "Sie" form, proper business salutations)
- Include realistic German company names, locations, and business practices
- Ensure technical accuracy in German engineering context

## Development Plan

### **High-Level Development Phases**

#### **Phase 1: Foundation & Demo Data** 
**Goal**: Create the data foundation that everything else depends on
- Create demo data files (CRM, tickets, manuals, SOPs) in German
- Establish file structure and basic data models
- Test data loading and basic validation

**Why first**: Everything else depends on having realistic demo data to work with

#### **Phase 2: Core Data Infrastructure**
**Goal**: Build reliable data access layer
- Implement data loading/saving functions
- Create Pydantic models for type safety  
- Basic file I/O with error handling
- Simple unit tests for data operations

**Iterative note**: We'll revisit this as we discover data needs from agents

#### **Phase 3: Simple Search Engine**
**Goal**: Get the three-stage search working with basic functionality
- Implement CRM keyword search
- Implement ticket history search  
- Implement manual lookup by product
- Test with our demo data

**Why early**: Agents need search results to be useful

#### **Phase 4: Individual Agent Development (Iterative)**
**Goal**: Build agents one at a time, testing as we go
- **4a**: Research Agent (most complex - handles search integration)
- **4b**: Planner Agent (depends on research output)
- **4c**: Executor Agent (depends on plan format)
- **4d**: Closer Agent (depends on execution results)

**Iterative approach**: Build minimal version of each, then enhance

#### **Phase 5: Basic UI Development (Parallel)**
**Goal**: Create testable interface as we build agents
- **5a**: Basic Streamlit skeleton with German UI text
- **5b**: Add panels progressively as agents are ready
- **5c**: Manual testing and debugging interface
- **5d**: Polish and demo-ready styling

**Why parallel**: UI helps us test and debug agents during development

#### **Phase 6: Integration & Workflow**
**Goal**: Connect all pieces into working demo
- Agent orchestration and state management
- Error handling and user feedback
- End-to-end testing with both demo tickets
- Performance and reliability improvements

#### **Phase 7: Polish & Demo Readiness**
**Goal**: Make it portfolio-quality
- German language refinement and authenticity
- Visual polish and professional presentation
- Demo script and talking points
- Documentation and README

### **Iterative Development Strategy**

**Embrace Going Backwards**:
- Start each agent with minimal functionality, enhance later
- Expect to revise data models as agent needs become clear
- UI will evolve as we understand the user flow better
- Search functionality will be refined based on agent feedback

**Small Step Approach**:
- Each phase has clear deliverables we can test
- Every few hours, we should have something that partially works
- Prefer working but limited functionality over perfect but incomplete features

**Testing Strategy**:
- Manual testing at each step with demo data
- Simple unit tests for data operations
- UI testing by running workflows manually
- Keep one "golden path" working as we expand features
