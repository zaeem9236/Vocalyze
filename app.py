import streamlit as st
import time
import random
import pandas as pd
from dotenv import load_dotenv
from agent import agent
import os, re, uuid
load_dotenv()

if "random_uuid" not in st.session_state or st.session_state.get("is_new_session", True):
    st.session_state["random_uuid"] = str(uuid.uuid4())
    st.session_state["is_new_session"] = False
    
# App Title
st.title("📞 Vocalyze - Agentic AI-Driven Spoken Aptitude Test")

# Number input field
phone_number = st.text_input("Enter your phone number", placeholder="+9230012345678", autocomplete="off")
if phone_number:
    if not re.match(r'^\+?\d*$', phone_number):
        st.error("Please enter only numbers with an optional '+' at the start.")
        
# Language selection
language = st.selectbox("Select language", ["English"])

# Number of questions selection
num_questions = st.selectbox("Choose number of questions ", ['2', '4'])


# Call status placeholder
if "call_status" not in st.session_state:
    st.session_state.call_status = ""
status_placeholder = st.empty()
message_placeholder = st.empty()
def status_updater(status):
    status_placeholder.write(f"📡 Call Status: **{status.capitalize().replace("_", " ")}**")
    if status == "queue":
        message_placeholder.success(f"📞 Calling {phone_number} for an aptitude test in {language}...")
    if status == "failed":
        message_placeholder.error("❌ Call Attempted! The call could not be completed due to an unknown issue. Please try again later.")
    if status == "busy":
        message_placeholder.error("❌ Call Attempted! The recipient was busy. Please try again later.")
    if status == "denied":
        message_placeholder.warning("🚫 Limit Reached! You have reached your limit for this number. Please try with a different number.")
    if status == "in_progress":
        message_placeholder.info("📢 Aptitude Test in Progress! Please wait 2 minutes after the test ends. Do not refresh the page—your score will appear soon!")
    if status == "completed":
        message_placeholder.success("✅ Call Completed! Test results will be processed soon.")
        

# Start Call button
if "button_disabled" not in st.session_state:
    st.session_state.button_disabled = False  # Initially enabled
if st.button("Start Call", disabled=st.session_state.button_disabled, on_click=lambda: setattr(st.session_state, "button_disabled", True)):
    if phone_number and language:
        agent_response = agent(phone_number, num_questions, "en", st.session_state.random_uuid, status_updater)    
           
        if len(agent_response) != 0:
            # st.success("✅ Call Completed! Test results will be processed soon.")


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
