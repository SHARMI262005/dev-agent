import os

os.makedirs("broken-app", exist_ok=True)

files = {
    "broken-app/main.py": '''from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy"}
''',
    "broken-app/requirements.txt": "fastapi\n",
    "broken-app/Dockerfile": '''FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
''',
}

for path, content in files.items():
    with open(path, "w") as f:
        f.write(content)
    print("created", path)