from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

from api.auth import CurrentUser, get_current_user

app = FastAPI()

# CORS — per-environment origin allowlist loaded from environment variable
# Never use allow_origins=["*"] in production with allow_credentials=True
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,   # Required for Authorization header to be sent
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


class Query(BaseModel):
    question: str
    session_id: str = "default"


class Answer(BaseModel):
    answer: str
    session_id: str
    user: str


@app.post("/ask", response_model=Answer)
async def ask(
    query: Query,
    user: CurrentUser = Depends(get_current_user),  # Authentication enforced here
):
    """Protected endpoint — requires a valid bearer token.

    The CurrentUser object carries identity and group context.
    Downstream, it can be used for:
    - Session isolation (session_id scoped to user.object_id)
    - Audit logging (user.upn + user.object_id)
    - Row-level security (user.groups used to filter retrieval results)

    This demo returns a placeholder answer. Replace the body with your
    agent call (e.g. ask_agent from the series backend).
    """
    # Scope the session to the authenticated user to prevent session crossing
    scoped_session_id = f"{user.object_id}:{query.session_id}"

    # --- Replace this with your actual agent call ---
    # from agent import ask_agent
    # answer = await ask_agent(query.question, session_id=scoped_session_id)
    answer = f"[Demo] Received: '{query.question}' (session: {scoped_session_id})"
    # ------------------------------------------------

    return Answer(
        answer=answer,
        session_id=query.session_id,
        user=user.upn,  # Include for frontend display; never log the full token
    )


@app.get("/health")
async def health():
    """Health check endpoint — unauthenticated, used by load balancer."""
    return {"status": "healthy"}
