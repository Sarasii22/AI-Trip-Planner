import streamlit as st
import requests
import uuid

BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Travel Planner AI",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------------- Custom styling ----------------
st.markdown("""
<style>
    /* Overall page padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 850px;
    }

    /* Sidebar background */
    section[data-testid="stSidebar"] {
        background-color: #00172D
    }
    section[data-testid="stSidebar"] * {
        color: #f5f5f5 !important;
    }
    section[data-testid="stSidebar"] button {
        background-color: rgba(11, 55, 69, 1) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 8px !important;
        text-align: left !important;
        margin-bottom: 4px;
    }
    section[data-testid="stSidebar"] button:hover {
        background-color: rgba(255,255,255,0.18) !important;
        border-color: #f2a541 !important;
    }

    /* New chat button — make it stand out */
    section[data-testid="stSidebar"] div[data-testid="stButton"]:first-of-type button {
        background-color: #0b3745 !important;
        color: #1a1a1a !important;
        font-weight: 600;
        border: none !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"]:first-of-type button:hover {
        background-color: #e0952f !important;
    }

    /* Chat bubbles */
    div[data-testid="stChatMessage"] {
        border-radius: 14px;
        padding: 4px 6px;
    }

    /* Title area */
    h1 {
        font-size: 2rem !important;
    }

    /* Download buttons */
    div[data-testid="stDownloadButton"] button {
        border-radius: 8px;
        border: 1px solid #0b5e59;
        color: #0b5e59;
        font-weight: 500;
    }
    div[data-testid="stDownloadButton"] button:hover {
        background-color: #0b5e59;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- Session state ----------------
if "chats" not in st.session_state:
    first_id = str(uuid.uuid4())
    st.session_state.chats = {first_id: {"title": "New chat", "messages": []}}
    st.session_state.active_chat = first_id

# ---------------- Sidebar ----------------
with st.sidebar:
    st.markdown("## 🌍 Travel Planner")
    st.caption("AI-powered trip planning")

    if st.button("➕  New chat", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.chats[new_id] = {"title": "New chat", "messages": []}
        st.session_state.active_chat = new_id
        st.rerun()

    st.markdown("---")
    st.markdown("**Recent chats**")

    chat_ids = list(st.session_state.chats.keys())
    if len(chat_ids) == 1 and st.session_state.chats[chat_ids[0]]["title"] == "New chat":
        st.caption("No chats yet — start planning below!")
    else:
        for thread_id in reversed(chat_ids):
            chat = st.session_state.chats[thread_id]
            is_active = thread_id == st.session_state.active_chat
            icon = "🟢" if is_active else "💬"
            if st.button(f"{icon}  {chat['title']}", key=f"chat_{thread_id}", use_container_width=True):
                st.session_state.active_chat = thread_id
                st.rerun()

    st.markdown("---")
    st.caption("Built with LangGraph · FastAPI · Streamlit")

# ---------------- Main chat area ----------------
active_id = st.session_state.active_chat
active_chat = st.session_state.chats[active_id]

st.title("🌍 Travel Planner")
st.caption("Tell me where you want to go, and I'll build you a complete trip plan.")

# Empty state — friendly starter prompts
if not active_chat["messages"]:
    st.markdown("#### Try asking:")
    example_cols = st.columns(3)
    examples = [
        "Plan a 4-day trip to Sri Lanka",
        "Weekend getaway to Goa",
        "5 days in Kyoto, budget-friendly",
    ]
    clicked_example = None
    for col, example in zip(example_cols, examples):
        if col.button(example, use_container_width=True):
            clicked_example = example
else:
    clicked_example = None

# Render existing messages
for msg in active_chat["messages"]:
    avatar = "🧳" if msg["role"] == "user" else "🌍"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

user_input = st.chat_input("e.g. Plan a trip to Goa for 5 days") or clicked_example

if user_input:
    if active_chat["title"] == "New chat":
        active_chat["title"] = user_input[:40] + ("..." if len(user_input) > 40 else "")

    active_chat["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧳"):
        st.markdown(user_input)

    with st.spinner("Planning your trip..."):
        try:
            response = requests.post(
                f"{BASE_URL}/query",
                json={"question": user_input, "thread_id": active_id},
                timeout=120,
            )
        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ Could not reach the backend: {e}")
            st.stop()

    if response.status_code == 200:
        data = response.json()
        answer = data.get("answer", "No answer returned.")
        saved_file = data.get("saved_file")
        saved_pdf = data.get("saved_pdf")

        active_chat["messages"].append({"role": "assistant", "content": answer})
        with st.chat_message("assistant", avatar="🌍"):
            st.markdown(answer)

            if saved_file or saved_pdf:
                col1, col2 = st.columns(2)
                if saved_file:
                    try:
                        with open(saved_file, "rb") as f:
                            col1.download_button(
                                "📥 Markdown", data=f,
                                file_name=saved_file.split("/")[-1], mime="text/markdown",
                                key=f"md_{active_id}_{len(active_chat['messages'])}",
                                use_container_width=True,
                            )
                    except FileNotFoundError:
                        pass
                if saved_pdf:
                    try:
                        with open(saved_pdf, "rb") as f:
                            col2.download_button(
                                "📄 PDF", data=f,
                                file_name=saved_pdf.split("/")[-1], mime="application/pdf",
                                key=f"pdf_{active_id}_{len(active_chat['messages'])}",
                                use_container_width=True,
                            )
                    except FileNotFoundError:
                        pass
        st.rerun()
    else:
        st.error("⚠️ Bot failed to respond: " + response.text)