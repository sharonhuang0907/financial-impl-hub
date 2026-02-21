import streamlit as st
from zeep import Client
from zeep.wsse.username_token import UsernameToken
import os

# --- Workday Connection Function ---
def call_workday_api(transaction_type, data):
    """
    Connects to Workday and executes the specific Financial Management service.
    """
    # 1. Credentials (Pull from Streamlit Secrets or .env)
    WD_USER = st.secrets["WD_USER"]
    WD_PASS = st.secrets["WD_PASS"]
    # Example WSDL URL for Financial Management
    WSDL_URL = f"https://{st.secrets['WD_HOST']}/ccx/service/{st.secrets['WD_TENANT']}/Financial_Management/v41.0?wsdl"

    try:
        # 2. Setup Security and Client
        auth = UsernameToken(WD_USER, WD_PASS)
        client = Client(WSDL_URL, wsse=auth)

        # 3. Dynamic Service Selection
        # Maps the AI-identified type to the actual Workday Operation
        operations = {
            "Supplier_Invoice": client.service.Submit_Supplier_Invoice,
            "Miscellaneous_Payment": client.service.Submit_Miscellaneous_Payment,
            "Ad_Hoc_Payment": client.service.Submit_Ad_Hoc_Payment
        }

        service_function = operations.get(transaction_type)
        
        if not service_function:
            return {"status": "error", "message": f"Operation {transaction_type} not supported."}

        # 4. Execute the request
        # 'data' must be a dictionary matching the Workday XSD structure
        response = service_function(Request_Data=data)
        
        return {"status": "success", "data": response}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- UI Implementation ---
st.title("🚀 Workday Execution Engine")

# This button would sit under the AI-generated XML preview
if st.button("🚀 Execute to Workday Tenant"):
    with st.spinner("Communicating with Workday..."):
        
        # Placeholder data from the AI analysis step
        mock_data = {
            "Memo": "Test Payment from Streamlit Hub",
            "Control_Amount_Total": 500.00,
            "Currency_Reference": {"ID": {"_value_1": "USD", "type": "Currency_ID"}}
        }
        
        # Replace 'Supplier_Invoice' with the dynamic variable from the AI
        result = call_workday_api("Supplier_Invoice", mock_data)

        if result["status"] == "success":
            st.balloons()
            st.success("Success! Transaction ID Created.")
            st.json(result["data"])
        else:
            st.error(f"Workday API Error: {result['message']}")
