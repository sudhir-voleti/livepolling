import streamlit as st
import requests
import pandas as pd
import time

# ================== CONFIG (Hardcoded for now - change to secrets later if desired) ==================
SUPABASE_URL = "https://wkzhfntozbnxibjhrnld.supabase.co"
SUPABASE_KEY = "sb_publishable_ov70pw19lK7p7ihZm0xEyg_acLkNiiy"
TABLE = "votes"

# ==============================================================================================

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

st.set_page_config(page_title="Classroom Activities", layout="wide")
st.title("🔥 Live Classroom Activities")

# Initialize session state for duplicate prevention
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# Activity Selector
mode_options = [
    "1. MCQ: Segment Attractiveness",
    "2. Open Feedback: Personas",
    "3. A/B Ad Vote (Coming Soon)"
]
mode = st.selectbox("Select Current Activity:", mode_options, index=0)

# Generate poll_id from selection
poll_id = mode.lower().replace(" ", "_").replace(":", "").replace(".", "").replace("(coming_soon)", "ab_vote")

st.markdown(f"**Current Activity:** `{poll_id}`")

# Activity configurations
configs = {
    "1_mcq_segment_attractiveness": {
        "question": "Which customer segment is most attractive for Spotify Ultra Premium launch?",
        "options": [
            "A: Budget-conscious students",
            "B: Family plan sharers",
            "C: Audiophiles / music superfans",
            "D: Casual free-tier users"
        ],
        "type": "mcq"
    },
    "2_open_feedback_personas": {
        "question": "What do you think of the AI-generated personas? Strengths? Improvements? Surprises?",
        "options": None,
        "type": "text"
    },
    "3_ab_vote": {
        "question": "Which ad variant do you prefer?",
        "options": ["Ad A", "Ad B"],
        "type": "mcq"
    }
}

config = configs.get(poll_id, configs["1_mcq_segment_attractiveness"])

st.divider()
st.header(config["question"])

if config["type"] == "mcq":
    cols = st.columns(2)
    for i, opt in enumerate(config["options"]):
        with cols[i % 2]:
            st.write(f"**{opt}**")

# Student identification (required)
st.divider()
st.subheader("Your Identity")
student_name = st.text_input("Enter your Name or Student ID (required):")

# Submission
st.divider()
st.header("Submit Your Response")

if config["type"] == "mcq":
    selected_option = st.radio("Your choice:", config["options"], horizontal=False)
else:
    selected_option = "Open Feedback"
    st.info("Share your detailed thoughts below.")

comment = st.text_area("Additional comments (optional for MCQ, encouraged for feedback):")

if st.button("Submit Response", type="primary"):
    if not student_name.strip():
        st.error("Please enter your name or ID.")
    elif st.session_state.submitted:
        st.warning("You have already submitted for this activity. Thank you!")
    else:
        data = {
            "poll_id": poll_id,
            "student_name": student_name.strip(),
            "option": selected_option,
            "comment": comment.strip() if comment.strip() else None
        }
        response = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLE}", headers=headers, json=data)
        if response.status_code == 201:
            st.success(f"Thank you, {student_name}! Your response is recorded.")
            st.session_state.submitted = True
            st.rerun()
        else:
            st.error("Submission failed. Check connection or keys.")

# Live Results
st.divider()
st.header("📊 Live Results")

placeholder = st.empty()
auto_refresh = st.checkbox("Auto-refresh every 5 seconds", value=True)

while True:
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE}?poll_id=eq.{poll_id}", headers=headers)
    if resp.status_code == 200:
        votes = resp.json()
        if votes:
            df = pd.DataFrame(votes)
            with placeholder.container():
                if config["type"] == "mcq":
                    counts = df['option'].value_counts()
                    st.bar_chart(counts)
                st.write(f"**Total responses: {len(df)}**")
                st.subheader("Individual Responses")
                display_df = df[['student_name', 'option', 'comment']].sort_values("student_name")
                st.dataframe(display_df, use_container_width=True)
        else:
            with placeholder.container():
                st.info("No responses yet — waiting for the class!")
    else:
        with placeholder.container():
            st.error(f"Supabase error {resp.status_code} — check keys/URL/table")
    if not auto_refresh:
        break
    time.sleep(5)
    st.rerun()
