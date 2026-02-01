import os
import asyncio
from pathlib import Path

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.functions import kernel_function, KernelArguments

# Azure OpenAI environment variables
AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_KEY = os.environ["AZURE_OPENAI_API_KEY"]
AZURE_OPENAI_DEPLOYMENT = os.environ["AZURE_OPENAI_DEPLOYMENT"]

FAQ_DIR = Path("./faq_docs")  # Folder containing .txt files

def load_faq_docs() -> dict[str, str]:
    """Load each .txt file into a {key: content} dictionary."""
    docs = {}
    for path in FAQ_DIR.glob("*.txt"):
        docs[path.stem] = path.read_text(encoding="utf-8").strip()
    return docs

FAQ = load_faq_docs()

class InternalFaqTool:
    @kernel_function(
        name="lookup_faq",
        description="Lookup internal policy or FAQ by key",
    )
    def lookup_faq(self, key: str) -> str:
        return FAQ.get(key, "No policy found for that key.")

instructions = """
You are a helpful internal knowledge assistant.
If you need a policy, call the lookup_faq tool.

You can answer questions about:
- Release freeze timelines and what is allowed during the freeze
- SEV1 incident handling, roles, escalation, and communication
"""

settings = OpenAIChatPromptExecutionSettings(
    temperature=0.2,  # Lower temperature for more consistent, factual responses
    max_tokens=500,   # Limit output length
    tool_choice="auto",  # Let the model decide when to call tools
)

_agent = ChatCompletionAgent(
    service=AzureChatCompletion(
        deployment_name=AZURE_OPENAI_DEPLOYMENT,
        endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
    ),
    name="Policy-Assistant",
    instructions=instructions,
    plugins=[InternalFaqTool()],
    arguments=KernelArguments(settings),
)

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