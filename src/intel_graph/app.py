import os
import json
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from state import AgentState
from nodes import research_node, qualification_node, copywriter_node

# ==========================================
# 1. CONDITIONAL ROUTING ROUTER
# ==========================================

def check_qualification_route(state: AgentState) -> str:
    """Evaluates state at runtime to determine the next graph transition node."""
    qualification = state.get("qualification")
    
    # Catch missing data states gracefully
    if not qualification:
        return "exit_workflow"
        
    # Dynamically route: If it passes ICP criteria, go to writer, else terminate
    if qualification.is_fit:
        return "continue_to_outreach"
    return "exit_workflow"

# ==========================================
# 2. STATEGRAPH GRAPH CONFIGURATION
# ==========================================

# Initialize the stateful workflow using our schema blueprint
workflow = StateGraph(AgentState)

# Register our computation nodes into the workflow framework
workflow.add_node("research", research_node)
workflow.add_node("qualify", qualification_node)
workflow.add_node("copywrite", copywriter_node)

# Set the operational entry point execution line
workflow.set_entry_point("research")

# Link the linear execution step
workflow.add_edge("research", "qualify")

# Implement conditional workflow logic stemming out of the qualification node
workflow.add_conditional_edges(
    "qualify",
    check_qualification_route,
    {
        "continue_to_outreach": "copywrite",
        "exit_workflow": END
    }
)

# Connect the copywriter output node straight to the termination boundary
workflow.add_edge("copywrite", END)

# Compile the execution graph into a single executable pipeline application
app = workflow.compile()

# ==========================================
# 3. TEST SUITE EXECUTION ENVIRONMENT
# ==========================================

if __name__ == "__main__":
    # Safety verification checklist check
    if not os.environ.get("API_KEY"):
        print("[System Alert] Execution halted: Missing API_KEY environmental variable.")
        exit(1)

    # Let's run a test domain through our machine
    # You can change this to any B2B domain (e.g., 'stripe.com') to test fit logic
    test_target_input = {"domain": "stripe.com", "logs": []}
    
    print("\n--- RUNNING AGENTIC PIPELINE WORKFLOW ---\n")
    
    # Execute the compiled graph system synchronously
    final_output_state = app.invoke(test_target_input)
    
    print("\n--- COMPLETED EXECUTION WORKFLOW LOGS ---\n")
    for log_event in final_output_state.get("logs", []):
        print(log_event)
        
    print("\n--- FINAL STRUCTURED OUTPUT RESULTS ---\n")
    
    # Isolate and print structural output targets
    intel_data = final_output_state.get("intel")
    qual_data = final_output_state.get("qualification")
    outreach_data = final_output_state.get("outreach")
    
    if intel_data:
        print(f"Company Identified: {intel_data.company_name}")
        print(f"Target Audience: {intel_data.target_audience}")
    if qual_data:
        print(f"ICP Verification Match Status: {qual_data.is_fit} (Confidence: {qual_data.confidence_score})")
    if outreach_data:
        print(f"\nPersonalised Outreach Pitch Generation:\n")
        print(f"Subject: {outreach_data.subject_line}")
        print(f"\n{outreach_data.email_body}")