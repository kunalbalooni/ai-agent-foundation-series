from fastapi import FastAPI
from pydantic import BaseModel

from agent import ask_agent, reset_session  # Stateful agent with per-session ChatHistory

app = FastAPI()

# --- Request/response schemas ---

class Query(BaseModel):
    question: str
    session_id: str = "default"  # Each client passes its own session ID for isolated history

class ResetRequest(BaseModel):
    session_id: str = "default"

# POST /ask — routes the question + session_id to the stateful agent.
# The agent appends to (or starts) the ChatHistory for that session_id,
# so follow-up questions retain full context from earlier in the conversation.
@app.post("/ask")
async def ask(query: Query):
    answer = await ask_agent(query.question, session_id=query.session_id)
    return {"answer": answer, "session_id": query.session_id}

# POST /reset — clears the ChatHistory for a session.
# Call this when the user explicitly starts a new topic or resets the chat.
@app.post("/reset")
async def reset(req: ResetRequest):
    reset_session(req.session_id)
    return {"status": "reset", "session_id": req.session_id}
