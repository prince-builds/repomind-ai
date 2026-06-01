"""Load settings from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
# Host only — the Groq SDK appends paths such as /openai/v1/chat/completions.
DEFAULT_GROQ_BASE_URL = "https://api.groq.com"

_OPENAI_V1_SUFFIX = "/openai/v1"


def normalize_groq_base_url(url: str) -> str:
    """Strip a duplicated /openai/v1 suffix so SDK paths are not doubled."""
    cleaned = url.strip().rstrip("/")
    if cleaned.endswith(_OPENAI_V1_SUFFIX):
        cleaned = cleaned[: -len(_OPENAI_V1_SUFFIX)]
    return cleaned.rstrip("/") or DEFAULT_GROQ_BASE_URL


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    groq_model: str
    groq_base_url: str
    github_token: str
    embedding_model: str
    data_dir: Path


def get_settings() -> Settings:
    return Settings(
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        groq_model=os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL),
        groq_base_url=normalize_groq_base_url(
            os.getenv("GROQ_BASE_URL", DEFAULT_GROQ_BASE_URL)
        ),
        github_token=os.getenv("GITHUB_TOKEN", ""),
        embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        data_dir=Path(os.getenv("DATA_DIR", "repomind/data")),
    )
