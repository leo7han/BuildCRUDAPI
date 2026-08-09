# BuildCRUDAPI

A simple in-memory Task API built with **FastAPI**. It supports full CRUD (Create, Read, Update, Delete) on a list of tasks, with input validation, correct HTTP status codes, and interactive API docs via Swagger UI. No database — tasks are stored in memory and reset when the server restarts.

## Install & Run

```bash
pip install fastapi uvicorn
uvicorn main:app --reload
```

The server runs on `http://localhost:8000`. Interactive docs are available at `http://localhost:8000/docs`.

## Endpoints

| Method | Path          | Description                          |
|--------|---------------|---------------------------------------|
| GET    | `/`           | API info                              |
| GET    | `/health`     | Health check                          |
| GET    | `/tasks`      | List all tasks                        |
| GET    | `/tasks/{id}` | Get a single task by id               |
| POST   | `/tasks`      | Create a new task                     |
| PUT    | `/tasks/{id}` | Update an existing task               |
| DELETE | `/tasks/{id}` | Delete a task                         |

## Status Codes

| Code | Meaning                                    |
|------|---------------------------------------------|
| 200  | Successful GET/PUT                          |
| 201  | Task created                                |
| 204  | Task deleted                                |
| 400  | Invalid request body (e.g. missing/empty title) |
| 404  | Task with given id not found                |

## Example Request

```bash
curl -i http://localhost:8000/tasks
```

```
HTTP/1.1 200 OK
date: Sun, 09 Aug 2026 08:57:34 GMT
server: uvicorn
content-length: 118
content-type: application/json

[
  {"id": 1, "title": "Buy groceries", "done": false},
  {"id": 2, "title": "Learn FastAPI", "done": true},
  {"id": 3, "title": "Walk the dog", "done": false}
]
```

## Swagger UI

All endpoints are documented and testable at `/docs`:

![Swagger UI](docs-screenshot.png)

## Notes

This project has no database — all data lives in memory and resets when the server restarts.
