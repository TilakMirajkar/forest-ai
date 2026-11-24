from fastapi import FastAPI

from forest_ai.routers import auth, entries, moods, insights

app = FastAPI(
    title="Forest AI",
    description="An AI-powered Journal API.",
    version="0.1.0"
)
app.include_router(auth.router)
app.include_router(entries.router)
app.include_router(moods.router)
app.include_router(insights.router)

@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}