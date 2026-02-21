import os
import asyncio
from pathlib import Path

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.functions import kernel_function, KernelArguments

# --- Configuration ---
# Load credentials from a .env file so secrets never appear in source code.
# Falls back to real environment variables if .env is absent (e.g. in CI/CD).
from dotenv import load_dotenv
load_dotenv()

AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_KEY = os.environ["AZURE_OPENAI_API_KEY"]
AZURE_OPENAI_DEPLOYMENT = os.environ["AZURE_OPENAI_DEPLOYMENT"]  # e.g. "gpt-4o-mini"

FAQ_DIR = Path("./faq_docs")  # Folder containing .txt files

def load_faq_docs() -> dict[str, str]:
    """Load each .txt file into a {key: content} dictionary."""
    docs = {}
    for path in FAQ_DIR.glob("*.txt"):
        docs[path.stem] = path.read_text(encoding="utf-8").strip()
    return docs

FAQ = load_faq_docs()  # Loaded once at startup; acts as the agent's private knowledge base

# --- Tool definition ---
# This class is the agent's only "action": retrieve a policy document by name.
# The @kernel_function decorator registers it so the LLM can invoke it by name.
class InternalFaqTool:
    @kernel_function(
        name="lookup_faq",
        description="Lookup internal policy or FAQ by key",
    )
    def lookup_faq(self, key: str) -> str:
        return FAQ.get(key, "No policy found for that key.")

# --- System prompt ---
# Shapes the agent's persona, scope, and when to call the tool.
# The LLM reads this on every turn to decide how to respond.
instructions = """
You are a helpful internal knowledge assistant.
If you need a policy, call the lookup_faq tool.

You can answer questions about:
- Release freeze timelines and what is allowed during the freeze
- SEV1 incident handling, roles, escalation, and communication
"""

# --- LLM parameters ---
# These settings are passed to the LLM on every call.
settings = OpenAIChatPromptExecutionSettings(
    temperature=0.2,  # Lower temperature for more consistent, factual responses
    max_tokens=500,   # Limit output length
    tool_choice="auto",  # Let the model decide when to call tools
)

# --- Agent assembly ---
# Wires together the LLM service, system prompt, tool, and call settings.
# AzureChatCompletion is the LLM call that drives all reasoning and responses.
_agent = ChatCompletionAgent(
    service=AzureChatCompletion(       # LLM: connects to Azure OpenAI
        deployment_name=AZURE_OPENAI_DEPLOYMENT,
        endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
    ),
    name="Policy-Assistant",
    instructions=instructions,
    plugins=[InternalFaqTool()],       # Tools the LLM is allowed to call
    arguments=KernelArguments(settings),
)

# --- Agent loop entry point ---
# get_response triggers the full plan -> act -> observe cycle:
# the LLM decides whether to call a tool or respond directly.
async def ask_agent(question: str) -> str:
    response = await _agent.get_response(messages=question)
    return response.content

async def main() -> None:
    user_question = input(
        "Ask a policy question (e.g., release freeze timing or SEV1 escalation): "
    ).strip()
    answer = await ask_agent(user_question)
    print(answer)

if __name__ == "__main__":
    asyncio.run(main())
