"""
Fuzzy search for customer identification
"""

from fuzzywuzzy import fuzz, process
from typing import List, Dict, Any, Optional, Tuple
from app.core.models import Customer
from app.core.research_models import CustomerMatchResult

class CustomerFuzzySearch:
    """Fuzzy search for matching customers in CRM data"""
    
    def __init__(self, crm_data):
        """Initialize with CRM data"""
        self.customers = crm_data.customers if hasattr(crm_data, 'customers') else crm_data
        self.customer_names = {customer.name: customer for customer in self.customers}
        self.customer_ids = {customer.id: customer for customer in self.customers}
    
    def find_customer_match(self, company_name: str, contact_name: str = "", contact_email: str = "") -> CustomerMatchResult:
        """
        Find the best matching customer using fuzzy search
        
        Args:
            company_name: Company name from ticket form
            contact_name: Contact person name (optional)
            contact_email: Contact email (optional)
            
        Returns:
            CustomerMatchResult with match details
        """
        if not company_name or not company_name.strip():
            return CustomerMatchResult(
                confidence_score=0.0,
                match_reason="No company name provided"
            )
        
        # Try exact company name match first
        exact_match = self._find_exact_match(company_name)
        if exact_match:
            return exact_match
        
        # Try fuzzy company name match
        fuzzy_match = self._find_fuzzy_company_match(company_name)
        if fuzzy_match and fuzzy_match.confidence_score > 0.7:
            return fuzzy_match
        
        # Try contact-based matching if available
        if contact_email:
            email_match = self._find_email_match(contact_email, company_name)
            if email_match and email_match.confidence_score > fuzzy_match.confidence_score:
                return email_match
        
        # Return best fuzzy match or no match
        return fuzzy_match if fuzzy_match else CustomerMatchResult(
            confidence_score=0.0,
            match_reason="No suitable customer match found"
        )
    
    def _find_exact_match(self, company_name: str) -> Optional[CustomerMatchResult]:
        """Find exact company name match"""
        company_name_clean = company_name.strip().lower()
        
        for customer in self.customers:
            if customer.name.strip().lower() == company_name_clean:
                return CustomerMatchResult(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    confidence_score=1.0,
                    match_reason="Exact company name match",
                    relevant_data=self._extract_customer_data(customer)
                )
        return None
    
    def _find_fuzzy_company_match(self, company_name: str) -> Optional[CustomerMatchResult]:
        """Find fuzzy company name match"""
        company_names = [customer.name for customer in self.customers]
        
        # Get best match using different fuzzy algorithms
        matches = [
            process.extractOne(company_name, company_names, scorer=fuzz.ratio),
            process.extractOne(company_name, company_names, scorer=fuzz.partial_ratio),
            process.extractOne(company_name, company_names, scorer=fuzz.token_sort_ratio)
        ]
        
        # Find the best overall match
        best_match = max(matches, key=lambda x: x[1] if x else 0)
        
        if best_match and best_match[1] >= 60:  # Minimum 60% similarity
            matched_customer = self.customer_names[best_match[0]]
            confidence = best_match[1] / 100.0
            
            return CustomerMatchResult(
                customer_id=matched_customer.id,
                customer_name=matched_customer.name,
                confidence_score=confidence,
                match_reason=f"Fuzzy company name match (similarity: {best_match[1]}%)",
                relevant_data=self._extract_customer_data(matched_customer)
            )
        
        return None
    
    def _find_email_match(self, contact_email: str, company_name: str) -> Optional[CustomerMatchResult]:
        """Find match based on contact email domain"""
        if not contact_email or '@' not in contact_email:
            return None
        
        email_domain = contact_email.split('@')[1].lower()
        
        for customer in self.customers:
            # Check if customer email domain matches
            if hasattr(customer, 'contact_person') and customer.contact_person.email:
                customer_domain = customer.contact_person.email.split('@')[1].lower()
                if customer_domain == email_domain:
                    # Also check if company names are somewhat similar
                    name_similarity = fuzz.partial_ratio(company_name.lower(), customer.name.lower())
                    if name_similarity >= 50:  # Loose match for email-based matching
                        confidence = min(0.9, (name_similarity + 70) / 100.0)  # Boost confidence for email match
                        
                        return CustomerMatchResult(
                            customer_id=customer.id,
                            customer_name=customer.name,
                            confidence_score=confidence,
                            match_reason=f"Email domain match with company name similarity ({name_similarity}%)",
                            relevant_data=self._extract_customer_data(customer)
                        )
        
        return None
    
    def _extract_customer_data(self, customer: Customer) -> Dict[str, Any]:
        """Extract relevant customer data for display"""
        data = {
            'customer_id': customer.id,
            'name': customer.name,
            'support_tier': customer.support_tier.value,
            'customer_since': customer.customer_since,
            'contact_person': {
                'name': customer.contact_person.name,
                'email': customer.contact_person.email,
                'phone': customer.contact_person.phone,
                'title': customer.contact_person.title
            }
        }
        
        # Add purchased products
        if hasattr(customer, 'purchases') and customer.purchases:
            data['purchased_products'] = [
                {
                    'sku': purchase.sku,
                    'installation_location': purchase.installation_location,
                    'installation_date': purchase.installation_date
                }
                for purchase in customer.purchases
            ]
        
        # Add company info if available
        if hasattr(customer, 'company_info'):
            data['company_info'] = {
                'employees': customer.company_info.employees,
                'industry': customer.company_info.industry,
                'annual_revenue_eur': customer.company_info.annual_revenue_eur
            }
        
        # Add notes if available
        if hasattr(customer, 'notes') and customer.notes:
            data['notes'] = customer.notes
        
        return data
