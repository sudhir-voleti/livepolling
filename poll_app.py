import streamlit as st
import requests
import pandas as pd
import time
import plotly.express as px

# ==========================================
# 1. SETUP & CONFIG
# ==========================================
SUPABASE_URL = "https://wkzhfntozbnxibjhrnld.supabase.co"
SUPABASE_KEY = "sb_publishable_ov70pw19lK7p7ihZm0xEyg_acLkNiiy"
INSTRUCTOR_PASSWORD = "Aitp@2026"

LECTURE_DATA = {
    "Pulse Check: Internal Alignment": {
        "id": "spotify_pulse_q1",
        "options": ["Debra (Superfans)", "David (Mass Volume)", "Marcus (Artist Safety)", "None / Other"],
        "content": "Whose internal perspective currently poses the most significant strategic risk to Spotify?"
    },
    "Initial Strategy (Intuition)": {
        "id": "spotify_strat_initial",
        "options": ["Superfan Elite ($19.99)", "Mass Utility Add-on", "The Two-Tier Hybrid", "Other"],
        "content": "Based on the internal stakeholder arguments only: Which strategy do you lean toward?"
    },
    "Final Recommendation (Evidence-Based)": {
        "id": "spotify_strat_final",
        "options": ["Superfan Elite ($19.99)", "Mass Utility Add-on", "The Two-Tier Hybrid", "Other"],
        "content": "After the NLM VoC analysis: Which strategy are you now recommending to Sarah Jenkins?"
    }
}

headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

st.set_page_config(page_title="Spotify Case Study Poll", layout="wide")
st.title("Spotify Music Pro: Strategic Launch Poll")

# ==========================================
# 2. ACTIVITY SELECTOR
# ==========================================
selected_act_name = st.selectbox("Current Discussion Question:", list(LECTURE_DATA.keys()))
current_act = LECTURE_DATA[selected_act_name]

# ==========================================
# 3. STUDENT VOTING UI
# ==========================================
with st.expander("Cast Your Vote", expanded=True):
    st.write(current_act["content"])
    
    # Using vertical layout for radio buttons
    choice = st.radio(
        "Select your strategic choice:", 
        current_act["options"], 
        horizontal=False, 
        key=f"r_{current_act['id']}"
    )
    
    moniker = st.text_input("Name / Group Number", key=f"n_{current_act['id']}")
    comment = st.text_area("Justification (Optional):", key=f"c_{current_act['id']}")

    if st.button("Submit Vote", type="primary"):
        if not moniker: 
            st.error("Identification is required to submit.")
        else:
            payload = {"poll_id": current_act["id"], "option": choice, "comment": comment, "student_name": moniker}
            resp = requests.post(f"{SUPABASE_URL}/rest/v1/votes", headers=headers, json=payload)
            if resp.status_code in [200, 201]:
                st.success("Vote submitted successfully.")
                time.sleep(1)
                st.rerun()

# ==========================================
# 4. RESULTS SECTION
# ==========================================
results_container = st.container()

# ==========================================
# 5. INSTRUCTOR PANEL
# ==========================================
st.divider()
if 'unlocked' not in st.session_state: st.session_state.unlocked = False

with st.expander("Instructor Panel"):
    pwd = st.text_input("Admin Password", type="password")
    if pwd == INSTRUCTOR_PASSWORD:
        colA, colB = st.columns(2)
        with colA:
            if st.button("REVEAL RESULTS", use_container_width=True): st.session_state.unlocked = True
        with colB:
            if st.button("HIDE RESULTS", use_container_width=True): st.session_state.unlocked = False
        
        if st.button("Reset Current Activity"):
            requests.delete(f"{SUPABASE_URL}/rest/v1/votes?poll_id=eq.{current_act['id']}", headers=headers)
            st.rerun()

# ==========================================
# 6. RENDER RESULTS & CSV DOWNLOAD
# ==========================================
if st.session_state.unlocked:
    with results_container:
        @st.fragment(run_every=5)
        def show_results():
            resp = requests.get(f"{SUPABASE_URL}/rest/v1/votes?poll_id=eq.{current_act['id']}&select=*", headers=headers)
            if resp.status_code == 200 and resp.json():
                df = pd.DataFrame(resp.json())
                
                # CSV Download functionality for student analysis
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Raw Data (CSV) for NLM Analysis",
                    data=csv,
                    file_name=f"spotify_results_{current_act['id']}.csv",
                    mime="text/csv",
                )

                counts = df['option'].value_counts().reindex(current_act['options'], fill_value=0).reset_index()
                counts.columns = ['Option', 'Votes']
                
                chart_choice = st.radio("Chart Type:", ["Bar", "Pie"], horizontal=True)
                
                if chart_choice == "Bar":
                    fig = px.bar(counts, x='Votes', y='Option', orientation='h', color='Option', text_auto=True)
                    fig.update_layout(yaxis={'categoryorder':'array', 'categoryarray':current_act['options']})
                else:
                    fig = px.pie(counts, values='Votes', names='Option', hole=0.4)
                
                st.plotly_chart(fig, use_container_width=True)
                
                if not df.dropna(subset=['comment']).empty:
                    st.write("Participant Commentary:")
                    st.dataframe(df[['student_name', 'option', 'comment']].dropna(subset=['comment']), use_container_width=True)
            else: 
                st.info("Awaiting submissions...")
        show_results()
