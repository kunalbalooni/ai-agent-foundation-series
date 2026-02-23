import os
import asyncio
from pathlib import Path

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function, KernelArguments

# --- Configuration ---
# Load credentials from a .env file so secrets never appear in source code.
# Falls back to real environment variables if .env is absent (e.g. in CI/CD).
from dotenv import load_dotenv
load_dotenv()

AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_KEY = os.environ["AZURE_OPENAI_API_KEY"]
AZURE_OPENAI_DEPLOYMENT = os.environ["AZURE_OPENAI_DEPLOYMENT"]

FAQ_DIR = Path("../data/faq_docs")

def load_faq_docs() -> dict[str, str]:
    """Load each .txt file into a {key: content} dictionary."""
    docs = {}
    for path in FAQ_DIR.glob("*.txt"):
        docs[path.stem] = path.read_text(encoding="utf-8").strip()
    return docs

FAQ = load_faq_docs()  # Loaded once at startup; acts as the agent's private knowledge base

# --- Tool definition ---
# lookup_faq is the only action the agent is allowed to take.
# The description tells the LLM exactly when to call it and which keys are valid.
class InternalFaqTool:
    @kernel_function(
        name="lookup_faq",
        description="Lookup an internal policy document by key. "
                    "Valid keys: 'release-freeze', 'incident-sev1'.",
    )
    def lookup_faq(self, key: str) -> str:
        return FAQ.get(key, "Policy not found. Please check with your Release Manager.")

# --- Structured system prompt ---
# Organised into named sections so each behaviour can be changed independently.
# Treat this like source code: one section = one responsibility.
INSTRUCTIONS = """
## PERSONA
You are the internal policy assistant for an engineering team.
You are precise, concise, and cite the specific policy that informs your answer.
You do not use filler phrases like "Great question!" or "Certainly!".

## SCOPE
You answer questions on these topics only:
- Release freeze: timing, allowed changes, exceptions, approvals, rollback.
- SEV1 incidents: definition, roles, timelines, escalation, post-incident requirements.

If a question is outside this scope, respond exactly:
  "I can only answer questions about release freeze and SEV1 incidents."

## TOOL USAGE RULES
- Always call lookup_faq before answering a policy question.
- Call it with the key "release-freeze" for release freeze questions.
- Call it with the key "incident-sev1" for SEV1 questions.
- Do not answer from memory; use only what the tool returns.

## RESPONSE FORMAT
- Answer in plain prose, 3-5 sentences maximum.
- If the answer involves a list of steps or roles, use a numbered or bulleted list.
- End every answer with: "Source: <policy key used>"

## BEHAVIOUR UNDER UNCERTAINTY
- If the tool returns no content for a key, respond: "Policy not found. Please check with your Release Manager."
- If the user's question is ambiguous, ask one clarifying question before calling the tool.
"""

# --- LLM parameters ---
# Temperature 0.1: maximise consistency across repeated runs.
# Raising it above ~0.4 will make answers noticeably less predictable.
SETTINGS = OpenAIChatPromptExecutionSettings(
    temperature=0.1,
    max_tokens=600,
    tool_choice="auto",  # Let the LLM decide when to call the tool
)

# --- Agent assembly ---
# Wires together the LLM service, structured prompt, tool, and call settings.
_agent = ChatCompletionAgent(
    service=AzureChatCompletion(       # LLM: connects to Azure OpenAI
        deployment_name=AZURE_OPENAI_DEPLOYMENT,
        endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
    ),
    name="Policy-Assistant",
    instructions=INSTRUCTIONS,
    plugins=[InternalFaqTool()],
    arguments=KernelArguments(SETTINGS),
)

# --- In-process session store ---
# Maps session_id -> ChatHistory so each user keeps their own conversation context.
# In production, replace this dict with an external store (Redis, database, etc.)
# so history survives server restarts and scales across multiple processes.
_sessions: dict[str, ChatHistory] = {}

def get_or_create_history(session_id: str) -> ChatHistory:
    """Return the existing ChatHistory for a session, or create a new one."""
    if session_id not in _sessions:
        _sessions[session_id] = ChatHistory()
    return _sessions[session_id]

# --- Stateful agent entry point ---
# The full ChatHistory is passed to invoke() on every call.
# The LLM sees the complete conversation — not just the latest question —
# so follow-up questions like "what about exceptions?" resolve correctly.
async def ask_agent(question: str, session_id: str = "default") -> str:
    history = get_or_create_history(session_id)
    history.add_user_message(question)        # Append new question to history

    response_text = ""
    # invoke() runs the plan -> act -> observe loop; tool calls happen inside here
    async for chunk in _agent.invoke(history):
        response_text += str(chunk.content)

    history.add_assistant_message(response_text)  # Persist the answer
    return response_text

def reset_session(session_id: str = "default") -> None:
    """Clear the conversation history for a session."""
    _sessions.pop(session_id, None)

async def main() -> None:
    """Interactive CLI loop — demonstrates multi-turn state.
    Type 'reset' to clear history, 'quit' to exit.
    """
    session_id = "cli-session"
    print("Policy Assistant (type 'reset' to clear history, 'quit' to exit)\n")
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            break
        if user_input.lower() == "reset":
            reset_session(session_id)
            print("[Session history cleared]\n")
            continue
        answer = await ask_agent(user_input, session_id=session_id)
        print(f"Agent: {answer}\n")

if __name__ == "__main__":
    asyncio.run(main())
