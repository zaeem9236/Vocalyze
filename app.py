import streamlit as st
import time
import random
import pandas as pd

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
        
        # Simulating real-time call status updates
        for status in call_statuses:
            time.sleep(random.randint(1, 3))  # Simulating status change delay
            status_placeholder.write(f"📡 Call Status: **{status}**")

        if status == "Completed":
            st.success("✅ Call Completed! Test results will be processed soon.")

            # Simulated Call Details
            call_length = round(random.uniform(1.0, 3.0), 2)  # Call duration between 1-3 mins
            country = "PK"
            price = round(call_length * 3.72, 2)  # Example price calculation

            # Display Call Details
            st.write("### Call Details")
            col1, col2, col3 = st.columns(3)
            col1.metric("📌 Country", country)
            col2.metric("⏳ Call Length", f"{call_length} mins")
            col3.metric("💰 Price", f"${price}")

            # Simulated Score
            score = random.randint(40, 90)  # Random score between 40% to 90%
            st.write("### Your Score")
            st.markdown(f"<h2 style='text-align: center; color: #4CAF50;'>{score}%</h2>", unsafe_allow_html=True)

            # Simulated Questions Table
            st.write("### Question Analysis")
            data = {
                "Question": ["What is 2 + 2?", "Capital of France?", "Sun rises from?", "Largest ocean?"],
                "Correct Answer": ["4", "Paris", "East", "Pacific"],
                "Your Answer": ["4", "Paris", "West", "Atlantic"]
            }

            df = pd.DataFrame(data)
            st.table(df)

            # Lead Generated
            lead_generated = random.choice(["Yes", "No"])
            st.write("### Customer Interested")
            
            if lead_generated == "Yes":
                st.success("🎯 Customer Interested: **Yes**")
            else:
                st.error("❌ Customer Interested: **No**")

    else:
        st.error("❌ Please enter a valid phone number and select a language.")
