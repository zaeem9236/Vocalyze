import streamlit as st
import time
import random
import pandas as pd
from dotenv import load_dotenv
from agent import agent
import os, re
load_dotenv()

global_call_status = {"call_status": ""}

    
# App Title
st.title("📞 Vocalyze - Agentic AI-Driven Spoken Aptitude Test")

# Number input field
phone_number = st.text_input("Enter your phone number", placeholder="+1234567890", autocomplete="off")
if phone_number:
    if not re.match(r'^\+?\d*$', phone_number):
        st.error("Please enter only numbers with an optional '+' at the start.")
        
# Language selection
language = st.selectbox("Select Language", ["English"])

# Call status placeholder
status_placeholder = st.empty()

# Call statuses to simulate real-time updates
call_statuses = ["Queue", "Dialing", "Busy", "Ongoing", "Failed", "Completed"]

import threading
# Start Call button
if st.button("Start Call"):
    if phone_number and language:
        st.success(f"📞 Calling {phone_number} for an aptitude test in {language}...")
        global_call_status["call_status"] = "queue"
        status_placeholder.write(f"📡 Call Status: **{global_call_status["call_status"].capitalize()}**")
        agent_response = agent(phone_number, "2", "en", global_call_status)    

        if global_call_status["call_status"] == "denied":
            status_placeholder.write(f"📡 Call Status: **{global_call_status["call_status"].capitalize()}**")
            st.warning("❌ Limit Reached! You have reached your limit for this number. Please try with a different number.")
        
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


            # Display Call Details
            st.write("### Call Details")
            col1, col2, col3 = st.columns(3)
            col1.metric("📌 Country", agent_response.get("country", None))
            col2.metric("⏳ Call Length", f"{round(float(agent_response.get("call_length")), 2)} mins" if agent_response.get("call_length", False) else None)
            col3.metric("💰 Price", f"$ {agent_response.get("price")}" if agent_response.get("price", False) else None)

            # Score
            score = agent_response.get('score', False)
            if score:
                st.write("### Your Score")
                st.markdown(f"<h2 style='text-align: center; color: {'#4CAF50' if float(score) >= 70 else '#F44336'}; pointer-events: none;'>{int(float(score))} %</h2>", unsafe_allow_html=True)

            if "analysis" in agent_response and isinstance(agent_response["analysis"], list):
                st.write("### Question Analysis")
                data = {
                    "Question": [item["question"] for item in agent_response["analysis"]],
                    "Correct Answer": [item["correct_answer"] for item in agent_response["analysis"]],
                    "Your Answer": [item["user_answer"] for item in agent_response["analysis"]],
                    "Result": ["✅" if item["is_correct"] == "True" else "❌" for item in agent_response["analysis"]]
                 }

                df = pd.DataFrame(data)
                
                st.dataframe(df, use_container_width=True)

            # Lead Generated Status
            if agent_response.get("lead_generated", None):
                st.write("### Customer Interested")
                if agent_response["lead_generated"] == "True" or agent_response["lead_generated"] == True:
                    st.success("🎯 Customer Interested: **Yes**")
                else:
                    st.error("❌ Customer Interested: **No**")

    else:
        st.error("❌ Please enter a valid phone number and select a language.")
