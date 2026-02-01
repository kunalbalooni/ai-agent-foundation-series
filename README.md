# AI Agents Blog Series

This repository is an **educational, code‑first blog series** that teaches how to build AI agents step‑by‑step—starting from LLM fundamentals and progressing to a production‑ready, enterprise‑grade system. Each blog introduces only the theory required to justify the code that follows and builds on a single evolving use case.

## Objective
Create a practical, code‑first series that explains not just **how** to build agents, but **why** each architectural step is necessary.

## Core Approach

- One realistic enterprise use case improved incrementally across blogs
- Theory first (only what’s necessary), then functional code
- Dev‑first implementation, production covered at the end
- Framework‑agnostic concepts, concrete implementation using **Semantic Kernel**

## Blog Outline & Intent

1. **[From LLMs to AI Agents — Why a Prompt Is Not Enough](blogs/blog-01-from-llms-to-agents/blog.md)**
   Explains how LLMs differ from agents (state, tools, control loops), surveys agent frameworks, and implements the first minimal agent using Semantic Kernel as a concrete example.

2. **Controlling Agent Behaviour — Prompt Engineering and State**
   Introduces prompts as control mechanisms (not text generation) and shows how explicit agent state enables predictable, debuggable behaviour.

3. **Teaching the Agent to Use Knowledge — Retrieval‑Augmented Generation (RAG)**
   Demonstrates why context windows are insufficient and adds document retrieval to ground agent responses in enterprise knowledge.

4. **Teaching the Agent to Act — Tools, APIs, and Data Access**
   Extends the agent with tools so it can take actions (search, data access, drafting outputs) instead of only responding in text.

5. **When a Single Agent Breaks — Introducing Multi‑Agent Systems**
   Shows practical failure modes of a single agent (context overload, conflicting goals) and motivates the need for multiple specialised agents.

6. **Coordinating Multiple Agents — Orchestration, State, and Control**
   Implements a multi‑agent workflow with clear roles, orchestration logic, and controlled state sharing.

7. **From Development to Production — Architecture, Security, and Governance**
   Covers what changes when moving to production: deployment architecture, security boundaries, identity, observability, and cost control.

8. **Production Deep Dives (Optional Follow‑ups)**
   Branch blogs covering implementation details such as Azure deployment, Azure AD integration, RBAC/RLS, monitoring, and evaluation.

## Outcome
By the end of the series, readers will understand not only how to build AI agents, but why each architectural step is necessary—culminating in a production‑ready, enterprise‑grade AI agent.
