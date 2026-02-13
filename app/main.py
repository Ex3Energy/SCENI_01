from fastapi import FastAPI

app = FastAPI(title="SCENI_01 API", version="0.1.0")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"service": "SCENI_01", "status": "ok"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"health": "up"}
