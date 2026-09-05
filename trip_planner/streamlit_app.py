import streamlit as st
import requests
import uuid
import re
import json

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

# ---------------- Helpers ----------------
def extract_clarify_blocks(text: str):
    """Look for a ```clarify [...] ``` fenced block in the assistant's reply.
    Returns (clean_text, blocks) where blocks is None if no valid block was found."""
    match = re.search(r"```clarify\s*(\[.*?\])\s*```", text, re.DOTALL)
    if not match:
        return text, None
    try:
        blocks = json.loads(match.group(1))
        if not isinstance(blocks, list) or not blocks:
            return text, None
    except (json.JSONDecodeError, TypeError):
        return text, None
    clean_text = (text[:match.start()] + text[match.end():]).strip()
    return clean_text, blocks


def send_message(active_id: str, active_chat: dict, text: str):
    """Send a message to the backend and update chat state. Shared by typed input,
    example clicks, and clarify-button clicks so all three behave identically."""
    if active_chat["title"] == "New chat":
        active_chat["title"] = text[:40] + ("..." if len(text) > 40 else "")

    active_chat["messages"].append({"role": "user", "content": text})
    active_chat["pending_clarify"] = None
    active_chat["clarify_selections"] = {}

    with st.spinner("Planning your trip..."):
        try:
            response = requests.post(
                f"{BASE_URL}/query",
                json={"question": text, "thread_id": active_id},
                #timeout=120,
            )
        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ Could not reach the backend: {e}")
            st.stop()

    if response.status_code == 200:
        data = response.json()
        raw_answer = data.get("answer", "No answer returned.")
        clean_answer, clarify_blocks = extract_clarify_blocks(raw_answer)

        active_chat["messages"].append({
            "role": "assistant",
            "content": clean_answer,
            "saved_file": data.get("saved_file"),
            "saved_pdf": data.get("saved_pdf"),
        })
        active_chat["pending_clarify"] = clarify_blocks
    else:
        st.error("⚠️ Bot failed to respond: " + response.text)

    st.rerun()


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
active_chat.setdefault("pending_clarify", None)
active_chat.setdefault("clarify_selections", {})

st.title("🌍 Travel Planner")
st.caption("Tell me where you want to go, and I'll build you a complete trip plan.")

# Empty state — friendly starter prompts
clicked_example = None
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
for i, msg in enumerate(active_chat["messages"]):
    avatar = "🧳" if msg["role"] == "user" else "🌍"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            saved_file = msg.get("saved_file")
            saved_pdf = msg.get("saved_pdf")
            if saved_file or saved_pdf:
                col1, col2 = st.columns(2)
                if saved_file:
                    try:
                        with open(saved_file, "rb") as f:
                            col1.download_button(
                                "📥 Markdown", data=f,
                                file_name=saved_file.split("/")[-1], mime="text/markdown",
                                key=f"md_{active_id}_{i}", use_container_width=True,
                            )
                    except FileNotFoundError:
                        pass
                if saved_pdf:
                    try:
                        with open(saved_pdf, "rb") as f:
                            col2.download_button(
                                "📄 PDF", data=f,
                                file_name=saved_pdf.split("/")[-1], mime="application/pdf",
                                key=f"pdf_{active_id}_{i}", use_container_width=True,
                            )
                    except FileNotFoundError:
                        pass

# ---------------- Pending clarify buttons (for the latest assistant message) ----------------
clarify_answer = None
pending = active_chat.get("pending_clarify")

if pending:
    with st.container():
        st.markdown("&nbsp;")
        selections = active_chat["clarify_selections"]
        other_texts = active_chat.setdefault("clarify_other_texts", {})
        show_other_input = active_chat.setdefault("clarify_show_other", {})

        def _single_question_ui(qi, block, msg_len, immediate_submit=False):
            """Renders a single-choice question with an 'Other' escape hatch.
            Returns an answer string if the user just submitted one, else None."""
            st.markdown(f"**{block['question']}**")

            opts = block["options"]
            cols = st.columns(len(opts) + 1)
            for oi, opt in enumerate(opts):
                is_selected = selections.get(qi) == opt
                label = ("✅ " if is_selected else "") + opt
                if cols[oi].button(opt if not is_selected else label, key=f"clarify_{active_id}_{msg_len}_{qi}_{oi}", use_container_width=True):
                    show_other_input[qi] = False
                    if immediate_submit:
                        return opt
                    selections[qi] = opt
                    st.rerun()

            if cols[-1].button("✏️ Other", key=f"clarify_other_btn_{active_id}_{msg_len}_{qi}", use_container_width=True):
                show_other_input[qi] = True
                st.rerun()

            if show_other_input.get(qi):
                custom_val = st.text_input(
                    "Type your own answer",
                    key=f"clarify_other_text_{active_id}_{msg_len}_{qi}",
                    label_visibility="collapsed",
                    placeholder="Type your answer and press Submit",
                )
                if st.button("Submit", key=f"clarify_other_submit_{active_id}_{msg_len}_{qi}"):
                    if custom_val.strip():
                        if immediate_submit:
                            return custom_val.strip()
                        selections[qi] = custom_val.strip()
                        st.rerun()
            return None

        has_multi = any(block.get("type") == "multi" for block in pending)

        if len(pending) == 1 and pending[0].get("type", "single") == "single":
            # single question, single choice -> submits immediately (including custom "Other" text)
            result = _single_question_ui(0, pending[0], len(active_chat["messages"]), immediate_submit=True)
            if result:
                clarify_answer = result
        else:
            for qi, block in enumerate(pending):
                q_type = block.get("type", "single")

                if q_type == "multi":
                    st.markdown(f"**{block['question']}**")
                    chosen = st.multiselect(
                        "Select all that apply",
                        options=block["options"],
                        default=[v for v in selections.get(qi, []) if v in block["options"]],
                        key=f"clarify_multi_{active_id}_{len(active_chat['messages'])}_{qi}",
                        label_visibility="collapsed",
                    )
                    custom_val = st.text_input(
                        "Anything else not listed?",
                        key=f"clarify_multi_other_{active_id}_{len(active_chat['messages'])}_{qi}",
                        placeholder="Optional — add anything not in the list above",
                    )
                    combined = list(chosen)
                    if custom_val.strip():
                        combined.append(custom_val.strip())
                    selections[qi] = combined
                else:
                    _single_question_ui(qi, block, len(active_chat["messages"]), immediate_submit=False)

            def _is_answered(qi, block):
                val = selections.get(qi)
                return bool(val) if block.get("type") == "multi" else val is not None

            all_answered = all(_is_answered(qi, block) for qi, block in enumerate(pending))

            if all_answered:
                if st.button("Continue ➜", type="primary", key=f"continue_{active_id}_{len(active_chat['messages'])}"):
                    parts = []
                    for qi, block in enumerate(pending):
                        val = selections[qi]
                        parts.append(", ".join(val) if isinstance(val, list) else val)
                    clarify_answer = "; ".join(parts)
            else:
                st.caption("Answer each question to continue.")
                
# ---------------- Input handling ----------------
typed_input = st.chat_input("e.g. Plan a trip to Goa for 5 days")

final_input = typed_input or clicked_example or clarify_answer

if final_input:
    with st.chat_message("user", avatar="🧳"):
        st.markdown(final_input)
    send_message(active_id, active_chat, final_input)