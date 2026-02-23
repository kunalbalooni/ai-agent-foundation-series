import uuid
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.title("Policy Assistant")
st.caption("Multi-turn — ask follow-up questions and the agent remembers the context.")

# Assign a unique session ID per browser tab so each user has isolated history.
# uuid4() is generated once per session and stored in Streamlit's session_state.
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Local message list mirrors what is displayed in the chat window.
# The authoritative conversation history lives server-side in ChatHistory.
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render the full conversation so far
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# st.chat_input renders a persistent input box at the bottom of the page.
# Streamlit re-runs the entire script each time the user submits a message.
question = st.chat_input("Ask a policy question...")

if question:
    # Display the user's message immediately (before waiting for the API)
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    # Send to the FastAPI backend — session_id ensures the agent uses the right history
    response = requests.post(
        f"{API_URL}/ask",
        json={"question": question, "session_id": st.session_state.session_id},
    )
    if response.ok:
        answer = response.json()["answer"]  # LLM response, grounded by the policy tool
    else:
        answer = "Request failed. Is the API server running?"

    # Persist and display the agent's response
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.write(answer)

# Sidebar: reset button clears both the local display and the server-side ChatHistory
with st.sidebar:
    st.header("Session")
    st.write(f"Session ID: `{st.session_state.session_id[:8]}...`")
    if st.button("Reset conversation"):
        # Clear server-side ChatHistory for this session
        requests.post(
            f"{API_URL}/reset",
            json={"session_id": st.session_state.session_id},
        )
        # Clear local display
        st.session_state.messages = []
        st.rerun()
