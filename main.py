import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

app = FastAPI()

# ---- Stage 0: SQLite Setup ----
# Open connection (this magically creates tasks.db if it doesn't exist)
conn = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = conn.cursor()

# Create the tasks table if it is missing
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        done INTEGER DEFAULT 0
    )
""")
conn.commit()

# Seed three example tasks only if the table is completely empty
cursor.execute("SELECT COUNT(*) FROM tasks")
if cursor.fetchone()[0] == 0:
    example_tasks = [
        ("Buy groceries", 0),
        ("Learn FastAPI", 1),
        ("Walk the dog", 0)
    ]
    cursor.executemany("INSERT INTO tasks (title, done) VALUES (?, ?)", example_tasks)
    conn.commit()


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
# (We will delete this list in Stage 1, but leave it here for now!)
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


# ---- Stage 2: Read endpoints (Database) ----
@app.get("/tasks")
def get_tasks():
    cursor = conn.cursor()
    # Fetch all rows from the database
    cursor.execute("SELECT * FROM tasks")
    rows = cursor.fetchall()
    
    # Convert the raw database rows into a list of dictionaries
    tasks_list = []
    for row in rows:
        tasks_list.append({"id": row[0], "title": row[1], "done": bool(row[2])})
    return tasks_list


@app.get("/tasks/{id}")
def get_task(id: int):
    cursor = conn.cursor()
    # We use a parameterized query (?) to safely find the specific ID
    cursor.execute("SELECT * FROM tasks WHERE id=?", (id,))
    row = cursor.fetchone()
    
    # If a row was found, return it
    if row:
        return {"id": row[0], "title": row[1], "done": bool(row[2])}
        
    # If no row was found, return our exact Assignment 1 error
    return JSONResponse(status_code=404, content={"error": "Task not found"})


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