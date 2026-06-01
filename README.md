# RepoMind AI

AI-powered repository understanding and architecture explanation.

## Tech stack

- Python 3.11
- Streamlit
- FAISS
- sentence-transformers
- GitPython
- Groq (LLM — free tier at [console.groq.com](https://console.groq.com))

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` with your keys. Set `GROQ_API_KEY` from [Groq Console](https://console.groq.com) for repository Q&A and architecture summaries.

## Run

```bash
streamlit run app.py
```

## Project layout

| Module | Role |
|--------|------|
| `ingestion/` | Clone repos, scan and filter files |
| `parsing/` | Parse source into structures |
| `chunking/` | Split content for retrieval |
| `embeddings/` | Vectorize chunks |
| `retrieval/` | FAISS similarity search |
| `architecture/` | Repo structure and dependency views |
| `explanations/` | Human-readable summaries |
| `llm/` | Groq prompts and chat completions |
| `ui/` | Streamlit interface |
| `utils/` | Shared helpers and config |
| `data/` | Local indexes and caches |

## Pipeline

```
GitHub URL → clone → scan → parse → chunk → embed → FAISS → architecture → Groq Q&A
```

## License

MIT
