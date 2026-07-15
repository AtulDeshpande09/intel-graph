import streamlit as st
import httpx

# Configure professional page layout
st.set_page_config(page_title="Intel-Graph Engine", page_icon="🤖", layout="wide")

st.title("🤖 Intel-Graph: Autonomous Lead Intelligence Engine")
st.markdown("Extract web intelligence, qualify leads via custom ICP gates, and draft tailored outreach automatically.")
st.write("---")

# Layout columns: Search Bar & Actions
col1, col2 = st.columns([3, 1])
with col1:
    domain_input = st.text_input("Target Company Domain", placeholder="e.g., vercel.com", label_visibility="collapsed")
with col2:
    submit_btn = st.button("Analyze Lead", use_container_width=True, type="primary")

if submit_btn and domain_input:
    # Clean the input domain link
    clean_domain = domain_input.replace("https://", "").replace("http://", "").split("/")[0]
    
    st.info(st.markdown(f"**Target Locked:** Processing pipeline execution for `{clean_domain}`..."))
    
    # Progress step spinner
    with st.spinner("Agents orchestrating workflow execution..."):
        try:
            # Synchronous request call to your active local FastAPI microservice
            with httpx.Client(timeout=45.0) as client:
                response = client.post("http://127.0.0.1:8000/api/research", json={"domain": clean_domain})
            
            if response.status_code == 200:
                data = response.json()
                
                # Check execution pipeline routing status
                if "Qualified" in data.get("status", ""):
                    st.success("🎉 Target Successfully Passed ICP Qualification Gates!")
                    
                    # Split view layout for parsed data payload
                    left_pane, right_pane = st.columns(2)
                    
                    with left_pane:
                        st.subheader("📋 Extracted Company Intel")
                        intel = data.get("intel", {})
                        st.metric(label="Company Name", value=intel.get("company_name", "N/A"))
                        st.markdown(f"**Core Product:** {intel.get('core_product')}")
                        st.markdown(f"**Value Prop:** {intel.get('value_proposition')}")
                        st.markdown("**Inferred Tech Stack:**")
                        st.code(", ".join(intel.get("estimated_tech_stack", [])), language="text")
                        
                    with right_pane:
                        st.subheader("✉️ Tailored Copywriting Outreach")
                        outreach = data.get("outreach", {})
                        st.text_input("Subject Line", value=outreach.get("subject_line", ""), disabled=True)
                        st.text_area("Email Body", value=outreach.get("email_body", ""), height=250)
                
                else:
                    st.warning("🚫 Target Lead Disqualified / Dropped at ICP Gate")
                    qual = data.get("qualification", {})
                    st.error(f"**Justification:** {qual.get('justification')}")
                
                # Expandable workflow engine step execution traces
                with st.expander("👁️ View Agent Runtime System Logs"):
                    for log in data.get("logs", []):
                        st.text(log)
            else:
                st.error(f"Backend Server returned an error code: {response.status_code}")
                
        except Exception as e:
            st.error(f"Failed to connect to backend microservice pipeline: {str(e)}")