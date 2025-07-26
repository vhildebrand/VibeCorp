# api/main.py

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Task(BaseModel):
    prompt: str

@app.post("/start_task")
async def start_task(task: Task):
    # This will later initiate the AutoGen group chat
    return {"message": "Task received!", "task_id": "dummy_task_id"}

@app.get("/get_conversation_history/{task_id}")
async def get_conversation_history(task_id: str):
    # This will later return the conversation history
    return {"task_id": task_id, "history": []}

@app.get("/get_latest_update/{task_id}")
async def get_latest_update(task_id: str):
    # This will later return new messages
    return {"task_id": task_id, "new_messages": []}
