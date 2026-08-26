import streamlit as st
import requests

BASE_URL = "http://localhost:8000"  # Backend endpoint

st.set_page_config(
    page_title="🌍 Travel Planner Agentic Application",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.title("🌍 Travel Planner Agentic Application")
st.caption("How can I help you plan a trip? Let me know where you want to visit.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render existing history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("e.g. Plan a trip to Goa for 5 days")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Bot is thinking..."):
        try:
            response = requests.post(f"{BASE_URL}/query", json={"question": user_input})
        except requests.exceptions.RequestException as e:
            st.error(f"Could not reach the backend: {e}")
            st.stop()

    if response.status_code == 200:
        data = response.json()
        answer = data.get("answer", "No answer returned.")
        saved_file = data.get("saved_file")

        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
            if saved_file:
                try:
                    with open(saved_file, "rb") as f:
                        st.download_button(
                            label="📥 Download this trip plan (.md)",
                            data=f,
                            file_name=saved_file.split("/")[-1],
                            mime="text/markdown",
                        )
                except FileNotFoundError:
                    pass
    else:
        st.error("Bot failed to respond: " + response.text)