from fastapi import FastAPI

app = FastAPI(
    title="Forest AI",
    description="An AI-powered Journal API.",
    version="0.1.0"
)

@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}