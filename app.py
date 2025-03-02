import streamlit as st
import time
import random
import pandas as pd
from dotenv import load_dotenv
from agent import agent
import os
load_dotenv()

global_call_status = {"call_status": ""}

    
# App Title
st.title("📞 Vocalyze - Agentic AI-Driven Spoken Aptitude Test")

# Number input field
phone_number = st.text_input("Enter your phone number", placeholder="+1234567890", autocomplete="off")

# Language selection
language = st.selectbox("Select Language", ["English", "Urdu", "Spanish", "French"])

# Call status placeholder
status_placeholder = st.empty()

# Call statuses to simulate real-time updates
call_statuses = ["Queue", "Dialing", "Busy", "Ongoing", "Failed", "Completed"]

# Start Call button
if st.button("Start Call"):
    if phone_number and language:
        st.success(f"📞 Calling {phone_number} for an aptitude test in {language}...")
        agent_response = agent("+9232", "2", "en", global_call_status)
        print(agent_response)
        

        if global_call_status["call_status"] == "queue":
            status_placeholder.write(f"📡 Call Status: **{global_call_status["call_status"].capitalize()}**")
        
        if global_call_status["call_status"] == "busy":
            status_placeholder.write(f"📡 Call Status: **{global_call_status["call_status"].capitalize()}**")
            st.error("❌ Call Attempted! The recipient was busy. Please try again later.")
        
        if global_call_status["call_status"] == "failed":
            status_placeholder.write(f"📡 Call Status: **{global_call_status["call_status"].capitalize()}**")
            st.error("❌ Call Attempted! The call could not be completed due to an unknown issue. Please try again later.")

             
        if global_call_status["call_status"] == "completed":
            st.success("✅ Call Completed! Test results will be processed soon.")

            # Simulated Call Details
            call_length = '1.23'  # Call duration between 1-3 mins
            country = "PK"
            price = "6"  # Example price calculation

            # Display Call Details
            st.write("### Call Details")
            col1, col2, col3 = st.columns(3)
            col1.metric("📌 Country", agent_response.get("country", None))
            col2.metric("⏳ Call Length", f"{agent_response.get("call_length")} mins" if agent_response.get("call_length", False) else None)
            col3.metric("💰 Price", f"${agent_response.get("call_price")}" if agent_response.get("call_price", False) else None)

            # Score
            score = agent_response.get('score', False)
            if score:
                st.write("### Your Score")
                st.markdown(f"<h2 style='text-align: center; color: {'#4CAF50' if score >= 70 else '#F44336'}; pointer-events: none;'>{score}%</h2>", unsafe_allow_html=True)

            if "analysis" in agent_response and isinstance(agent_response["analysis"], list):
                st.write("### Question Analysis")
                data = {
                    "Question": [item["question"] for item in agent_response["analysis"]],
                    "Correct Answer": [item["correct_answer"] for item in agent_response["analysis"]],
                    "Your Answer": [item["user_answer"] for item in agent_response["analysis"]],
                    "Result": ["✅" if item["is_correct"] else "❌" for item in agent_response["analysis"]]
                 }

                df = pd.DataFrame(data)
                
                # st.table(df)
                st.dataframe(df, use_container_width=True)

            # Lead Generated Status
            if agent_response.get("lead_generated", None):
                st.write("### Customer Interested")
                if agent_response["lead_generated"] == "yes":
                    st.success("🎯 Customer Interested: **Yes**")
                else:
                    st.error("❌ Customer Interested: **No**")

    else:
        st.error("❌ Please enter a valid phone number and select a language.")
