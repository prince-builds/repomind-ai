"""
Temporary experimental test script for FastEmbed migration validation.
Does NOT modify any production code or RepositoryStore.
"""

import os
import sys

# Allow OpenMP duplicate for local macOS testing of torch + onnxruntime side-by-side
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import subprocess
from pathlib import Path
import numpy as np

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

# Helper for memory measurement (RSS in MB)
def get_process_rss_mb() -> float:
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except Exception:
        out = subprocess.check_output(["ps", "-o", "rss=", "-p", str(os.getpid())])
        return int(out.strip()) / 1024.0

def main():
    print("=" * 60)
    print("FASTEMBED MIGRATION EXPERIMENTAL VALIDATION")
    print("=" * 60)

    # 1. Baseline Memory
    rss_baseline = get_process_rss_mb()
    print(f"[1] Process Baseline RSS: {rss_baseline:.2f} MB")

    # 2. Import FastEmbed
    import fastembed
    from fastembed import TextEmbedding
    rss_after_import = get_process_rss_mb()
    print(f"[2] FastEmbed Version: {fastembed.__version__}")
    print(f"    RSS after importing FastEmbed: {rss_after_import:.2f} MB (+{rss_after_import - rss_baseline:.2f} MB)")

    # 3. Load Model
    model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    rss_after_model = get_process_rss_mb()
    print(f"[3] Model Loaded: sentence-transformers/all-MiniLM-L6-v2")
    print(f"    RSS after loading TextEmbedding: {rss_after_model:.2f} MB (+{rss_after_model - rss_after_import:.2f} MB)")

    # 4. Generate Embeddings for Test Sentences
    test_texts = [
        "Python FastAPI backend",
        "React frontend application",
        "FAISS vector search",
        "repository semantic search",
        "user authentication system",
    ]
    
    # FastEmbed returns a generator of numpy arrays
    embeddings_gen = model.embed(test_texts)
    embeddings_list = list(embeddings_gen)
    embeddings_np = np.asarray(embeddings_list, dtype=np.float32)

    rss_after_embed = get_process_rss_mb()
    print(f"[4] Embeddings Generated for {len(test_texts)} sentences")
    print(f"    RSS after embedding test texts: {rss_after_embed:.2f} MB")
    print(f"    Shape: {embeddings_np.shape}")
    print(f"    Dtype: {embeddings_np.dtype}")
    print(f"    Embedding Dimension: {embeddings_np.shape[1]}")
    print(f"    All finite (no NaN/inf): {np.all(np.isfinite(embeddings_np))}")
    print(f"    Convertible to float32 NumPy: {isinstance(embeddings_np, np.ndarray) and embeddings_np.dtype == np.float32}")

    # 5. FAISS Retrieval Compatibility Test
    print("\n" + "=" * 60)
    print("FAISS RETRIEVAL COMPATIBILITY TEST")
    print("=" * 60)
    import faiss

    # Normalize FastEmbed vectors
    index_vectors = embeddings_np.copy()
    faiss.normalize_L2(index_vectors)

    dimension = index_vectors.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(index_vectors)
    print(f"FAISS IndexFlatIP created with dimension={index.d}, total vectors={index.ntotal}")

    # Search with a test query
    query_text = "FastAPI backend REST endpoints"
    query_gen = model.embed([query_text])
    query_vector = np.asarray(list(query_gen)[0], dtype=np.float32).reshape(1, -1)
    faiss.normalize_L2(query_vector)

    scores, indices = index.search(query_vector, 3)
    print(f"Query: '{query_text}'")
    print(f"Top-3 Results:")
    for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
        print(f"  Rank {rank+1}: idx={idx}, score={score:.4f}, text='{test_texts[idx]}'")

    assert indices[0][0] == 0, f"Expected top match to be 'Python FastAPI backend' (idx 0), got idx {indices[0][0]}"
    print("FAISS search verified successfully!")

    # 6. Isolated Full Pipeline Test on ai-study-copilot
    print("\n" + "=" * 60)
    print("FULL PIPELINE TEST ON ai-study-copilot REPOSITORY")
    print("=" * 60)

    repo_dir = WORKSPACE_ROOT / "repomind" / "data" / "repos" / "prince-builds-ai-study-copilot"
    if not repo_dir.exists():
        repos = list((WORKSPACE_ROOT / "repomind" / "data" / "repos").glob("*ai-study-copilot*"))
        if repos:
            repo_dir = repos[0]

    print(f"Testing on repository at: {repo_dir}")

    from repomind.ingestion.file_scanner import scan_repository
    from repomind.parsing.parser import parse_repository
    from repomind.chunking.chunker import chunk_parsed_files

    scanned_files = scan_repository(repo_dir)
    parse_summary = parse_repository(repo_dir, scanned_files, "ai-study-copilot")
    chunks = chunk_parsed_files(parse_summary.parsed_files)
    print(f"Files scanned: {len(scanned_files)}")
    print(f"Files parsed: {len(parse_summary.parsed_files)}")
    print(f"Total Chunks created: {len(chunks)}")

    # Embed all chunks using FastEmbed
    chunk_texts = [c.content for c in chunks]
    fe_chunk_embeddings = np.asarray(list(model.embed(chunk_texts, batch_size=32)), dtype=np.float32)
    print(f"FastEmbed chunk embeddings shape: {fe_chunk_embeddings.shape}")
    print(f"Embedding dimension: {fe_chunk_embeddings.shape[1]}")
    print(f"Vector count: {fe_chunk_embeddings.shape[0]}")

    # Build FAISS index
    faiss_chunks = fe_chunk_embeddings.copy()
    faiss.normalize_L2(faiss_chunks)
    repo_index = faiss.IndexFlatIP(fe_chunk_embeddings.shape[1])
    repo_index.add(faiss_chunks)
    print(f"Repository FAISS Index built with {repo_index.ntotal} vectors.")

    # Test retrieval queries
    test_queries = [
        "Where is the main entry point or UI defined?",
        "How are documents or study notes ingested?",
        "What model or LLM API is used for answering questions?",
    ]

    for q in test_queries:
        q_vec = np.asarray(list(model.embed([q]))[0], dtype=np.float32).reshape(1, -1)
        faiss.normalize_L2(q_vec)
        q_scores, q_indices = repo_index.search(q_vec, 2)
        print(f"\nQuery: '{q}'")
        for r, (sc, idx) in enumerate(zip(q_scores[0], q_indices[0])):
            matched_chunk = chunks[idx]
            print(f"  Hit {r+1} (score={sc:.4f}): {matched_chunk.file_path} (chunk {matched_chunk.chunk_index})")
            snippet = matched_chunk.content[:100].replace('\n', ' ')
            print(f"    Snippet: {snippet}...")

    rss_repo_analyzed = get_process_rss_mb()
    print("\n" + "-" * 50)
    print(f"Peak RSS for FastEmbed + Full Repo Analyzed: {rss_repo_analyzed:.2f} MB")
    print("-" * 50)

    # 7. Compare against SentenceTransformer (isolated comparison)
    print("\n" + "=" * 60)
    print("COMPARISON: FastEmbed vs SentenceTransformer (PyTorch)")
    print("=" * 60)
    
    rss_before_torch = get_process_rss_mb()
    from sentence_transformers import SentenceTransformer
    st_model = SentenceTransformer("all-MiniLM-L6-v2")
    st_embeddings = st_model.encode(test_texts, convert_to_numpy=True, show_progress_bar=False)
    st_embeddings_np = np.asarray(st_embeddings, dtype=np.float32)
    rss_after_torch = get_process_rss_mb()
    
    print(f"SentenceTransformer loaded.")
    print(f"ST Shape: {st_embeddings_np.shape}, ST Dtype: {st_embeddings_np.dtype}")

    print("\nPairwise Vector Comparison (for 5 test sentences):")
    for i, text in enumerate(test_texts):
        v_fe = embeddings_np[i]
        v_st = st_embeddings_np[i]

        norm_fe = v_fe / (np.linalg.norm(v_fe) + 1e-12)
        norm_st = v_st / (np.linalg.norm(v_st) + 1e-12)

        cos_sim = float(np.dot(norm_fe, norm_st))
        max_diff = float(np.max(np.abs(norm_fe - norm_st)))
        mean_diff = float(np.mean(np.abs(norm_fe - norm_st)))

        print(f"  Sentence [{i+1}] '{text}':")
        print(f"    Cosine Similarity: {cos_sim:.8f}")
        print(f"    Max Absolute Diff (normalized): {max_diff:.6e}")
        print(f"    Mean Absolute Diff (normalized): {mean_diff:.6e}")

    print("\n" + "=" * 60)
    print("ALL EXPERIMENTAL VALIDATIONS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
