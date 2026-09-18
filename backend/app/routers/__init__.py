"""FastAPI routers package."""

from backend.app.routers.architecture import router as architecture_router
from backend.app.routers.files import router as files_router
from backend.app.routers.interview import router as interview_router
from backend.app.routers.qa import router as qa_router
from backend.app.routers.repositories import router as repositories_router

__all__ = [
    "repositories_router",
    "architecture_router",
    "files_router",
    "qa_router",
    "interview_router",
]
