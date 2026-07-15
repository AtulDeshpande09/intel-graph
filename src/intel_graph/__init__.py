"""
intel-graph: An autonomous multi-agent lead intelligence & outreach generation engine.
Built with LangGraph, FastAPI, and Pydantic.
"""

from intel_graph.app import app
from intel_graph.state import AgentState, CompanyIntel, LeadQualification, OutreachDraft
from intel_graph.nodes import research_node, qualification_node, copywriter_node

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