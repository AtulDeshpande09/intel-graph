import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, Optional

# Import your compiled LangGraph application
from app import app as graph_pipeline

# Initialize FastAPI app
server = FastAPI(
    title="ICP-Scout Engine API",
    description="Production-grade asynchronous multi-agent lead intelligence & outreach generation engine.",
    version="1.0.0"
)

# Enable CORS so a frontend (React/Streamlit) can easily talk to this backend
server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 1. API REQUEST & RESPONSE SCHEMAS
# ==========================================

class ResearchRequest(BaseModel):
    """The incoming payload validation schema."""
    domain: str = BaseModel.Field(..., example="stripe.com", description="The target company domain to analyze.")

class ResearchResponse(BaseModel):
    """The structured server response payload."""
    status: str
    domain: str
    logs: list[str]
    intel: Optional[Dict[str, Any]] = None
    qualification: Optional[Dict[str, Any]] = None
    outreach: Optional[Dict[str, Any]] = None

# ==========================================
# 2. ENDPOINT DEFINITIONS
# ==========================================

@server.get("/health", tags=["System"])
def health_check():
    """Simple health check endpoint to confirm backend availability."""
    if not os.environ.get("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY environment variable is missing.")
    return {"status": "healthy", "engine": "LangGraph Active"}

@server.post("/api/research", response_model=ResearchResponse, tags=["Core Engine"])
async def trigger_lead_research(payload: ResearchRequest):
    """
    Triggers the multi-agent state machine pipeline to scrape, qualify,
    and generate custom outreach copy for a given target domain.
    """
    # Clean the input domain format
    target_domain = payload.domain.strip().lower()
    
    try:
        # Initialize the state schema required by our LangGraph application
        initial_state = {
            "domain": target_domain,
            "logs": []
        }
        
        # Execute the state machine workflow synchronously within the async route
        # LangGraph invoke processes the nodes sequentially based on graph rules
        final_state = graph_pipeline.invoke(initial_state)
        
        # Determine final operational status based on qualification metrics
        qual = final_state.get("qualification")
        status_flag = "Qualified & Drafted" if (qual and qual.is_fit) else "Disqualified / Processed"
        
        # Convert internal Pydantic payloads from state back into dictionary formats for JSON serialization
        return ResearchResponse(
            status=status_flag,
            domain=target_domain,
            logs=final_state.get("logs", []),
            intel=final_state.get("intel").model_dump() if final_state.get("intel") else None,
            qualification=qual.model_dump() if qual else None,
            outreach=final_state.get("outreach").model_dump() if final_state.get("outreach") else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Internal multi-agent state machine execution failure: {str(e)}"
        )