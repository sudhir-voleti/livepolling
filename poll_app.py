import streamlit as st
import requests
import pandas as pd
import time
import plotly.express as px

# ==========================================
# 1. SETUP & CONFIG (Hardcoded for Class)
# ==========================================
SUPABASE_URL = "https://wkzhfntozbnxibjhrnld.supabase.co"
SUPABASE_KEY = "sb_publishable_ov70pw19lK7p7ihZm0xEyg_acLkNiiy"
INSTRUCTOR_PASSWORD = "Aitp@2026"

# Centralized Lecture Data
LECTURE_DATA = {
    "Pulse Check: Internal Alignment": {
        "id": "spotify_pulse_q1",
        "options": ["Debra (Superfans)", "David (Mass Volume)", "Marcus (Artist Safety)", "None / Other"],
        "content": "Whose internal perspective currently poses the most significant strategic risk to Spotify?"
    },
    "Final Recommendation": {
        "id": "spotify_final_q2",
        "options": ["Superfan Elite ($19.99)", "Mass Utility Add-on", "The Two-Tier Hybrid", "Other / See Comments"],
        "content": "After group discussion: Which pricing architecture are you recommending to the CPO?"
    },
    "The AI Guardrail": {
        "id": "spotify_ai_q3",
        "options": ["Full Permission", "Artist Opt-In Only", "Revenue-Share Model", "Ban AI Tools"],
        "content": "How should Spotify deploy AI Remix tools to maximize engagement while protecting artist trust?"
    }
}

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

st.set_page_config(page_title="Spotify Case Study Poll", layout="wide")

# ==========================================
# 2. ACTIVITY SELECTOR
# ==========================================
st.title("🎧 Spotify Music Pro: Strategic Launch Poll")
selected_act_name = st.selectbox("Select Current Discussion Question:", list(LECTURE_DATA.keys()))
current_act = LECTURE_DATA[selected_act_name]

# ==========================================
# 3. STUDENT VOTING UI
# ==========================================
with st.container(border=True):
    st.header(selected_act_name)
    st.info(current_act["content"])
    
    col1, col2 = st.columns([1, 2])
    with col1:
        moniker = st.text_input("Your Name / Group #", placeholder="e.g. Group 4", key=f"n_{current_act['id']}")
    with col2:
        choice = st.radio("Your Strategic Choice:", current_act["options"], horizontal=True, key=f"r_{current_act['id']}")
    
    comment = st.text_area("Justification / Open Text (Optional):", placeholder="Why did you choose this?", key=f"c_{current_act['id']}")

    if st.button("Submit Vote", type="primary", key=f"b_{current_act['id']}"):
        if not moniker:
            st.error("Please enter a name or group number!")
        else:
            payload = {
                "poll_id": current_act["id"],
                "option": choice,
                "comment": comment,
                "student_name": moniker
            }
            resp = requests.post(f"{SUPABASE_URL}/rest/v1/votes", headers=headers, json=payload)
            if resp.status_code in [200, 201]:
                st.success(f"Success, {moniker}! Results will be revealed by the instructor.")
                time.sleep(1)
                st.rerun()

# ==========================================
# 4. INSTRUCTOR PANEL
# ==========================================
st.divider()
if 'unlocked' not in st.session_state:
    st.session_state.unlocked = False

with st.expander("Instructor Panel (Reveal Controls)"):
    pwd = st.text_input("Admin Password", type="password")
    if pwd == INSTRUCTOR_PASSWORD:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("REVEAL RESULTS", use_container_width=True):
                st.session_state.unlocked = True
        with c2:
            if st.button("HIDE RESULTS", use_container_width=True):
                st.session_state.unlocked = False
        
        if st.button("🗑️ Reset This Activity"):
            requests.delete(f"{SUPABASE_URL}/rest/v1/votes?poll_id=eq.{current_act['id']}", headers=headers)
            st.rerun()

# ==========================================
# 5. INTERACTIVE RESULTS
# ==========================================
if st.session_state.unlocked:
    @st.fragment(run_every=5)
    def show_results():
        st.subheader(f"📊 Live Data: {selected_act_name}")
        resp = requests.get(f"{SUPABASE_URL}/rest/v1/votes?poll_id=eq.{current_act['id']}&select=*", headers=headers)
        
        if resp.status_code == 200 and resp.json():
            df = pd.DataFrame(resp.json())
            counts = df['option'].value_counts().reset_index()
            counts.columns = ['Option', 'Votes']
            
            # Interactive Chart Toggle
            chart_choice = st.radio("Toggle View:", ["Pie Chart", "Bar Chart"], horizontal=True)
            
            if chart_choice == "Pie Chart":
                fig = px.pie(counts, values='Votes', names='Option', hole=0.4, 
                             color_discrete_sequence=px.colors.qualitative.Prism)
            else:
                fig = px.bar(counts, x='Votes', y='Option', orientation='h', color='Option',
                             text_auto=True, color_discrete_sequence=px.colors.qualitative.Prism)
                fig.update_layout(yaxis={'categoryorder':'total ascending'})

            st.plotly_chart(fig, use_container_width=True)
            
            # Comments display
            if not df.dropna(subset=['comment']).empty:
                st.write("**Student Commentary:**")
                st.dataframe(df[['student_name', 'option', 'comment']].dropna(subset=['comment']), use_container_width=True)
        else:
            st.info("No votes yet. Waiting for students...")

    show_results()
else:
    st.info("Results are locked. They will be displayed once the debate concludes.")
