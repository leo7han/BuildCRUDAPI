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

# Stage 2: Read Endpoints
@app.get("/tasks")
def get_tasks():
    return tasks

@app.get("/tasks/{id}")
def get_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})

# Stage 3: Create Endpoint
@app.post("/tasks")
def create_task(payload: dict):
    title = payload.get("title", "").strip()
    if not title:
        return JSONResponse(
            status_code=400, 
            content={"error": "Title is required and cannot be empty"}
        )
    
    next_id = max(task["id"] for task in tasks) + 1 if tasks else 1
    new_task = {
        "id": next_id,
        "title": title,
        "done": False
    }
    tasks.append(new_task)
    return JSONResponse(status_code=201, content=new_task)

# Stage 4: Update Endpoint
@app.put("/tasks/{id}")
def update_task(id: int, payload: dict):
    title = payload.get("title", "").strip()
    if not title:
        return JSONResponse(
            status_code=400, 
            content={"error": "Title is required and cannot be empty"}
        )
    
    for task in tasks:
        if task["id"] == id:
            task["title"] = title
            if "done" in payload:
                task["done"] = payload["done"]
            return task
            
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})

# Stage 4: Delete Endpoint
@app.delete("/tasks/{id}")
def delete_task(id: int):
    for index, task in enumerate(tasks):
        if task["id"] == id:
            del tasks[index]
            return JSONResponse(status_code=204, content=None)
            
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})