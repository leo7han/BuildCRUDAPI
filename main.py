import os
import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

# NEW: Import the Supabase client
from supabase import create_client, Client

# Load secrets from your .env file
load_dotenv() 

# ---- Stage 0: Supabase Setup ----
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

# NEW: Add startup event for Stage 0 checkpoint
@app.on_event("startup")
async def startup_event():
    print("Server running and connected to Supabase")

# ---- Stage 1: Postgres Setup ----
# Helper function to get a fresh connection for each request
def get_db_connection():
    return psycopg.connect(os.environ["DATABASE_URL"])

# Initialize the database on startup
with get_db_connection() as conn:
    with conn.cursor() as cursor:
        # Create the tasks table if it is missing (using SERIAL for auto-increment in Postgres)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                done BOOLEAN DEFAULT FALSE
            )
        """)
        conn.commit()
        
        # Seed three example tasks only if the table is completely empty
        cursor.execute("SELECT COUNT(*) FROM tasks")
        if cursor.fetchone()[0] == 0:
            example_tasks = [
                ("Buy groceries", False),
                ("Learn FastAPI", True),
                ("Walk the dog", False)
            ]
            # Use %s for psycopg parameter placeholders
            cursor.executemany("INSERT INTO tasks (title, done) VALUES (%s, %s)", example_tasks)
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
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Fetch all rows from the Postgres database
            cursor.execute("SELECT * FROM tasks ORDER BY id ASC")
            rows = cursor.fetchall()
            
            # Convert the raw database rows into a list of dictionaries
            tasks_list = []
            for row in rows:
                tasks_list.append({"id": row[0], "title": row[1], "done": row[2]})
            return tasks_list


@app.get("/tasks/{id}")
def get_task(id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # We use a parameterized query (%s) to safely find the specific ID
            cursor.execute("SELECT * FROM tasks WHERE id=%s", (id,))
            row = cursor.fetchone()
            
            # If a row was found, return it
            if row:
                return {"id": row[0], "title": row[1], "done": row[2]}
                
            # If no row was found, return a 404 error
            return JSONResponse(status_code=404, content={"error": "Task not found"})


# ---- Stage 3: Create (Database) ----
@app.post("/tasks", status_code=201)
def create_task(task: Task):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Insert the new task and use RETURNING id to get the generated Postgres ID
            cursor.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id", 
                (task.title, task.done)
            )
            new_id = cursor.fetchone()[0]
            conn.commit()
            
            # Return the newly created task
            return {"id": new_id, "title": task.title, "done": task.done}


# ---- Stage 3: Update and Delete (Database) ----
@app.put("/tasks/{id}")
def update_task(id: int, task: Task):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Update the task in the database
            cursor.execute(
                "UPDATE tasks SET title=%s, done=%s WHERE id=%s", 
                (task.title, task.done, id)
            )
            conn.commit()
            
            # cursor.rowcount tells us how many rows were modified
            if cursor.rowcount == 0:
                return JSONResponse(status_code=404, content={"error": "Task not found"})
                
            return {"id": id, "title": task.title, "done": task.done}


@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Delete the task from the database
            cursor.execute("DELETE FROM tasks WHERE id=%s", (id,))
            conn.commit()
            
            if cursor.rowcount == 0:
                return JSONResponse(status_code=404, content={"error": "Task not found"})
                
            return