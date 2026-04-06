from fastapi import FastAPI

app = FastAPI()

@app.get("/person2/ready")
def ready():
    return {"status": "person2 ready"}

@app.get("/person2/status")
def status():
    return {"status": "running"}

@app.get("/person2/health")
def health():
    return {"health": "ok"}