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
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})

# Stage 3: Create a new task (The missing piece!)
@app.post("/tasks")
def create_task(payload: dict):
    # 1. Validation
    title = payload.get("title", "").strip()
    if not title:
        return JSONResponse(
            status_code=400, 
            content={"error": "Title is required and cannot be empty"}
        )
    
    # 2. Find the next free ID
    next_id = max(task["id"] for task in tasks) + 1 if tasks else 1
    
    # 3. Create the new task
    new_task = {
        "id": next_id,
        "title": title,
        "done": False
    }
    
    # 4. Add it to the list and return 201 Created
    tasks.append(new_task)
    return JSONResponse(status_code=201, content=new_task)