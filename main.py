from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

app = FastAPI()


# ---- Data model ----
class Task(BaseModel):
    title: str
    done: bool = False

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title cannot be empty")
        return v


# ---- In-memory "database" ----
tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Learn FastAPI", "done": True},
    {"id": 3, "title": "Walk the dog", "done": False},
]


# ---- Validation error -> 400 (spec requires 400, FastAPI defaults to 422) ----
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid request body"},
    )


# ---- Stage 1: Root + health ----
@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ---- Stage 2: Read endpoints ----
@app.get("/tasks")
def get_tasks():
    return tasks


@app.get("/tasks/{id}")
def get_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {id} not found")


# ---- Stage 3: Create ----
@app.post("/tasks", status_code=201)
def create_task(task: Task):
    new_id = max((t["id"] for t in tasks), default=0) + 1
    new_task = {"id": new_id, "title": task.title, "done": task.done}
    tasks.append(new_task)
    return new_task


# ---- Stage 4: Update + Delete ----
@app.put("/tasks/{id}")
def update_task(id: int, task: Task):
    for existing in tasks:
        if existing["id"] == id:
            existing["title"] = task.title
            existing["done"] = task.done
            return existing
    raise HTTPException(status_code=404, detail=f"Task {id} not found")


@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    for existing in tasks:
        if existing["id"] == id:
            tasks.remove(existing)
            return
    raise HTTPException(status_code=404, detail=f"Task {id} not found")