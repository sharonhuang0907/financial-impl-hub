import streamlit as st
from zeep import Client
import os
import json

# --- Page Configuration ---
st.set_page_config(page_title="Financial Implementation Hub", layout="wide", page_icon="🏦")

# --- Custom Styling ---
st.markdown("""
    <style>
    .app-card {
        border-radius: 15px;
        padding: 25px;
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        height: 250px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    </style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "Marketplace"
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Dialog: Connection Settings ---
@st.dialog("Workday Connection Settings")
def connection_modal():
    st.write("Enter your Workday tenant credentials. These are stored only for this session.")
    host = st.text_input("Host", value=st.session_state.get('wd_host', 'wd3-impl-services1.workday.com'))
    tenant = st.text_input("Tenant Name", value=st.session_state.get('wd_tenant', ''))
    user = st.text_input("ISU Username", value=st.session_state.get('wd_user', ''))
    pwd = st.text_input("Password", type="password")
 
    if st.button("Save & Verify"):
        if all([host, tenant, user, pwd]):
            st.session_state.wd_host = host
            st.session_state.wd_tenant = tenant
            st.session_state.wd_user = user
            st.session_state.wd_pass = pwd
            st.success("Credentials saved!")
            st.rerun()




# --- Logic: Workday SOAP Call ---
def execute_workday_call(tx_type, extracted_data):
    try:
        user = st.session_state.wd_user
        pwd = st.session_state.wd_pass
        host = st.session_state.wd_host
        tenant = st.session_state.wd_tenant
        
        wsdl_url = f"https://{host}/ccx/service/{tenant}/Financial_Management/v41.0?wsdl"
        
        auth = UsernameToken(user, pwd)
        client = Client(wsdl_url, wsse=auth)
        
        # This is a simplified request structure; specific XSD mapping may be needed per operation
        request_data = {
            "Control_Amount_Total": extracted_data['amount'],
            "Currency_Reference": {"ID": {"_value_1": extracted_data['currency'], "type": "Currency_ID"}},
            "Memo": extracted_data['memo']
        }
        
        # Access the operation dynamically
        operation = getattr(client.service, f"Submit_{tx_type}")
        response = operation(Request_Data=request_data)
        return {"status": "success", "response": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Sidebar ---
with st.sidebar:
    st.title("Financial Hub")
    if st.button("🏠 Marketplace Home", use_container_width=True):
        st.session_state.current_page = "Marketplace"
    
    st.divider()
    # Status Indicator
    if "wd_pass" in st.session_state:
        st.success("● Workday Connected")
    else:
        st.error("○ Workday Disconnected")

# --- Main App Views ---

# 1. VIEW: Marketplace
if st.session_state.current_page == "Marketplace":
    st.title("Implementation Marketplace")
    st.write("Select a module to begin implementation testing.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="app-card"><h3>🔗 Connection</h3><p>Manage your Workday API credentials and Tenant settings.</p></div>', unsafe_allow_html=True)
        if st.button("Open Settings", key="btn_conn", use_container_width=True):
            connection_modal()

    with col2:
        st.markdown('<div class="app-card"><h3>💳 Payment Test Creator</h3><p>Convert chat requests into Workday SOAP transactions automatically.</p></div>', unsafe_allow_html=True)
        if st.button("Launch Creator", key="btn_pay", use_container_width=True):
            if "wd_pass" not in st.session_state:
                st.warning("Please configure Connection first!")
            else:
                st.session_state.current_page = "Payment Creator"
                st.rerun()

# 2. VIEW: Payment Creator
elif st.session_state.current_page == "Payment Creator":
    st.title("💳 Payment Test Creator")
    
    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ex: Create a supplier invoice for $500 to Office Depot"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.status("Brainstorming with Gemini AI...") as status:
                extracted = ai_analyze_request(prompt)
                if extracted:
                    status.update(label="Analysis Complete!", state="complete")
                    st.write(f"**Target Operation:** `Submit_{extracted['transaction_type']}`")
                    st.json(extracted)
                    
                    # Store extraction in session state to use in button click
                    st.session_state.last_extraction = extracted
                else:
                    status.update(label="Analysis Failed", state="error")

        if "last_extraction" in st.session_state:
            if st.button("🚀 Execute Transaction in Workday"):
                with st.spinner("Pushing to Workday Tenant..."):
                    result = execute_workday_call(
                        st.session_state.last_extraction['transaction_type'], 
                        st.session_state.last_extraction
                    )
                    if result["status"] == "success":
                        st.balloons()
                        st.success("Transaction Created Successfully!")
                        st.expander("Raw Response").write(result["response"])
                    else:
                        st.error(f"Workday Error: {result['message']}")
