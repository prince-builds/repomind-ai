"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routers import (
    architecture_router,
    files_router,
    interview_router,
    qa_router,
    repositories_router,
)
from backend.app.store import repository_store
from repomind import __version__


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context for startup warmup and graceful shutdown."""
    repository_store.warmup()
    yield


app = FastAPI(
    title="RepoMind AI REST API",
    description="REST API backend for RepoMind AI repository intelligence engine.",
    version=__version__,
    lifespan=lifespan,
)

# Enable CORS for Next.js frontend (default port 3000) and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(repositories_router)
app.include_router(architecture_router)
app.include_router(files_router)
app.include_router(qa_router)
app.include_router(interview_router)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "version": __version__}


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    """Root info endpoint."""
    return {
        "app": "RepoMind AI API",
        "version": __version__,
        "docs": "/docs",
    }
