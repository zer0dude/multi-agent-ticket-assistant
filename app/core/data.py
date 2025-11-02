"""
Data loading and persistence functions for the Multi-Agent Ticketing Assistant
"""

import json
import jsonlines
from pathlib import Path
from typing import List, Dict, Any

from .models import (
    CRMData, Ticket, ManualSection, TicketSummary,
    TicketStatus, TicketPriority
)


class DataLoader:
    """Handles loading and saving of all demo data"""
    
    def __init__(self, data_path: str = "data"):
        self.data_path = Path(data_path)
        
    def load_crm_data(self) -> CRMData:
        """Load and validate CRM data from JSON file"""
        crm_file = self.data_path / "crm.json"
        
        try:
            with open(crm_file, 'r', encoding='utf-8') as f:
                crm_raw = json.load(f)
            return CRMData(**crm_raw)
        except Exception as e:
            raise ValueError(f"Error loading CRM data: {e}")
    
    def load_tickets(self) -> List[Ticket]:
        """Load and validate tickets from JSONL file"""
        tickets_file = self.data_path / "tickets.jsonl"
        tickets = []
        
        try:
            with jsonlines.open(tickets_file, 'r') as reader:
                for line in reader:
                    # Convert string status/priority to enums
                    if 'status' in line:
                        line['status'] = TicketStatus(line['status'])
                    if 'priority' in line:
                        line['priority'] = TicketPriority(line['priority'])
                    
                    ticket = Ticket(**line)
                    tickets.append(ticket)
            return tickets
        except Exception as e:
            raise ValueError(f"Error loading tickets: {e}")
    
    def load_manuals(self) -> List[ManualSection]:
        """Load and parse manual markdown files"""
        manuals_dir = self.data_path / "manuals"
        manual_sections = []
        
        # Mapping of manual files to product SKUs
        manual_mapping = {
            "kleinwasser.md": "KW-100",
            "grosswasser.md": "GW-300", 
            "viskopro.md": "VP-200"
        }
        
        try:
            for manual_file, product_sku in manual_mapping.items():
                file_path = manuals_dir / manual_file
                
                if not file_path.exists():
                    continue
                    
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse markdown sections
                sections = self._parse_manual_sections(content, product_sku, manual_file)
                manual_sections.extend(sections)
                
            return manual_sections
        except Exception as e:
            raise ValueError(f"Error loading manuals: {e}")
    
    def _parse_manual_sections(self, content: str, product_sku: str, manual_file: str) -> List[ManualSection]:
        """Parse markdown content into sections"""
        sections = []
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            if line.startswith('##'):  # H2 header - new section
                # Save previous section if exists
                if current_section and current_content:
                    sections.append(ManualSection(
                        title=current_section,
                        content='\n'.join(current_content).strip(),
                        product_sku=product_sku,
                        manual_file=manual_file
                    ))
                
                # Start new section
                current_section = line.strip('# ').strip()
                current_content = []
                
            elif line.startswith('#') and not line.startswith('##'):  # H1 header - document title
                continue
            else:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections.append(ManualSection(
                title=current_section,
                content='\n'.join(current_content).strip(),
                product_sku=product_sku,
                manual_file=manual_file
            ))
        
        return sections
    
    def load_communication_sops(self) -> str:
        """Load communication SOPs as plain text"""
        sops_file = self.data_path / "sops" / "communication.md"
        
        try:
            with open(sops_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Error loading communication SOPs: {e}")
    
    def save_ticket(self, ticket: Ticket) -> None:
        """Save or update a ticket in the JSONL file"""
        tickets_file = self.data_path / "tickets.jsonl"
        
        # Load all existing tickets
        existing_tickets = []
        if tickets_file.exists():
            existing_tickets = self.load_tickets()
        
        # Update existing ticket or add new one
        ticket_updated = False
        for i, existing_ticket in enumerate(existing_tickets):
            if existing_ticket.ticket_id == ticket.ticket_id:
                existing_tickets[i] = ticket
                ticket_updated = True
                break
        
        if not ticket_updated:
            existing_tickets.append(ticket)
        
        # Write all tickets back to file
        try:
            with jsonlines.open(tickets_file, 'w') as writer:
                for t in existing_tickets:
                    # Convert to dict and handle enums
                    ticket_dict = t.model_dump()
                    ticket_dict['status'] = ticket_dict['status'].value if hasattr(ticket_dict['status'], 'value') else ticket_dict['status']
                    ticket_dict['priority'] = ticket_dict['priority'].value if hasattr(ticket_dict['priority'], 'value') else ticket_dict['priority']
                    writer.write(ticket_dict)
        except Exception as e:
            raise ValueError(f"Error saving ticket: {e}")
    
    def get_customer_by_id(self, customer_id: str, crm_data: CRMData):
        """Get customer by ID from CRM data"""
        for customer in crm_data.customers:
            if customer.id == customer_id:
                return customer
        return None
    
    def get_product_by_sku(self, sku: str, crm_data: CRMData):
        """Get product by SKU from CRM data"""
        for product in crm_data.products:
            if product.sku == sku:
                return product
        return None
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """Validate that all data cross-references are consistent"""
        issues = []
        warnings = []
        
        try:
            # Load all data
            crm_data = self.load_crm_data()
            tickets = self.load_tickets()
            manuals = self.load_manuals()
            sops = self.load_communication_sops()
            
            # Validate ticket references
            for ticket in tickets:
                # Check customer ID exists
                customer = self.get_customer_by_id(ticket.customer_id, crm_data)
                if not customer:
                    issues.append(f"Ticket {ticket.ticket_id} references unknown customer {ticket.customer_id}")
                
                # Check product SKUs exist
                for sku in ticket.related_skus:
                    product = self.get_product_by_sku(sku, crm_data)
                    if not product:
                        issues.append(f"Ticket {ticket.ticket_id} references unknown product {sku}")
            
            # Validate customer purchases reference valid products
            for customer in crm_data.customers:
                for purchase in customer.purchases:
                    product = self.get_product_by_sku(purchase.sku, crm_data)
                    if not product:
                        issues.append(f"Customer {customer.id} purchased unknown product {purchase.sku}")
            
            # Check manual coverage
            product_skus = {p.sku for p in crm_data.products}
            manual_skus = {m.product_sku for m in manuals}
            missing_manuals = product_skus - manual_skus
            if missing_manuals:
                warnings.append(f"Missing manuals for products: {missing_manuals}")
            
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "warnings": warnings,
                "data_summary": {
                    "crm_customers": len(crm_data.customers),
                    "crm_products": len(crm_data.products),
                    "tickets_total": len(tickets),
                    "tickets_open": len([t for t in tickets if t.status == TicketStatus.OPEN]),
                    "tickets_closed": len([t for t in tickets if t.status == TicketStatus.CLOSED]),
                    "manual_sections": len(manuals),
                    "sops_length": len(sops)
                }
            }
            
        except Exception as e:
            return {
                "valid": False,
                "issues": [f"Data loading error: {e}"],
                "warnings": [],
                "data_summary": {}
            }


# Convenience functions for easy access
def load_all_data(data_path: str = "data"):
    """Load all data and return as tuple"""
    loader = DataLoader(data_path)
    crm_data = loader.load_crm_data()
    tickets = loader.load_tickets()
    manuals = loader.load_manuals()
    sops = loader.load_communication_sops()
    return crm_data, tickets, manuals, sops


def validate_demo_data(data_path: str = "data"):
    """Validate demo data integrity"""
    loader = DataLoader(data_path)
    return loader.validate_data_integrity()
