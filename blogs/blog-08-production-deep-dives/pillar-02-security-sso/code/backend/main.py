import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.auth import CurrentUser, get_current_user

app = FastAPI(title="AI Agent SSO Demo — Backend")

# CORS — per-environment origin allowlist loaded from environment variable.
# Never use allow_origins=["*"] in production with allow_credentials=True.
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,   # Required for Authorization header to be sent
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


class Query(BaseModel):
    question: str
    session_id: str = "default"


@app.post("/ask")
async def ask(
    query: Query,
    user: CurrentUser = Depends(get_current_user),  # Authentication enforced here
):
    """Protected endpoint — requires a valid bearer token.

    The CurrentUser object carries identity and group context. Downstream it is used for:
    - Session isolation (session_id scoped to user.object_id)
    - Audit logging (user.upn + user.object_id)
    - Row-level security (user.groups used to filter retrieval results)
    """
    # Scope the session to the authenticated user to prevent session crossing
    scoped_session_id = f"{user.object_id}:{query.session_id}"

    # Stub response — in production this calls ask_agent(query.question, session_id=...)
    answer = (
        f"Hello {user.display_name or user.upn}! "
        f"Your session is '{scoped_session_id}'. "
        f"You asked: \"{query.question}\". "
        f"(Connect your agent here — authentication is working correctly.)"
    )

    return {
        "answer": answer,
        "session_id": query.session_id,
        "user": user.upn,     # Include for frontend display; never log the full token
    }


@app.get("/health")
async def health():
    """Health check endpoint — unauthenticated, used by load balancer."""
    return {"status": "healthy"}


@app.get("/me")
async def me(user: CurrentUser = Depends(get_current_user)):
    """Returns the validated identity claims from the bearer token.
    Useful for debugging authentication in development.
    """
    return {
        "object_id": user.object_id,
        "upn": user.upn,
        "display_name": user.display_name,
        "groups": user.groups,
        "scopes": user.scopes,
    }
