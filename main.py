import os
import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Depends
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

class UserCredentials(BaseModel):
    email: str
    password: str

    @field_validator("email", "password")
    @classmethod   
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty")
        return v


# ---- Validation error -> 400 (spec requires 400, FastAPI defaults to 422) ----
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid request body"},
    )

# ---- Reshape HTTPException output so it matches the {"error": "..."} shape the spec wants ----
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


# ---- Stage 1: Auth Endpoints ----
@app.post("/auth/signup", status_code=201)
def signup(credentials: UserCredentials):
    try:
        # Register the user in Supabase
        res = supabase.auth.sign_up({
            "email": credentials.email,
            "password": credentials.password
        })
        # Return the user object
        return res.user.model_dump() if res.user else {}
    except Exception as e:
        # Catch errors like "User already exists"
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.post("/auth/login", status_code=200)
def login(credentials: UserCredentials):
    try:
        # Authenticate with Supabase
        res = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        # Return the Access Token (JWT) and Refresh Token
        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token
        }
    except Exception:
        # If Supabase rejects the credentials, return a 401 Unauthorized
        return JSONResponse(
            status_code=401, 
            content={"error": "Invalid login credentials"}
        )


# ---- Stage 2: Public endpoint ----
@app.get("/public/info")
def public_info():
    # No auth required — anyone can hit this
    return {"message": "Welcome stranger! This info is public."}


# ---- Stage 4: Reusable auth guard (FastAPI dependency) ----
# This replaces the token-checking that used to be pasted directly into
# protected_profile. Any route that adds `Depends(get_current_user)` gets
# the exact same guard, without duplicating the logic.
def get_current_user(authorization: str = Header(None)):
    # Stage 2 check: was a bearer token even presented?
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"error": "Access token required"})

    token = authorization.split(" ")[1]

    # Stage 3 check: is the token actually valid? This calls Supabase over
    # the network, so a "yes" here is trustworthy — not just decoded locally.
    try:
        res = supabase.auth.get_user(token)
        if not res or not res.user:
            raise HTTPException(status_code=401, detail={"error": "Invalid or expired token"})
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "Invalid or expired token"})

    # Attach both the verified user and their raw token — logout needs the token itself.
    return {"user": res.user, "token": token}


# ---- Stage 3: Protected profile route, now guarded by the dependency ----
@app.get("/protected/profile")
def protected_profile(current=Depends(get_current_user)):
    return current["user"].model_dump()


# ---- Stage 4: Second protected route — proves the guard is reusable, no new auth code ----
@app.get("/protected/dashboard")
def protected_dashboard(current=Depends(get_current_user)):
    return {"message": f"Welcome back, {current['user'].email}! This is your dashboard."}


# ---- Stage 4: Logout — also guarded, so only a logged-in user can log out ----
@app.post("/auth/logout", status_code=204)
def logout(current=Depends(get_current_user)):
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    return


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