import asyncio
from fastapi import FastAPI
from pydantic import BaseModel

from agent import ask_agent

app = FastAPI()

class Query(BaseModel):
    question: str

@app.post("/ask")
async def ask(query: Query):
    answer = await ask_agent(query.question)
    return {"answer": answer}