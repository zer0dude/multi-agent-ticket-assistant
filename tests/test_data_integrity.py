"""
Test script to validate the integrity of our demo data
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.core.data import validate_demo_data, load_all_data
from app.core.models import TicketStatus


def test_data_loading():
    """Test that all data files can be loaded without errors"""
    print("Testing data loading...")
    
    try:
        crm_data, tickets, manuals, sops = load_all_data()
        print("✅ All data loaded successfully")
        
        # Print summary
        print(f"   - CRM: {len(crm_data.customers)} customers, {len(crm_data.products)} products")
        print(f"   - Tickets: {len(tickets)} total")
        print(f"   - Manuals: {len(manuals)} sections")
        print(f"   - SOPs: {len(sops)} characters")
        
        return True
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return False


def test_data_integrity():
    """Test cross-references and data consistency"""
    print("\nTesting data integrity...")
    
    validation = validate_demo_data()
    
    if validation["valid"]:
        print("✅ All data integrity checks passed")
    else:
        print("❌ Data integrity issues found:")
        for issue in validation["issues"]:
            print(f"   - {issue}")
    
    if validation["warnings"]:
        print("⚠️ Warnings:")
        for warning in validation["warnings"]:
            print(f"   - {warning}")
    
    # Print data summary
    print("\nData Summary:")
    for key, value in validation["data_summary"].items():
        print(f"   - {key}: {value}")
    
    return validation["valid"]


def test_ticket_scenarios():
    """Test that our demo tickets have the expected scenarios"""
    print("\nTesting ticket scenarios...")
    
    try:
        _, tickets, _, _ = load_all_data()
        
        # Find our demo tickets
        t_ex1 = None
        t_ex2 = None
        t_old1 = None
        t_old2 = None
        
        for ticket in tickets:
            if ticket.ticket_id == "T-EX1":
                t_ex1 = ticket
            elif ticket.ticket_id == "T-EX2":
                t_ex2 = ticket
            elif ticket.ticket_id == "T-OLD1":
                t_old1 = ticket
            elif ticket.ticket_id == "T-OLD2":
                t_old2 = ticket
        
        # Validate T-EX1 (GW-300 problem)
        if t_ex1:
            assert t_ex1.status == TicketStatus.OPEN, "T-EX1 should be open"
            assert "GW-300" in t_ex1.related_skus, "T-EX1 should relate to GW-300"
            assert "C-ACME" == t_ex1.customer_id, "T-EX1 should be from Acme"
            assert "2 meter" in t_ex1.body.lower() or "2m" in t_ex1.body.lower(), "T-EX1 should mention 2m height"
            print("✅ T-EX1 (GW-300 cavitation issue) validated")
        else:
            print("❌ T-EX1 not found")
            return False
        
        # Validate T-EX2 (VP-200 problem)
        if t_ex2:
            assert t_ex2.status == TicketStatus.OPEN, "T-EX2 should be open"
            assert "VP-200" in t_ex2.related_skus, "T-EX2 should relate to VP-200"
            assert "C-BIOV" == t_ex2.customer_id, "T-EX2 should be from Biovisco"
            assert "7000 cP" in t_ex2.body, "T-EX2 should mention 7000 cP viscosity"
            print("✅ T-EX2 (VP-200 glucose issue) validated")
        else:
            print("❌ T-EX2 not found")
            return False
        
        # Validate closed tickets have summaries
        if t_old1:
            assert t_old1.status == TicketStatus.CLOSED, "T-OLD1 should be closed"
            assert t_old1.summary is not None, "T-OLD1 should have summary"
            assert len(t_old1.summary.tags) > 0, "T-OLD1 should have tags"
            print("✅ T-OLD1 (closed with summary) validated")
        else:
            print("❌ T-OLD1 not found")
            return False
        
        if t_old2:
            assert t_old2.status == TicketStatus.CLOSED, "T-OLD2 should be closed"
            assert t_old2.summary is not None, "T-OLD2 should have summary"
            print("✅ T-OLD2 (closed with summary) validated")
        else:
            print("❌ T-OLD2 not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ticket scenario validation failed: {e}")
        return False


def test_manual_content():
    """Test that manuals contain expected content for demo scenarios"""
    print("\nTesting manual content...")
    
    try:
        _, _, manuals, _ = load_all_data()
        
        # Check GW-300 manual has cavitation/saughöhe content (relates to T-EX1)
        gw_300_sections = [m for m in manuals if m.product_sku == "GW-300"]
        has_saughöhe_content = False
        has_kavitation_content = False
        
        for section in gw_300_sections:
            content_lower = section.content.lower()
            if "saughöhe" in content_lower or "1,5" in content_lower or "1.5" in content_lower:
                has_saughöhe_content = True
            if "kavitation" in content_lower or "pfeif" in content_lower:
                has_kavitation_content = True
        
        if has_saughöhe_content and has_kavitation_content:
            print("✅ GW-300 manual contains relevant content for T-EX1 scenario")
        else:
            print("❌ GW-300 manual missing key content for demo scenario")
            return False
        
        # Check VP-200 manual has viscosity content (relates to T-EX2) 
        vp_200_sections = [m for m in manuals if m.product_sku == "VP-200"]
        has_viscosity_content = False
        has_glucose_content = False
        
        for section in vp_200_sections:
            content_lower = section.content.lower()
            if "viskosität" in content_lower or "7000" in content_lower:
                has_viscosity_content = True
            if "glucose" in content_lower or "glukose" in content_lower:
                has_glucose_content = True
        
        if has_viscosity_content:
            print("✅ VP-200 manual contains relevant content for T-EX2 scenario")
        else:
            print("❌ VP-200 manual missing viscosity content for demo scenario")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Manual content validation failed: {e}")
        return False


def main():
    """Run all data validation tests"""
    print("🔍 Multi-Agent Ticketing Assistant - Data Validation")
    print("=" * 60)
    
    all_passed = True
    
    # Run all tests
    all_passed &= test_data_loading()
    all_passed &= test_data_integrity()
    all_passed &= test_ticket_scenarios()
    all_passed &= test_manual_content()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All validation tests passed! Phase 1 complete.")
        print("\nDemo data is ready for Phase 2 development.")
    else:
        print("💥 Some validation tests failed. Please fix issues before proceeding.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
