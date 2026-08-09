from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# Our in-memory "database"
tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Learn FastAPI", "done": True},
    {"id": 3, "title": "Walk the dog", "done": False}
]

# Stage 1 Endpoints
@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Stage 2: Return all tasks
@app.get("/tasks")
def get_tasks():
    return tasks

# Stage 2: Return a single task by ID
@app.get("/tasks/{id}")
def get_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    # If the loop finishes and no task is found, return a 404 error
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})