from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import engine, Base
from .routers import artifacts, map as map_router, tiles, auth

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="中国早期铜器数据库", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(artifacts.router)
app.include_router(map_router.router)
app.include_router(tiles.router)
app.include_router(auth.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/api/health")
def health():
    return {"status": "ok"}
