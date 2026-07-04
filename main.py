from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from database import init_db, close_db
from auth import router as auth_router
from routes.ingest import router as ingest_router
from routes.ask import router as ask_router
from routes.feedback import router as feedback_router
from routes.profile import router as profile_router
from routes.mock_interview import router as mock_interview_router
from routes.compare import router as compare_router
from routes.roadmap import router as roadmap_router
from routes.visualize import router as visualize_router
from routes.company import router as company_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Interview Brain",
    description="AI-powered interview preparation platform backed by Cognee knowledge graphs",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(ingest_router)
app.include_router(ask_router)
app.include_router(feedback_router)
app.include_router(profile_router)
app.include_router(mock_interview_router)
app.include_router(compare_router)
app.include_router(roadmap_router)
app.include_router(visualize_router)
app.include_router(company_router)


# ── Root redirect ────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "healthy"}


# ── Static files (MUST be after API routes so /api/* isn't shadowed) ─────────

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    import config as cfg

    uvicorn.run("main:app", host=cfg.HOST, port=cfg.PORT, reload=True)
