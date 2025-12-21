import streamlit as st
import requests
import pandas as pd
import time

# ================== CONFIG - CHANGE THESE ==================
# Use .streamlit/secrets.toml for real keys (see earlier instructions)
SUPABASE_URL = "https://wkzhfntozbnxibjhrnld.supabase.co"  # ← CHANGE
SUPABASE_KEY = "sb_publishable_ov70pw19lK7p7ihZm0xEyg_acLkNiiy"              # ← CHANGE
TABLE = "votes"

INSTRUCTOR_PASSWORD = "mysecret123"                # Change this!

# ===========================================================

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

st.set_page_config(page_title="Live Classroom Activities", layout="wide")
st.title("🔥 Live Classroom Activities")

# Mode Selector (for multiple activities in one app)
mode_options = [
    "1. MCQ: Segment Attractiveness",
    "2. Open Feedback: Personas"
]
mode = st.selectbox("Select Activity:", mode_options)

# Auto-generate poll_id from mode (keeps data separate)
poll_id = mode.lower().replace(" ", "_").replace(":", "").replace(".", "")

st.markdown(f"**Current Activity ID:** {poll_id}")

# Activity-Specific Config
if "MCQ" in mode:
    question = "Which customer segment is most attractive for Spotify Ultra Premium?"
    options = [
        "A: Budget-conscious students (price-sensitive, high volume)",
        "B: Family sharers (value group plans, medium spend)",
        "C: Audiophiles (willing to pay for hi-res, low volume)",
        "D: Casual listeners (ad-tolerant, hard to convert)"
    ]
    show_options = True
elif "Open Feedback" in mode:
    question = "What do you think of the generated personas? Share your thoughts, suggestions, or improvements."
    options = None  # No radio for open text
    show_options = False

# Display Question
st.divider()
st.header(question)

if show_options:
    cols = st.columns(2)  # Display options in grid for better layout
    for i, opt in enumerate(options):
        with cols[i % 2]:
            st.subheader(opt.split(":")[0])  # e.g., "A"
            st.write(opt.split(":")[1])      # Description

# Input Section
st.divider()
st.header("Your Response")

if show_options:
    selected_option = st.radio("Choose one:", [opt.split(":")[0] for opt in options], horizontal=True)
else:
    selected_option = "Open Feedback"  # Dummy for text-only

comment = st.text_area("Optional/Required Comment (share details here):")

if st.button("Submit Response", type="primary"):
    data = {
        "poll_id": poll_id,
        "option": selected_option if show_options else "N/A",
        "comment": comment if comment.strip() else None
    }
    response = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLE}", headers=headers, json=data)
    if response.status_code == 201:
        st.success("Submitted! 🎉")
        st.rerun()
    else:
        st.error(f"Error: {response.status_code} – Check Supabase.")

# Live Results
st.divider()
st.header("📊 Live Results")

placeholder = st.empty()
auto_refresh = st.checkbox("Auto-refresh every 4 seconds", value=True)

while True:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/{TABLE}?poll_id=eq.{poll_id}&select=option,comment",
        headers=headers
    )
    if resp.status_code == 200:
        votes = resp.json()
        if votes:
            df = pd.DataFrame(votes)
            if show_options:
                counts = df['option'].value_counts()
                with placeholder.container():
                    st.bar_chart(counts)
                    st.write(f"**Total responses:** {len(votes)}")
            else:
                with placeholder.container():
                    st.write(f"**Total responses:** {len(votes)}")
                    st.subheader("Collected Feedback")
                    feedback_df = df[['comment']].dropna().reset_index(drop=True)
                    st.dataframe(feedback_df, use_container_width=True)
        else:
            with placeholder.container():
                st.info("Waiting for first response...")
    if not auto_refresh:
        break
    time.sleep(4)
    st.rerun()

# Instructor Tools
st.divider()
with st.expander("👩‍🏫 Instructor Only"):
    pw = st.text_input("Password", type="password")
    if pw == INSTRUCTOR_PASSWORD:
        st.success("Authenticated")
        if st.button("🗑️ Clear Responses for This Activity"):
            del_resp = requests.delete(
                f"{SUPABASE_URL}/rest/v1/{TABLE}?poll_id=eq.{poll_id}",
                headers=headers
            )
            if del_resp.status_code == 204:
                st.success("Activity reset!")
                st.rerun()
        st.markdown("**Reveal/Notes:** Edit as needed for each activity.")
    elif pw:
        st.error("Incorrect password")
