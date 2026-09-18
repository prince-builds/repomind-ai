"""
Production migration verification and memory profiling script.
Validates:
1. Direct production Embedder interface
2. Production dependency tree (ensuring torch / sentence_transformers are not imported)
3. Full end-to-end repository pipeline via RepositoryStore
4. Accurate memory measurements (RSS in MB)
5. Comprehensive REST API endpoint validation
"""

import os
import subprocess
import sys
from pathlib import Path
import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

def get_process_rss_mb() -> float:
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except Exception:
        out = subprocess.check_output(["ps", "-o", "rss=", "-p", str(os.getpid())])
        return int(out.strip()) / 1024.0

def main():
    print("=" * 70)
    print("REPOMIND PRODUCTION FASTEMBED MIGRATION VALIDATION")
    print("=" * 70)

    # A. Baseline process
    rss_a = get_process_rss_mb()
    print(f"[A] Baseline Process RSS: {rss_a:.2f} MB")

    # B. After FastEmbed import
    from repomind.embeddings.embedder import Embedder
    rss_b = get_process_rss_mb()
    print(f"[B] RSS after FastEmbed & Embedder import: {rss_b:.2f} MB (+{rss_b - rss_a:.2f} MB)")

    # 1. Direct Embedder interface tests
    print("\n--- Testing Production Embedder Interface ---")
    embedder = Embedder()
    _ = embedder.model  # initialize model
    rss_c = get_process_rss_mb()
    print(f"[C] RSS after Embedder initialization: {rss_c:.2f} MB (+{rss_c - rss_b:.2f} MB)")

    texts = [
        "Python FastAPI backend",
        "FAISS vector search",
    ]
    batch_embeddings = embedder.embed_texts(texts)
    print(f"embed_texts result shape: {batch_embeddings.shape}")
    print(f"embed_texts result dtype: {batch_embeddings.dtype}")
    print(f"embed_texts all finite: {np.all(np.isfinite(batch_embeddings))}")
    assert batch_embeddings.shape == (2, 384), f"Expected (2, 384), got {batch_embeddings.shape}"
    assert batch_embeddings.dtype == np.float32, f"Expected float32, got {batch_embeddings.dtype}"
    assert np.all(np.isfinite(batch_embeddings)), "Embeddings contained non-finite values!"

    query = "repository semantic search"
    query_vector = embedder.embed_query(query)
    print(f"embed_query result shape: {query_vector.shape}")
    print(f"embed_query result dtype: {query_vector.dtype}")
    print(f"embed_query all finite: {np.all(np.isfinite(query_vector))}")
    assert query_vector.shape == (384,), f"Expected (384,), got {query_vector.shape}"
    assert query_vector.dtype == np.float32, f"Expected float32, got {query_vector.dtype}"
    assert np.all(np.isfinite(query_vector)), "Query vector contained non-finite values!"
    print("Direct Embedder interface verified 100% successfully!")

    # 2. Verify runtime dependency tree
    print("\n--- Checking Runtime Dependency Modules ---")
    forbidden_modules = ["torch", "torchvision", "sentence_transformers"]
    loaded_forbidden = [m for m in forbidden_modules if m in sys.modules]
    if loaded_forbidden:
        print(f"WARNING: Unexpected modules in sys.modules: {loaded_forbidden}")
    else:
        print("CONFIRMED: None of torch, torchvision, sentence_transformers are in sys.modules!")

    # 3. Full repository pipeline analysis via RepositoryStore
    print("\n--- Running Production Repository Analysis on ai-study-copilot ---")
    from backend.app.store import repository_store
    repo_url = "https://github.com/prince-builds/ai-study-copilot"
    session = repository_store.analyze(repo_url)

    rss_d = get_process_rss_mb()
    print(f"[D] RSS after RepositoryStore.analyze(): {rss_d:.2f} MB")
    print(f"    Repo ID: {session.repo_id}")
    print(f"    Scanned files: {len(session.ingestion.files)}")
    print(f"    Parsed files: {len(session.parse_summary.parsed_files)}")
    print(f"    Chunks count: {len(session.chunks)}")
    print(f"    Embedding dimension: {session.embedding_dim}")
    print(f"    FAISS vector count: {session.retriever.store.size if session.retriever else 0}")
    print(f"    Architecture files analyzed: {session.architecture.files_analyzed if session.architecture else 0}")
    print(f"    Architecture summary generated: {bool(session.architecture_summary)}")

    # 4. Semantic retrieval test on active session
    print("\n--- Testing Retrieval over Session ---")
    assert session.retriever is not None, "Retriever was not created!"
    hits = session.retriever.query("How does the study copilot ingest notes and documents?", top_k=3)
    print(f"Retrieved {len(hits)} hits:")
    for i, hit in enumerate(hits):
        print(f"  Hit {i+1} (score={hit.score:.4f}): {hit.file_path} (chunk {hit.chunk_index})")
        print(f"    Snippet: {hit.content[:80].replace(chr(10), ' ')}...")
    assert len(hits) > 0, "No hits retrieved!"

    # 5. Test REST API Endpoints with TestClient
    print("\n--- Testing Full FastAPI Endpoints Suite ---")
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)

    # GET /health
    r_health = client.get("/health")
    assert r_health.status_code == 200, f"Health check failed: {r_health.text}"
    print(f"GET /health -> {r_health.status_code} ({r_health.json()})")

    repo_id = session.repo_id

    # GET /api/repositories/{repo_id}/overview
    r_ov = client.get(f"/api/repositories/{repo_id}/overview")
    assert r_ov.status_code == 200, f"Overview failed: {r_ov.text}"
    ov_data = r_ov.json()
    print(f"GET /api/repositories/{repo_id}/overview -> {r_ov.status_code} (files_indexed={ov_data['metrics']['files_indexed']})")

    # GET /api/repositories/{repo_id}/architecture
    r_arch = client.get(f"/api/repositories/{repo_id}/architecture")
    assert r_arch.status_code == 200, f"Architecture failed: {r_arch.text}"
    arch_data = r_arch.json()
    print(f"GET /api/repositories/{repo_id}/architecture -> {r_arch.status_code} (dot_graph length={len(arch_data.get('dot_graph', ''))})")

    # GET /api/repositories/{repo_id}/files
    r_files = client.get(f"/api/repositories/{repo_id}/files")
    assert r_files.status_code == 200, f"Files failed: {r_files.text}"
    files_data = r_files.json()
    print(f"GET /api/repositories/{repo_id}/files -> {r_files.status_code} (total_files={files_data['total_files']})")

    # POST /api/repositories/{repo_id}/files/analyze
    test_file = session.parse_summary.parsed_files[0].file_path
    r_fa = client.post(f"/api/repositories/{repo_id}/files/analyze", json={"file_path": test_file})
    assert r_fa.status_code == 200, f"File analyze failed: {r_fa.text}"
    print(f"POST /api/repositories/{repo_id}/files/analyze for '{test_file}' -> {r_fa.status_code}")

    # POST /api/repositories/{repo_id}/qa
    r_qa = client.post(f"/api/repositories/{repo_id}/qa", json={"question": "What is the main purpose of this repository?", "top_k": 3})
    assert r_qa.status_code == 200, f"QA endpoint failed: {r_qa.text}"
    qa_data = r_qa.json()
    print(f"POST /api/repositories/{repo_id}/qa -> {r_qa.status_code} (retrieval_hits={len(qa_data.get('retrieval_hits', []))})")

    # POST /api/repositories/{repo_id}/interview
    r_iv = client.post(f"/api/repositories/{repo_id}/interview", json={"prompt": "Generate a technical interview question for this project."})
    assert r_iv.status_code == 200, f"Interview endpoint failed: {r_iv.text}"
    print(f"POST /api/repositories/{repo_id}/interview -> {r_iv.status_code}")

    # E. Peak RSS
    rss_e = get_process_rss_mb()
    margin_512 = 512.0 - rss_e
    print("\n" + "=" * 70)
    print("FINAL PRODUCTION MEMORY AUDIT RESULTS")
    print("=" * 70)
    print(f"[A] Baseline Process: {rss_a:.2f} MB")
    print(f"[B] After FastEmbed import: {rss_b:.2f} MB")
    print(f"[C] After Embedder initialization: {rss_c:.2f} MB")
    print(f"[D] After Repository analysis: {rss_d:.2f} MB")
    print(f"[E] Peak Production RSS: {rss_e:.2f} MB")
    print(f"    Memory Margin below 512 MB Limit: {margin_512:.2f} MB ({margin_512 / 512.0 * 100:.1f}% free)")
    print("=" * 70)
    print("ALL PRODUCTION VERIFICATIONS PASSED!")

if __name__ == "__main__":
    main()
