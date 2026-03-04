# From LLMs to AI Agents — Why a Prompt Is Not Enough

You have probably used AI assistants like **[ChatGPT](https://chat.openai.com/)**, **[Grok](https://x.ai/)**, or **[DeepSeek](https://www.deepseek.com/)**. They are great for everyday work: summarizing documents, explaining logs, writing SQL, generating Python snippets, troubleshooting errors, or drafting emails and reports. Under the hood, these assistants are powered by **Large Language Models (LLMs)** — models trained on vast amounts of text to understand and generate language. If you are like most people, you have also noticed the assistant gets better when you **paste in more context**: more tables, more logs, more documentation, more examples.

That ceiling — the point where pasting more context stops being enough — is where a plain LLM falls short and an agent takes over. To be truly useful in a business context, an assistant must **retrieve the right context** automatically (for example, fetching the latest policy page rather than relying on whatever you pasted last week), **take actions through tools** (like querying a database or calling an API), and **keep state** (remembering earlier steps in a workflow or a multi-turn investigation). That is what AI agents add on top of LLMs.

In this post, we will build a small **internal policy assistant** that answers release-freeze and incident questions, and use it as the running example for the series.

---

## LLM vs agent

### Where LLMs are genuinely useful

For many everyday business tasks, a well-prompted LLM is all you need. In these cases *you* are the one doing the retrieval (you paste the content in) and *you* are the one taking action (you run the SQL, you send the email). The LLM handles only the language part:

| Business task | What the LLM does |
|---|---|
| Draft a post-incident summary | Reads the log you paste, writes a clear narrative |
| Generate SQL from natural language | Turns "show me last month's top customers" into a working query |
| Explain a cryptic error message | Reads the stack trace and describes the likely cause |
| Write a release note | Takes a list of changes and produces a professional summary |
| Summarise a long policy document | Condenses 20 pages into 5 bullets |

### Where LLMs fall short — and need an agent

The moment the *retrieval*, *action*, or *memory* must happen **automatically and repeatedly**, a standalone LLM breaks down:

| Business need | Why the LLM alone fails |
|---|---|
| "Answer questions about our *current* release freeze policy" | The LLM was trained months ago. It cannot fetch the live policy document. |
| "Alert me if this log pattern appears again within an hour" | The LLM has no memory between calls. Each prompt starts from zero. |
| "Raise a PagerDuty ticket if the on-call engineer hasn't acknowledged the SEV1" | The LLM cannot call external APIs or take actions in other systems. |
| "Walk an engineer through an incident response *step by step*, checking each step is complete before moving on" | The LLM cannot maintain workflow state across multiple turns reliably. |

In each case, the language capability of the LLM is still exactly what you want — you just need to give it **hands** (tools to call), **memory** (state that persists), and a **driver** (a loop that keeps it on task). That is where an agent comes in.

---

## What makes an agent

An agent does not replace the LLM — it **builds around it**. The LLM stays at the centre, doing what it does best (reasoning and language). The agent framework layers on three capabilities the LLM is missing on its own:

- **Tools** — the ability to call APIs or functions (so it can *act*)
- **State** — memory and context across steps (so it can *remember*)
- **Control loop** — a repeatable plan/act/observe cycle (so it can *drive a workflow*)

### The building blocks

The architecture diagram below shows the relationship: the LLM is the reasoning core, surrounded by tools, state, and the control loop that orchestrates everything.

```mermaid
flowchart TB
  subgraph Agent
    LLM[LLM Reasoning]
    Tools[Tools]
    State[State / Memory]
    subgraph Control_Loop[Control Loop]
      Plan[Plan]
      Act[Act]
      Observe[Observe]
      Plan --> Act --> Observe --> Plan
    end
  end
  Plan --> LLM
  LLM --> Act
  Act --> Tools
  Tools --> APIs[APIs / DBs / Search]
  Observe --> State
  LLM <--> State
  State --> Context[Conversation + Workflow Context]
```

State is what lets the agent remember you already asked for the SEV1 policy, so it does not re-fetch it every turn. Tools are what let it actually look that policy up from your internal system, rather than guessing.

### The control loop at runtime

Those building blocks only become useful when the agent is actually running. At runtime, the agent follows a tight loop:

1. **Plan** — the LLM reasons about what to do next given the current state
2. **Act** — it either calls a tool or returns a direct response
3. **Observe** — the result is fed back into state and the loop repeats if needed

```mermaid
flowchart TD
    A[User request] --> B[LLM plans next step]
    B --> C{Tool needed?}
    C -- No --> D[Return response]
    C -- Yes --> E[Call tool]
    E --> F[Observe tool result]
    F --> B
```

This loop is the reason agent code looks different from a plain LLM call: you need a tool registry, an execution kernel, and a state store — one for each phase of the loop.

---

## Frameworks and SDKs

Understanding the loop and the building blocks is the conceptual foundation. Before writing any code, you need to pick the right framework to implement it — because your choice shapes how easy the loop is to build, inspect, and run in production.

A simple way to choose is to compare frameworks on a few **practical metrics**.

### Key metrics to compare

1. **Language support** — Does it match your stack (Python, C#, JS, etc.)?
2. **Tooling & integrations** — Built-in connectors to data, APIs, search, and enterprise tools.
3. **Orchestration features** — Memory, routing, planners, multi-agent support.
4. **Control & transparency** — How easy it is to inspect decisions and failures.
5. **Production readiness** — Deployment patterns, security features, monitoring.
6. **Learning curve** — How fast a beginner can ship something useful.

### Quick comparison

| Framework / SDK | Best for | Lang support | Tooling & integrations | Orchestration | Control & transparency | Production readiness | Learning curve | Strengths | Trade-offs | Recommendation |
|---|---|---|---|---|---|---|---|---|---|---|
| **[Semantic Kernel](https://github.com/microsoft/semantic-kernel)** | Enterprise agents, structured tools | Python, .NET | ✓ Azure, OpenAI, Hugging Face | ✓ Planners, multi-step | ✓ Structured logging | ✓✓ Azure-native | Medium | Tool-first design, strong Azure integration | Smaller community than LangChain | **Best for Azure / .NET enterprise teams** |
| **[LangChain](https://www.langchain.com/)** | Rapid prototyping, broad ecosystem | Python, JS/TS | ✓✓ 100+ integrations | ✓ Chains, agents, memory | ✓ LangSmith tracing | ✓ Broad deployment | Low | Largest community, most examples | Can feel abstract, harder to debug | **Best for beginners & rapid prototyping** |
| **[LlamaIndex](https://www.llamaindex.ai/)** | Data-centric applications | Python, JS/TS | ✓ Data/retrieval focused | ✗ Limited agent orchestration | ✓ Query pipelines | ✓ Pairs with other frameworks | Low | Best-in-class RAG tooling | Not a full agent framework | **Best for RAG & data-heavy applications** |
| **[AutoGen](https://github.com/microsoft/autogen)** | Multi-agent research | Python | ✓ OpenAI, Azure | ✓✓ Multi-agent coordination | ✓ Conversation traces | ✗ Experimental for production | High | Strong multi-agent patterns, active research | Production-readiness gaps | **Best for multi-agent research & experimentation** |
| **[CrewAI](https://www.crewai.com/)** | Role-based agent teams | Python | ✓ OpenAI, Anthropic, local | ✓ Role-based multi-agent | ✓ Basic | ✗ Limited enterprise features | Low | Simple role-based design, minimal boilerplate | Limited scaling & enterprise controls | **Best for quick role-based agent prototypes** |
| **[n8n](https://n8n.io/)** | Low-code workflows | No-code / JS | ✓✓ 400+ integrations | ✓ Visual workflows | ✗ Limited custom logic | ✓ Self-hostable | Very Low | Fast visual automation, no code needed | Not code-first, less flexible for custom logic | **Best for non-developers & low-code automation** |
| **[AWS Strands](https://aws.amazon.com/)** | AWS-native agent stacks | Python | ✓✓ AWS services native | ✓ Step Functions, Bedrock | ✓ CloudWatch, X-Ray | ✓✓ AWS production patterns | Medium | Tight AWS integration, enterprise deployment | AWS-leaning, smaller community outside AWS | **Best for AWS-native production stacks** |
| **[Copilot Studio](https://www.microsoft.com/microsoft-copilot/microsoft-copilot-studio)** | Business users, M365 ecosystem | No-code | ✓ M365, Power Platform | ✓ Visual flows | ✗ Limited debugging | ✓ M365 managed | Very Low | Easy UI, Microsoft ecosystem | Platform constraints, less custom control | **Best for M365 business users, no coding needed** |
| **[Azure AI Studio](https://ai.azure.com/)** | Azure-native build & deploy | Python | ✓✓ Azure-native | ✓ Prompt flow, evaluation | ✓✓ Built-in eval & monitoring | ✓✓ Managed Azure deployment | Medium | Unified model catalog, evaluation, deployment | Azure-centric workflows | **Best for Azure-native build & deployment pipelines** |

For the examples below, we will use **Semantic Kernel (Python)** as a code-first option. The overall flow stays very similar across most frameworks, so feel free to map the same steps to the SDK you prefer.

---

## Building the agent

We have covered the concept (LLM as core, agent wrapping it with tools, state, and a control loop) and chosen a framework (Semantic Kernel). Now let's turn that loop into running code.

When you build your first agent, four recurring code patterns show up, each with a clear purpose:

1. **Model configuration** — gives the agent its reasoning core (the LLM). Without this, nothing thinks.
2. **System prompt** — shapes the agent's persona, scope, and behaviour. It tells the LLM *who it is*, *what it knows*, and *when to use a tool*. The LLM reads this on every turn before deciding how to respond.
3. **Tool registration** — defines what the agent can *do* beyond generating text. This is the "act" phase of the loop.
4. **Execution call** — triggers the plan → act → observe cycle and returns a grounded answer.

We will keep the tools minimal — one tool that looks up an internal FAQ document — and focus on the reasoning behind each step. The scenario is deliberately practical: an internal policy assistant that can answer questions about release freezes and SEV1 incidents by fetching the right document automatically.

> **Prerequisites:**
> - Azure OpenAI resource with a deployed model (e.g., `gpt-4o-mini`)
> - Python 3.10+ with `semantic-kernel` installed
> - A folder of `.txt` files for FAQs (one policy per file)

**Model recommendations**
- **Fast + cost-effective:** `gpt-4o-mini`
- **Balanced accuracy:** `gpt-4o`
- **Advanced reasoning tasks:** `o3-mini` (if available in your Azure region)

For guidance on choosing models, see **[Azure OpenAI model selection](https://learn.microsoft.com/azure/ai-services/openai/concepts/models)**.

> **No Azure subscription yet?** **[free-llm-api-resources](https://github.com/cheahjs/free-llm-api-resources)** is a regularly updated GitHub repository that tracks free tiers, trial credits, and open-access endpoints across many providers. It is a practical starting point if you want to experiment before committing to a paid service.

### Full example

**agent.py**

```python
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

FAQ_DIR = Path("../data/faq_docs")

def load_faq_docs() -> dict[str, str]:
    """Load each .txt file into a {key: content} dictionary."""
    docs = {}
    for path in FAQ_DIR.glob("*.txt"):
        docs[path.stem] = path.read_text(encoding="utf-8").strip()
    return docs

FAQ = load_faq_docs()  # Loaded once at startup; acts as the agent's private knowledge base

# --- Tool registration ---
# This class is the agent's only "action": retrieve a policy document by name.
# The @kernel_function decorator registers it so the LLM can invoke it by name.
class InternalFaqTool:
    @kernel_function(
        name="lookup_faq",
        description="Lookup an internal policy document by key. "
                    "Valid keys: 'release-freeze', 'incident-sev1'.",
    )
    def lookup_faq(self, key: str) -> str:
        return FAQ.get(key, "Policy not found. Please check with your Release Manager.")

# --- System prompt ---
# Shapes the agent's persona, scope, and when to call a tool.
# The LLM reads this on every turn before deciding how to respond.
instructions = """
You are a helpful internal knowledge assistant.
If you need a policy, call the lookup_faq tool.

You can answer questions about:
- Release freeze timelines and what is allowed during the freeze
- SEV1 incident handling, roles, escalation, and communication
"""

# --- LLM parameters ---
# These settings are passed to the LLM on every call.
SETTINGS = OpenAIChatPromptExecutionSettings(
    temperature=0.2,  # Lower temperature for more consistent, factual responses
    max_tokens=500,   # Limit output length
    tool_choice="auto",  # Let the model decide when to call tools
)

# --- Model configuration ---
# Wires together the LLM service, system prompt, tool, and call settings.
_agent = ChatCompletionAgent(
    service=AzureChatCompletion(       # Connects to Azure OpenAI — this is the LLM API endpoint
        deployment_name=AZURE_OPENAI_DEPLOYMENT,
        endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
    ),
    name="Policy-Assistant",
    instructions=instructions,         # System prompt
    plugins=[InternalFaqTool()],       # Registered tools
    arguments=KernelArguments(SETTINGS),
)

# --- Execution call ---
# get_response triggers the full plan -> act -> observe loop:
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
```

### Exposing the agent via API + simple UI

The agent now works from the command line. For real-world use, we want it accessible over HTTP so any client — a browser, a Slack bot, a CI pipeline — can call it without knowing the agent internals. That means wrapping it in a thin API layer and adding a simple UI. Keeping the **backend (API)** separate from the **frontend (UI)** is standard practice: it makes the agent reusable across multiple clients and mirrors how production agents are deployed later in the series.

```mermaid
flowchart LR
  User[User] --> FE_UI

  subgraph Frontend
    FE_UI[Browser UI - Streamlit]
  end

  subgraph Backend
    API[FastAPI Backend]
    subgraph Agent_System[Agent System]
      Agent[Agent]
      Files[FAQ txt files]
    end
  end

  subgraph LLM_Service[LLM Service]
    LLM[Azure OpenAI Endpoint]
  end

  FE_UI -->|1. HTTP API call| API
  API -->|2. Forward question| Agent
  Agent -->|3. Tool call: lookup_faq| Files
  Files -->|4. Retrieved context| Agent
  Agent -->|5. LLM call| LLM
  LLM -->|6. Response| Agent
  Agent -->|7. Answer| API
  API -->|8. Response| FE_UI
```

**api.py**

```python
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
```

**streamlit.py**

```python
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
```

---

## Example run

```bash
# 1) Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 2) Install dependencies from requirements.txt
pip install -r requirements.txt

# 3) Create a .env file from the provided template and fill in your credentials
# .env is already listed in .gitignore — never commit real secrets to source control
cp .env.template .env
# Then open .env and replace the placeholder values with your Azure OpenAI details

# 4) Run the agent locally (CLI)
python agent.py

# 5) Start the API server (keep this running)
uvicorn api:app --reload

# 6) Test the API in a new terminal
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"When does release freeze start?\"}"

# 7) Run the Streamlit UI in another terminal
streamlit run streamlit.py
```

---

## Closing note

Try swapping the FAQ `.txt` files, add one more tool, and watch how the loop behaves. You can also tweak the **prompt**, change the **model deployment**, or adjust **temperature/max_tokens** to see how the agent's behaviour shifts. Keeping changes small and observable is the fastest way to get confident with agents.

**What's next:** in the next post we will focus on prompt engineering and explicit agent state to make behaviour predictable and debuggable.
