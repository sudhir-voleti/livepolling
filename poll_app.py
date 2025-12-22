import streamlit as st
import requests

st.title("Connection Test 🛠️")

# 1. Check Secrets
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    st.success("✅ Secrets found in Streamlit Cloud!")
except Exception as e:
    st.error("❌ Secrets missing! Go to Streamlit Settings > Secrets.")
    st.stop()

# 2. Check Connection & RLS
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

st.write("Attempting to talk to Supabase...")
# This tries to fetch data from your 'votes' table
resp = requests.get(f"{url}/rest/v1/votes?select=*", headers=headers)

if resp.status_code == 200:
    st.success("✅ Connection Successful!")
    st.write("Data found in table:", resp.json())
elif resp.status_code == 401:
    st.error("❌ Unauthorized: Your SUPABASE_KEY is likely incorrect.")
elif resp.status_code == 403:
    st.error("❌ RLS Blocked: You need to enable the SELECT policy for 'anon'.")
else:
    st.error(f"❌ Error {resp.status_code}")
    st.write(resp.text)
