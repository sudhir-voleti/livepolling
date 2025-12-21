import streamlit as st
import requests
import pandas as pd
import time

# ================== CONFIG ==================
# Replace these with your Supabase details
SUPABASE_URL = "https://wkzhfntozbnxibjhrnld.supabase.co"  # ← CHANGE
SUPABASE_KEY = "sb_publishable_ov70pw19lK7p7ihZm0xEyg_acLkNiiy"              # ← CHANGE

TABLE = "votes"
POLL_ID = "spotify_ad_test_round1"               # ← Change per poll/session

# Options for this poll (edit as needed)
OPTIONS = ["Option A", "Option B", "Option C"]   # 2–4 options work best

# Instructor password for reveal/analysis
INSTRUCTOR_PASSWORD = "secret2026"               # ← Change this!

# ===========================================

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

st.set_page_config(page_title="Live Poll", layout="centered")
st.title("🔥 Live Classroom Poll")

st.markdown(f"**Poll:** {POLL_ID.replace('_', ' ').title()}")

# Display options with sample content (customize per use)
cols = st.columns(len(OPTIONS))
sample_content = {
    "Option A": "🎧 **Upgrade now** – Hi-res audio + exclusive playlists for true music lovers.",
    "Option B": "🎶 **Try Ultra Premium free for 1 month** – Better sound, no ads, offline downloads.",
    "Option C": "🔥 **Limited time: 30% off first year** – For students and superfans only."
}

for i, opt in enumerate(OPTIONS):
    with cols[i]:
        st.subheader(opt)
        st.write(sample_content.get(opt, "Great choice!"))

# Voting
st.divider()
st.header("Cast Your Vote")

selected_option = st.radio("Choose one:", OPTIONS, horizontal=True)
comment = st.text_area("Optional: Why did you choose this? (or any feedback)")

if st.button("Submit Vote", type="primary"):
    data = {
        "poll_id": POLL_ID,
        "option": selected_option,
        "comment": comment if comment.strip() else None
    }
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/{TABLE}",
        headers=headers,
        json=data
    )
    if response.status_code == 201:
        st.success("Vote recorded! 🎉")
        st.rerun()
    else:
        st.error("Error submitting vote. Try again.")

# Live Results
st.divider()
st.header("📊 Live Results")

placeholder = st.empty()
auto_refresh = st.checkbox("Auto-refresh every 4 seconds", value=True)

while True:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/{TABLE}?poll_id=eq.{POLL_ID}&select=option,comment",
        headers=headers
    )
    if resp.status_code == 200:
        votes = resp.json()
        if votes:
            df = pd.DataFrame(votes)
            counts = df['option'].value_counts().reindex(OPTIONS, fill_value=0)
            
            with placeholder.container():
                st.bar_chart(counts)
                st.write(f"**Total votes:** {len(votes)}")
                
                # Show comments (latest 10)
                if not df['comment'].dropna().empty:
                    st.subheader("Recent Comments")
                    recent_comments = df[['option', 'comment']].dropna(subset=['comment']).tail(10)
                    st.dataframe(recent_comments, use_container_width=True)
        else:
            with placeholder.container():
                st.info("No votes yet — be the first!")
    
    if not auto_refresh:
        break
    time.sleep(4)
    st.rerun()

# Instructor Section
st.divider()
with st.expander("👩‍🏫 Instructor Controls"):
    password = st.text_input("Password", type="password")
    if password == INSTRUCTOR_PASSWORD:
        st.success("Access granted")
        
        if st.button("Clear All Votes (Reset Poll)"):
            delete_resp = requests.delete(
                f"{SUPABASE_URL}/rest/v1/{TABLE}?poll_id=eq.{POLL_ID}",
                headers=headers
            )
            if delete_resp.status_code == 204:
                st.success("All votes cleared!")
                st.rerun()
        
        st.markdown("### Reveal Suggestions")
        st.write("- Option A = AI-generated formal ad")
        st.write("- Option B = Human-written emotional ad")
        st.write("- Option C = Discount-focused ad")
        
        # Quick AI analysis of comments (using Gemini via st.text_input simulation)
        if st.button("Summarize Comments with AI (paste into Gemini)"):
            comments = [row['comment'] for row in votes if row['comment']]
            if comments:
                summary_prompt = "Summarize key themes from these student comments:\n" + "\n".join(comments)
                st.code(summary_prompt, language="text")
                st.info("Copy-paste this into Gemini/ChatGPT for instant summary!")
    elif password:
        st.error("Wrong password")
