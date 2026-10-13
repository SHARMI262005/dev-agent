from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/")
def home():
    return {"message": "Hello from sample app"}
