import os
import httpx
from bs4 import BeautifulSoup
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from intel_graph.state import AgentState, CompanyIntel
from langchain_core.messages import HumanMessage
from intel_graph.state import LeadQualification, OutreachDraft

# Initialize our LLM (Using Groq for ultra-fast inference speeds)
# Make sure you run: export GROQ_API_KEY="your-api-key" in your terminal

# reasoning model
reasoning_llm = ChatGroq(
    model="openai/gpt-oss-120b", 
    temperature=0.1
)

# 2. Fast/Cheap Model
fast_llm = ChatGroq(
    model="llama-3.1-8b-instant", 
    temperature=0.3,
    max_tokens=250  # Cap generation length strictly to prevent runaway output costs
)

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
    structured_llm = reasoning_llm.with_structured_output(CompanyIntel)
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


# ==========================================
# 3. QUALIFICATION NODE (The Gatekeeper)
# ==========================================

def qualification_node(state: AgentState) -> dict:
    """Evaluates the extracted company intelligence against a target B2B profile."""
    intel = state["intel"]
    current_logs = state.get("logs", []).copy()
    
    if not intel:
        current_logs.append("[Qualification Node] Skipped: No company intelligence payload found.")
        return {
            "qualification": LeadQualification(is_fit=False, confidence_score=0.0, justification="Missing company intel."),
            "logs": current_logs
        }
        
    current_logs.append(f"[System] Initiating ICP qualification for {intel.company_name}...")

    # Define the strict target criteria (The Ideal Customer Profile)
    # This aligns directly with GTMER's domain: B2B companies looking for automation
    target_icp_description = (
        "Mid-sized or enterprise B2B companies, tech startups, SaaS organizations, "
        "digital agencies, healthcare platforms, or fintech services. They must sell a product "
        "or service directly to other businesses (B2B). Companies that are strictly B2C "
        "(selling directly to individual retail consumers) are an absolute mismatch."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a strict B2B Sales Operations Specialist evaluating incoming leads.\n"
            "Compare the extracted company profile against the target Ideal Customer Profile (ICP) parameters below.\n\n"
            "Target ICP Parameters:\n{icp_criteria}\n\n"
            "Analyze objectively. If they sell to businesses, mark them as a fit. If they sell strictly to "
            "individual retail consumers, mark them as a mismatch."
        )),
        ("human", (
            "Company Profile Data:\n"
            "- Name: {name}\n"
            "- Product: {product}\n"
            "- Target Audience: {audience}\n"
            "- Value Prop: {value_prop}"
        ))
    ])

    structured_llm = reasoning_llm.with_structured_output(LeadQualification)
    chain = prompt | structured_llm

    try:
        evaluation = chain.invoke({
            "icp_criteria": target_icp_description,
            "name": intel.company_name,
            "product": intel.core_product,
            "audience": intel.target_audience,
            "value_prop": intel.value_proposition
        })
        
        status = "PASSED" if evaluation.is_fit else "FAILED"
        current_logs.append(f"[Qualification Agent] Lead status: {status}. Reason: {evaluation.justification}")
        
        return {
            "qualification": evaluation,
            "logs": current_logs
        }
    except Exception as e:
        current_logs.append(f"[Error] Qualification execution failed: {str(e)}")
        return {
            "qualification": LeadQualification(is_fit=False, confidence_score=0.0, justification=f"Processing error: {str(e)}"),
            "logs": current_logs
        }

# ==========================================
# 4. COPYWRITING NODE (The Convincer)
# ==========================================

def copywriter_node(state: AgentState) -> dict:
    """Generates an elite, hyper-personalized outreach draft in parallel using extracted intel."""
    intel = state.get("intel")
    
    # Safety fallback step: ensure research succeeded
    if not intel:
        return {
            "outreach": None, 
            "logs": ["[Copywriter Node] Skipped: Missing company intel payload."]
        }
        
    new_logs = [f"[System] Drafting context-aware outreach sequence for {intel.company_name}..."]

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an elite B2B Growth Marketer writing cold outreach emails that actually book meetings.\n"
            "Rules:\n"
            "1. Be brief and direct (under 120 words). Never use corporate fluff like 'Hope this finds you well'.\n"
            "2. Lead with a personalized hook based on their actual product value proposition.\n"
            "3. Pitch a clear business transformation (e.g., automating pipeline, cutting manual overhead).\n"
            "4. End with a low-friction, casual call to action (CTA) asking for a short chat next week."
        )),
        ("human", (
            "Company Intel to synthesize:\n"
            "- Target Name: {name}\n"
            "- Target Core Offering: {product}\n"
            "- Target Corporate Value Prop: {value_prop}"
        ))
    ])

    structured_llm = fast_llm.with_structured_output(OutreachDraft)
    chain = prompt | structured_llm

    try:
        outreach_payload = chain.invoke({
            "name": intel.company_name,
            "product": intel.core_product,
            "value_prop": intel.value_proposition
        })
        
        new_logs.append(f"[Copywriter Agent] Completed outreach payload structure for {intel.company_name}.")
        return {
            "outreach": outreach_payload,
            "logs": new_logs
        }
    except Exception as e:
        return {
            "outreach": None, 
            "logs": [f"[Error] Copywriting engine failed: {str(e)}"]
        }