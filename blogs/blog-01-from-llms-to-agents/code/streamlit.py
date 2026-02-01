import requests
import streamlit as st

st.title("Policy Assistant")
question = st.text_input("Ask a policy question")

if st.button("Ask") and question:
    response = requests.post("http://127.0.0.1:8000/ask", json={"question": question})
    if response.ok:
        st.write(response.json()["answer"])
    else:
        st.error("Request failed")