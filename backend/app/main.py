from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, clothing, outfits
from app.services import minio_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure MinIO bucket exists
    try:
        minio_service.ensure_bucket()
    except Exception as exc:
        print(f"WARNING: Could not ensure MinIO bucket: {exc}")
    yield
    # Shutdown: nothing to clean up


app = FastAPI(
    title="WardrobeAI API",
    version="1.0.0",
    lifespan=lifespan,
)

origins = ["http://localhost:5173", "http://localhost:80", "http://localhost"]
if settings.environment == "production":
    # In prod, nginx serves frontend on port 80 — same origin after proxy
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(clothing.router, prefix="/api/v1")
app.include_router(outfits.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/ready")
async def ready():
    from app.database import engine
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    minio_ok = True
    try:
        minio_service.get_client().bucket_exists(settings.minio_bucket)
    except Exception:
        minio_ok = False

    if not db_ok or not minio_ok:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail={"db": db_ok, "minio": minio_ok})

    return {"status": "ready", "db": True, "minio": True}
