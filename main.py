from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta

app = FastAPI()

tasks = []

pomodoro_sessions = []
class Task(BaseModel):
    "title must exist and have between 3 and 100 chars"
    title: str = Field(..., min_length=3, max_length=100)
    "description doesnt have to exist"
    description: Optional[str] = Field(None, max_length=300)
    "regex for status"
    status: str = Field("TODO", pattern="^(TODO|in_progress|done)$")


class PomodoroSession(BaseModel):
    task_id: int
    start_time: datetime
    end_time: datetime
    completed: bool

"POST action, response is JSOn"
@app.post("/tasks", response_model=dict)
def create_task(task: Task):
    "check if title is unique"
    if any(t["title"] == task.title for t in tasks):
        raise HTTPException(status_code=400, detail="Task title must be unique.")

    "generate new unique id"
    task_id = len(tasks) + 1
    "convert Task instance to dict"
    task_data = task.dict()
    task_data["id"] = task_id
    tasks.append(task_data)
    return {"message": "Task created successfully", "task": task_data}

"GET action, returns tasks in dict"
@app.get("/tasks", response_model=List[dict])
def get_tasks(status: Optional[str] = Query(None, pattern="^(TODO|in_progress|done)$")):
    "filter through given status"
    if status:
        return [task for task in tasks if task["status"] == status]
    return tasks


@app.get("/tasks/{task_id}", response_model=dict)
def get_task(task_id: int):
    task = next((task for task in tasks if task["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task


@app.put("/tasks/{task_id}", response_model=dict)
def update_task(task_id: int, updated_task: Task):
    task = next((task for task in tasks if task["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    "check if title unique"
    if updated_task.title != task["title"] and any(t["title"] == updated_task.title for t in tasks):
        raise HTTPException(status_code=400, detail="Task title must be unique.")

    task.update(updated_task.dict())
    return {"message": "Task updated successfully", "task": task}


@app.delete("/tasks/{task_id}", response_model=dict)
def delete_task(task_id: int):
    global tasks
    task = next((task for task in tasks if task["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    tasks = [t for t in tasks if t["id"] != task_id]
    return {"message": "Task deleted successfully."}


@app.post("/pomodoro", response_model=dict)
def create_pomodoro(task_id: int):
    task = next((task for task in tasks if task["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    if any(session["task_id"] == task_id and not session["completed"] for session in pomodoro_sessions):
        raise HTTPException(status_code=400, detail="An active Pomodoro timer already exists for this task.")

    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=25)
    pomodoro_sessions.append({
        "task_id": task_id,
        "start_time": start_time,
        "end_time": end_time,
        "completed": False
    })
    return {"message": "Pomodoro timer created successfully.", "task_id": task_id}


@app.post("/pomodoro/{task_id}/stop", response_model=dict)
def stop_pomodoro(task_id: int):
    session = next(
        (session for session in pomodoro_sessions if session["task_id"] == task_id and not session["completed"]), None)
    if not session:
        raise HTTPException(status_code=400, detail="No active Pomodoro timer found for this task.")

    session["completed"] = True
    session["end_time"] = datetime.now()
    return {"message": "Pomodoro timer stopped successfully."}


@app.get("/pomodoro/stats", response_model=dict)
def get_pomodoro_stats():
    stats = {}
    for session in pomodoro_sessions:
        if session["completed"]:
            task_id = session["task_id"]
            if task_id not in stats:
                stats[task_id] = {"count": 0, "total_time": timedelta()}
            stats[task_id]["count"] += 1
            stats[task_id]["total_time"] += (session["end_time"] - session["start_time"])

    return {"pomodoro_stats": stats}
