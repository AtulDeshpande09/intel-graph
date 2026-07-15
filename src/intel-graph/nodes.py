import os
import httpx
from bs4 import BeautifulSoup
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState, CompanyIntel

# Initialize our LLM (Using Groq for ultra-fast inference speeds)
# Make sure you run: export GROQ_API_KEY="your-api-key" in your terminal
llm = ChatGroq(model="llama-3.1-70b-versatile", temperature=0.1)

# ==========================================
# 1. WEB SCRAPING UTILITY
# ==========================================

def scrape_domain(domain: str) -> str:
    """Helper function to fetch and clean raw text from a domain."""
    # Ensure standard url format
    url = domain if domain.startswith(("http://", "https://")) else f"https://{domain}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # Use a strict timeout so the state machine never gets hung up permanently
        with httpx.Client(headers=headers, follow_redirects=True, timeout=10.0) as client:
            response = client.get(url)
            response.raise_for_status()
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Strip script, style, and navigation tags that bloat token count
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.extract()
            
        # Extract clean text segments, stripping extra whitespaces
        chunks = (phrase.strip() for line in soup.get_text().splitlines() for phrase in line.split("  "))
        clean_text = "\n".join(chunk for chunk in chunks if chunk)
        
        # Truncate content length to prevent context window explosion
        return clean_text[:6000]
        
    except Exception as e:
        return f"Error scraping target domain {url}: {str(e)}"

# ==========================================
# 2. LANGGRAPH WORKFLOW NODES
# ==========================================

def research_node(state: AgentState) -> dict:
    """Scrapes the domain and leverages structured LLM outputs to parse company metrics."""
    domain = state["domain"]
    current_logs = state.get("logs", []).copy()
    
    current_logs.append(f"[System] Initiating data acquisition for: {domain}")
    
    # Execute the scraping utility
    raw_text = scrape_domain(domain)
    
    if raw_text.startswith("Error"):
        current_logs.append(f"[Error] Data acquisition failed: {raw_text}")
        return {
            "raw_web_text": raw_text,
            "intel": None,
            "logs": current_logs
        }
        
    current_logs.append("[System] Data acquisition complete. Processing text via structured LLM schema.")
    
    # Design an aggressive formatting prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert B2B data extraction analyst. Analyze the following raw website "
            "text and cleanly pull structured intelligence about the company according to the schema provided.\n\n"
            "Raw Website Content:\n{website_content}"
        ))
    ])
    
    # Enforce Pydantic structure directly on our fast inference LLM
    structured_llm = llm.with_structured_output(CompanyIntel)
    chain = prompt | structured_llm
    
    try:
        extracted_intel = chain.invoke({"website_content": raw_text})
        current_logs.append(f"[Research Agent] Successfully isolated data payload for {extracted_intel.company_name}.")
        return {
            "raw_web_text": raw_text,
            "intel": extracted_intel,
            "logs": current_logs
        }
    except Exception as e:
        current_logs.append(f"[Error] Schema structure parsing error: {str(e)}")
        return {
            "raw_web_text": raw_text,
            "intel": None,
            "logs": current_logs
        }