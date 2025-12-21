import streamlit as st
import requests
import pandas as pd
import time

# ================== HARDCODED CONFIG (Working Version) ==================
SUPABASE_URL = "https://wkzhfntozbnxibjhrnld.supabase.co"
SUPABASE_KEY = "sb_publishable_ov70pw19lK7p7ihZm0xEyg_acLkNiiy"
TABLE = "votes"

# ======================================================================

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

st.set_page_config(page_title="Classroom Poll", layout="centered")
st.title("Live Classroom Poll")

# Activity dropdown
activity = st.selectbox(
    "Select Activity",
    ["1. MCQ: Which segment is most attractive?", "2. Open Feedback on Personas"]
)

# Generate poll_id from selection
if "MCQ" in activity:
    poll_id = "mcq_segment"
    question = "Which customer segment is most attractive for Spotify Ultra Premium?"
    options = ["A: Budget students", "B: Family sharers", "C: Audiophiles", "D: Casual listeners"]
    is_mcq = True
else:
    poll_id = "feedback_personas"
    question = "What do you think of the AI-generated personas? Strengths? Improvements?"
    options = None
    is_mcq = False

st.header(question)

# Display options for MCQ
if is_mcq:
    for opt in options:
        st.write(f"**{opt}**")

# Student name
st.divider()
student_name = st.text_input("Your Name or ID (required)")

# Response input
if is_mcq:
    choice = st.radio("Your choice", options)
else:
    choice = None
    st.text_area("Your feedback", height=150, key="feedback_text")

comment = st.text_input("Optional additional comment")

if st.button("Submit"):
    if not student_name.strip():
        st.error("Please enter your name/ID")
    else:
        data = {
            "poll_id": poll_id,
            "student_name": student_name.strip(),
            "option": choice if is_mcq else "Open feedback
