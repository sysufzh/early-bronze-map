from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.middleware import SlowAPIMiddleware

from .config import settings
from .database import engine, Base
from .limiter import limiter
from .routers import artifacts, map as map_router, auth

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="中国早期铜器数据库", version="0.1.0")
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(artifacts.router)
app.include_router(map_router.router)
app.include_router(auth.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
