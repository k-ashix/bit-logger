from fastapi import FastAPI

app = FastAPI(
    title="Bit-Logger API",
    description="AI-powered Bitcoin transaction traffic monitoring and analysis platform",
    version="0.1.0",
)


@app.get("/health", tags=["System"])
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "bit-logger-api",
    }


@app.get("/ready", tags=["System"])
async def ready() -> dict[str, str]:
    return {
        "status": "ready",
        "service": "bit-logger-api",
    }


@app.get("/api/v1", tags=["System"])
async def api_v1() -> dict[str, str]:
    return {
        "api": "v1",
        "status": "active",
    }