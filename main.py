from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="PIXNET 自動發文系統",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "PIXNET 自動發文系統已啟動",
        "docs": "/docs"
    }

@app.get("/healthz")
def healthz():
    return JSONResponse({"ok": True})

@app.post("/post_article")
def post_article():
    return {"status": "ok", "detail": "已觸發發文（示範）"}
