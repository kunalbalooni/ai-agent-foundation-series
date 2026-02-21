from fastapi import FastAPI
from pydantic import BaseModel

from agent import ask_agent  # Imports the agent loop defined in agent.py

app = FastAPI()

# Request schema — validates and documents the expected JSON body
class Query(BaseModel):
    question: str

# POST /ask — receives the user's question and returns the agent's answer.
# Keeping this thin means the same agent can be reused by any client
# (CLI, Streamlit, Slack bot, etc.) without changing agent.py.
@app.post("/ask")
async def ask(query: Query):
    answer = await ask_agent(query.question)  # Delegates to the agent loop (LLM call happens here)
    return {"answer": answer}
