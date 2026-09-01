import streamlit as st
import requests
import uuid

BASE_URL = "http://localhost:8000"  # Backend endpoint

st.set_page_config(
    page_title="Travel Planner Agentic Application",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---- Session state setup ----
if "chats" not in st.session_state:
    # chats: dict of thread_id -> {"title": str, "messages": [...]}
    first_id = str(uuid.uuid4())
    st.session_state.chats = {
        first_id: {"title": "New chat", "messages": []}
    }
    st.session_state.active_chat = first_id

# ---- Sidebar ----
with st.sidebar:
    st.header("💬 Chats")

    if st.button("➕ New chat", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.chats[new_id] = {"title": "New chat", "messages": []}
        st.session_state.active_chat = new_id
        st.rerun()

    st.divider()

    # list chats, most recently created first
    for thread_id in reversed(list(st.session_state.chats.keys())):
        chat = st.session_state.chats[thread_id]
        label = chat["title"]
        is_active = thread_id == st.session_state.active_chat
        if st.button(
            ("🟢 " if is_active else "") + label,
            key=f"chat_{thread_id}",
            use_container_width=True,
        ):
            st.session_state.active_chat = thread_id
            st.rerun()

st.title("🌍 Travel Planner Agentic Application")
st.caption("How can I help you plan a trip? Let me know where you want to visit.")

active_id = st.session_state.active_chat
active_chat = st.session_state.chats[active_id]

for msg in active_chat["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("e.g. Plan a trip to Goa for 5 days")

if user_input:
    # first message in a chat becomes its title
    if active_chat["title"] == "New chat":
        active_chat["title"] = user_input[:40] + ("..." if len(user_input) > 40 else "")

    active_chat["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Bot is thinking..."):
        try:
            response = requests.post(
                f"{BASE_URL}/query",
                json={"question": user_input, "thread_id": active_id},
            )
        except requests.exceptions.RequestException as e:
            st.error(f"Could not reach the backend: {e}")
            st.stop()

    if response.status_code == 200:
        data = response.json()
        answer = data.get("answer", "No answer returned.")
        saved_file = data.get("saved_file")
        saved_pdf = data.get("saved_pdf")

        active_chat["messages"].append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)

            col1, col2 = st.columns(2)
            if saved_file:
                try:
                    with open(saved_file, "rb") as f:
                        col1.download_button(
                            "📥 Download Markdown", data=f,
                            file_name=saved_file.split("/")[-1], mime="text/markdown",
                            key=f"md_{active_id}_{len(active_chat['messages'])}",
                        )
                except FileNotFoundError:
                    pass
            if saved_pdf:
                try:
                    with open(saved_pdf, "rb") as f:
                        col2.download_button(
                            "📄 Download PDF", data=f,
                            file_name=saved_pdf.split("/")[-1], mime="application/pdf",
                            key=f"pdf_{active_id}_{len(active_chat['messages'])}",
                        )
                except FileNotFoundError:
                    pass
        st.rerun()
    else:
        st.error("Bot failed to respond: " + response.text)