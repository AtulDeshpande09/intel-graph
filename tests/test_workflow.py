import pytest
from icp_scout.app import check_qualification_route
from icp_scout.state import LeadQualification

def test_route_continues_on_valid_icp():
    """Ensures that the state machine accurately advances to the copywriter if the company matches the target ICP."""
    mock_state = {
        "domain": "stripe.com",
        "qualification": LeadQualification(is_fit=True, confidence_score=0.9, justification="Valid business model.")
    }
    
    next_route = check_qualification_route(mock_state)
    assert next_route == "continue_to_outreach"

def test_route_exits_on_invalid_icp():
    """Ensures that the state machine terminates early if the lead fails target criteria, protecting runtime costs."""
    mock_state = {
        "domain": "nike.com",
        "qualification": LeadQualification(is_fit=False, confidence_score=0.95, justification="Target is strictly B2C consumer-facing.")
    }
    
    next_route = check_qualification_route(mock_state)
    assert next_route == "exit_workflow"