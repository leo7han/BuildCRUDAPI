FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# We use port 3000 here to match the assignment's compose file
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]