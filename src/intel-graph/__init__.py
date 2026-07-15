"""
intel-graph: An autonomous multi-agent lead intelligence & outreach generation engine.
Built with LangGraph, FastAPI, and Pydantic.
"""

from icp_scout.app import app
from icp_scout.state import AgentState, CompanyIntel, LeadQualification, OutreachDraft
from icp_scout.nodes import research_node, qualification_node, copywriter_node

# Explicitly define what gets exported when someone runs "from icp_scout import *"
__all__ = [
    "app",
    "AgentState",
    "CompanyIntel",
    "LeadQualification",
    "OutreachDraft",
    "research_node",
    "qualification_node",
    "copywriter_node",
]