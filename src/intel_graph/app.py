import os
import json
import asyncio
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from intel_graph.state import AgentState
from intel_graph.nodes import research_node, qualification_node, copywriter_node

from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. AGGREGATOR & ROUTER LOGIC
# ==========================================

def aggregate_node(state: AgentState) -> AgentState:
    """Combines parallel outputs and drops outreach copy if disqualified."""
    qualification = state.get("qualification")
    
    # If the company didn't pass ICP, drop the generated email draft
    if qualification and not qualification.is_fit:
        state["outreach"] = None
        state["status"] = "Disqualified"
    else:
        state["status"] = "Qualified & Drafted"
        
    return state


# ==========================================
# 2. STATEGRAPH CONFIGURATION (PARALLEL)
# ==========================================

workflow = StateGraph(AgentState)

# Register nodes
workflow.add_node("research", research_node)
workflow.add_node("qualify", qualification_node)
workflow.add_node("copywrite", copywriter_node)
workflow.add_node("aggregate", aggregate_node)

# Entry point
workflow.set_entry_point("research")

# FAN-OUT: Run qualify AND copywrite concurrently right after research!
workflow.add_edge("research", "qualify")
workflow.add_edge("research", "copywrite")

# FAN-IN: Both parallel nodes stream their outputs into the aggregator
workflow.add_edge("qualify", "aggregate")
workflow.add_edge("copywrite", "aggregate")

workflow.add_edge("aggregate", END)

# Compile application
app = workflow.compile()


# ==========================================
# 3. ASYNC / STREAMING TEST SUITE
# ==========================================

async def main():
    if not os.environ.get("GROQ_API_KEY"):
        print("[System Alert] Missing GROQ_API_KEY environment variable.")
        return

    test_target_input = {"domain": "stripe.com", "logs": []}
    
    print("\n--- RUNNING PARALLEL AGENTIC PIPELINE (STREAMING) ---\n")
    
    # Using astream gives you real-time node outputs as they finish!
    async for event in app.astream(test_target_input):
        for node_name, state_update in event.items():
            print(f"[Node Completed]: {node_name}")
            if "logs" in state_update and state_update["logs"]:
                print(f"   └─ Log: {state_update['logs'][-1]}")

if __name__ == "__main__":
    asyncio.run(main())