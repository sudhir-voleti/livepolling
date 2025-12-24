import streamlit as st
import requests
import pandas as pd
import time
import plotly.express as px

# ==========================================
# 0. SETUP & CONFIG (Logic Engine)
# ==========================================
SUPABASE_URL = "https://wkzhfntozbnxibjhrnld.supabase.co"
SUPABASE_KEY = "sb_publishable_ov70pw19lK7p7ihZm0xEyg_acLkNiiy"
INSTRUCTOR_PASSWORD = "Aitp@2026"
headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

# ==========================================
# 1. LECTURE CONTENT (JSON-Style Config)
# ==========================================
LECTURE_CONTENT = {
    "Pulse Check: Strategic Risks": {
        "id": "spotify_risk_q1",
        "type": "SINGLE",
        "content": "Whose internal perspective currently poses the most significant strategic risk to Spotify?",
        "options": ["Debra (Superfans)", "David (Mass Volume)", "Marcus (Artist Safety)", "Other"],
        "correct": None
    },
    "Feature Pillar Selection": {
        "id": "spotify_multi_q2",
        "type": "MULTI",
        "content": "Select ALL features you believe are 'Non-Negotiable' for a $20 tier:",
        "options": ["Lossless Audio", "AI Remixing", "Ticket Access", "Exclusive Content"],
        "correct": ["Lossless Audio", "Ticket Access"]
    },
    "The Strategy Pivot (Justification)": {
        "id": "spotify_text_q3",
        "type": "TEXT",
        "content": "Explain your 'Hybrid' solution: How do you satisfy both Audiophiles and Families?",
        "options": [],
        "correct": None
    }
}

# ==========================================
# 2. ANALYSIS FUNCTIONS (The Dispatcher)
# ==========================================

def analyze_single(df, config):
    counts = df['option'].value_counts().reindex(config['options'], fill_value=0).reset_index()
    counts.columns = ['Choice', 'Votes']
    chart_choice = st.radio("Toggle View:", ["Bar", "Pie"], horizontal=True, key=f"chart_{config['id']}")
    if chart_choice == "Bar":
        fig = px.bar(counts, x='Votes', y='Choice', orientation='h', color='Choice', text_auto=True)
    else:
        fig = px.pie(counts, values='Votes', names='Choice', hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

def analyze_multi(df, config):
    st.write("### Exact Combination Match Rate")
    combos = df['option'].value_counts().reset_index()
    combos.columns = ['Combination Chosen', 'Student Count']
    st.table(combos)
    if config['correct']:
        target = ", ".join(sorted(config['correct']))
        matches = len(df[df['option'] == target])
        st.success(f"✅ **Target Combo:** {target} ({matches} students matched)")

def analyze_text(df, config):
    df['Word Count'] = df['comment'].apply(lambda x: len(str(x).split()))
    df = df.sort_values('Word Count', ascending=False)
    st.write("### Submissions (Sorted by Effort/CP Marks)")
    st.dataframe(df[['student_name', 'comment', 'Word Count']], use_container_width=True)

# ==========================================
# 3. MAIN APP & VOTING UI
# ==========================================
st.set_page_config(page_title="Spotify Strategic Engine", layout="wide")
st.title("🎧 Spotify Music Pro: Strategic Launch Engine")

selected_label = st.selectbox("Select Activity:", list(LECTURE_CONTENT.keys()))
q_cfg = LECTURE_CONTENT[selected_label]
poll_id = q_cfg['id']
lock_key = f"voted_{poll_id}"

# State Initialization
if lock_key not in st.session_state: st.session_state[lock_key] = False
if 'unlocked' not in st.session_state: st.session_state.unlocked = False

# Voting UI
with st.container(border=True):
    st.subheader(q_cfg['content'])
    pgid = st.text_input("Enter PGID (Mandatory for CP Marks)", key=f"pgid_{poll_id}")
    
    if q_cfg['type'] == "SINGLE":
        choice = st.radio("Pick one strategy:", q_cfg['options'], key=f"val_{poll_id}")
        final_val = choice
    elif q_cfg['type'] == "MULTI":
        choice = st.multiselect("Select all that apply:", q_cfg['options'], key=f"val_{poll_id}")
        final_val = ", ".join(sorted(choice))
    else:
        final_val = "TEXT_MODE"

    comment = st.text_area("Justification (Mandatory - Min 20 chars)", key=f"comm_{poll_id}")
    
    # Validation Logic
    is_ready = len(pgid.strip()) > 0 and len(comment.strip()) >= 20 and final_val != ""

    if st.session_state[lock_key]:
        st.warning("✅ Vote recorded for this activity.")
    else:
        if st.button("Submit to Database", type="primary", disabled=not is_ready):
            payload = {"poll_id": poll_id, "student_name": pgid, "option": final_val, "comment": comment}
            resp = requests.post(f"{SUPABASE_URL}/rest/v1/votes", headers=headers, json=payload)
            if resp.status_code in [200, 201]:
                st.session_state[lock_key] = True
                st.success("Vote cast!")
                time.sleep(1); st.rerun()

# ==========================================
# 4. INSTRUCTOR REVEAL & ANALYSIS
# ==========================================
st.divider()
with st.expander("👩‍🏫 Instructor Controls"):
    pwd = st.text_input("Admin Password", type="password")
    if pwd == INSTRUCTOR_PASSWORD:
        c1, c2 = st.columns(2)
        if c1.button("REVEAL ALL RESULTS", use_container_width=True): st.session_state.unlocked = True
        if c2.button("HIDE RESULTS", use_container_width=True): st.session_state.unlocked = False
        if st.button("Reset Current Question Data"):
            requests.delete(f"{SUPABASE_URL}/rest/v1/votes?poll_id=eq.{poll_id}", headers=headers)
            st.rerun()

if st.session_state.unlocked:
    st.divider()
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/votes?poll_id=eq.{poll_id}&select=*", headers=headers)
    if resp.status_code == 200 and resp.json():
        df = pd.DataFrame(resp.json())
        
        # CSV Download for Students
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Results (CSV)", data=csv, file_name=f"{poll_id}_results.csv")
        
        # DISPATCHER
        if q_cfg['type'] == "SINGLE": analyze_single(df, q_cfg)
        elif q_cfg['type'] == "MULTI": analyze_multi(df, q_cfg)
        elif q_cfg['type'] == "TEXT": analyze_text(df, q_cfg)
    else:
        st.info("Awaiting submissions for this specific question...")
