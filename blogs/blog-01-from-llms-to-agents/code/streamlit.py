import requests
import streamlit as st

st.title("Policy Assistant")
question = st.text_input("Ask a policy question")

if st.button("Ask") and question:
    # Send the question to the FastAPI backend via HTTP POST.
    # The backend delegates to the agent, which calls the LLM and returns an answer.
    response = requests.post("http://127.0.0.1:8000/ask", json={"question": question})
    if response.ok:
        st.write(response.json()["answer"])  # Display the agent's response
    else:
        st.error("Request failed")
