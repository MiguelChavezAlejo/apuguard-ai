from fastapi import FastAPI

app = FastAPI(
    title="ApuGuard AI",
    version="0.1.0"
)

@app.get("/")
def root():
    return {
        "name": "ApuGuard AI",
        "status": "running",
        "version": "0.1.0"
    }