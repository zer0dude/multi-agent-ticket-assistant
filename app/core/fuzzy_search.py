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
                match_reason="Kein Firmenname angegeben"
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
            match_reason="Keine passende Kundenzuordnung gefunden"
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
                    match_reason="Exakte Firmenname-Übereinstimmung",
                    relevant_data=self._extract_customer_data(customer)
                )
        return None
    
    def _find_fuzzy_company_match(self, company_name: str) -> Optional[CustomerMatchResult]:
        """Find fuzzy company name match using consensus scoring"""
        best_match = None
        best_score = 0.0
        best_customer = None
        
        for customer in self.customers:
            # Calculate consensus score with length penalty
            score = self._calculate_consensus_score(company_name, customer.name)
            
            if score > best_score:
                best_score = score
                best_match = customer.name
                best_customer = customer
        
        # Require minimum 75% consensus score (raised from 60%)
        if best_score >= 0.75:
            return CustomerMatchResult(
                customer_id=best_customer.id,
                customer_name=best_customer.name,
                confidence_score=best_score,
                match_reason=f"Ungefähre Firmenname-Übereinstimmung (Konsens-Score: {best_score:.1%})",
                relevant_data=self._extract_customer_data(best_customer)
            )
        
        return None
    
    def _calculate_consensus_score(self, name1: str, name2: str) -> float:
        """
        Calculate consensus score using multiple algorithms with length penalty
        
        Args:
            name1: First company name
            name2: Second company name
            
        Returns:
            Consensus score between 0.0 and 1.0
        """
        # Extract core company names (remove German legal forms)
        core_name1 = self._extract_core_company_name(name1)
        core_name2 = self._extract_core_company_name(name2)
        
        # Calculate scores using different algorithms
        ratio_score = fuzz.ratio(core_name1.lower(), core_name2.lower())
        partial_score = fuzz.partial_ratio(core_name1.lower(), core_name2.lower())
        token_score = fuzz.token_sort_ratio(core_name1.lower(), core_name2.lower())
        
        # Convert to 0-1 scale
        scores = [ratio_score / 100.0, partial_score / 100.0, token_score / 100.0]
        
        # Require at least 2 out of 3 algorithms to score above 0.6
        high_scores = [s for s in scores if s >= 0.6]
        if len(high_scores) < 2:
            return 0.0  # Consensus failed
        
        # Additional check: prevent partial word matching without core company name
        # If one name is much shorter and is just a partial match, be more strict
        if self._is_likely_partial_match(core_name1, core_name2, scores[1]):
            return 0.0  # Reject partial-only matches
        
        # Calculate weighted average (ratio gets higher weight for exact matching)
        weighted_score = (scores[0] * 0.4 + scores[1] * 0.3 + scores[2] * 0.3)
        
        # Apply length penalty for significantly different lengths
        length_penalty = self._calculate_length_penalty(core_name1, core_name2)
        
        # Final consensus score
        consensus_score = weighted_score * length_penalty
        
        return consensus_score
    
    def _is_likely_partial_match(self, name1: str, name2: str, partial_score: float) -> bool:
        """
        Check if this appears to be a problematic partial match
        
        Args:
            name1: First company name
            name2: Second company name  
            partial_score: Partial ratio score
            
        Returns:
            True if this looks like a problematic partial-only match
        """
        # If partial score is high but names are very different lengths, it might be partial-only
        if partial_score >= 0.7:  # High partial score
            words1 = set(name1.lower().split())
            words2 = set(name2.lower().split())
            
            # Remove common German business words that shouldn't count as matches
            business_words = {'gmbh', 'ag', 'kg', 'maschinenbau', 'laboratorien', 'labs', 'industries'}
            words1_filtered = words1 - business_words
            words2_filtered = words2 - business_words
            
            # If one name has no unique business words, it's likely just matching common terms
            if len(words1_filtered) == 0 or len(words2_filtered) == 0:
                return True
                
            # If there's no overlap in actual business words, it's a false match
            if len(words1_filtered & words2_filtered) == 0:
                return True
        
        return False
    
    def _extract_core_company_name(self, company_name: str) -> str:
        """
        Extract core business name from German company name
        
        Args:
            company_name: Full company name
            
        Returns:
            Core business name without legal suffixes
        """
        # Common German legal forms
        legal_forms = [
            'gmbh', 'ag', 'kg', 'ohg', 'gbr', 'ug', 'eg', 'ev',
            'gmbh & co. kg', 'gmbh & co kg', 'se', 'kgaa'
        ]
        
        name_lower = company_name.lower().strip()
        
        # Remove common legal forms from the end
        for form in legal_forms:
            if name_lower.endswith(' ' + form):
                name_lower = name_lower[:-len(form)-1].strip()
                break
            elif name_lower.endswith(form):
                name_lower = name_lower[:-len(form)].strip()
                break
        
        # Remove common German business suffixes
        suffixes = ['gesellschaft', 'unternehmen', 'betrieb', 'firma']
        for suffix in suffixes:
            if name_lower.endswith(' ' + suffix):
                name_lower = name_lower[:-len(suffix)-1].strip()
                break
        
        return name_lower.title()  # Return with proper capitalization
    
    def _calculate_length_penalty(self, name1: str, name2: str) -> float:
        """
        Calculate length penalty for significantly different name lengths
        
        Args:
            name1: First name
            name2: Second name
            
        Returns:
            Length penalty factor (0.5 to 1.0)
        """
        len1, len2 = len(name1), len(name2)
        
        if len1 == 0 or len2 == 0:
            return 0.5
        
        # Calculate length ratio (shorter/longer)
        length_ratio = min(len1, len2) / max(len1, len2)
        
        # No penalty if lengths are similar (ratio > 0.7)
        if length_ratio >= 0.7:
            return 1.0
        
        # Moderate penalty for somewhat different lengths (0.5 < ratio < 0.7)
        elif length_ratio >= 0.5:
            return 0.85
        
        # Strong penalty for very different lengths (ratio < 0.5)
        else:
            return 0.6
    
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
                            match_reason=f"E-Mail-Domain-Übereinstimmung mit Firmenname-Ähnlichkeit ({name_similarity}%)",
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
                    'purchase_date': purchase.purchase_date
                }
                for purchase in customer.purchases
            ]
        
        # Add company info if available
        if hasattr(customer, 'company_info'):
            data['company_info'] = {
                'founded': customer.company_info.founded,
                'employees': customer.company_info.employees,
                'business': customer.company_info.business
            }
        
        # Add notes if available
        if hasattr(customer, 'notes') and customer.notes:
            data['notes'] = customer.notes
        
        return data
