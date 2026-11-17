import google.generativeai as genai
import json
import math
import time
from app.core.config import supabase, settings
from app.services.embeddings import generate_embedding, normalize_and_slice_vector

# Modern google-genai client
modern_client = None
try:
    from google import genai as modern_genai
    modern_client = modern_genai.Client(api_key=settings.GEMINI_API_KEY)
except Exception as e:
    print(f"[RAG] Modern google-genai client not available: {e}")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# In-memory chunk cache
_CHUNKS_CACHE = None
_CACHE_TIME = 0
_CACHE_TTL = 300  # 5 minutes TTL

def invalidate_chunks_cache():
    """Call this when a new document is uploaded or deleted."""
    global _CHUNKS_CACHE, _CACHE_TIME
    _CHUNKS_CACHE = None
    _CACHE_TIME = 0
    print("[RAG Cache] Cache invalidated.")

def parse_vector(v):
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            try:
                return [float(x) for x in v.strip("[]").split(",") if x.strip()]
            except Exception:
                return []
    return []

def get_cached_chunks(force_refresh=False):
    """Retrieve all chunks from memory cache or load from Supabase."""
    global _CHUNKS_CACHE, _CACHE_TIME
    now = time.time()
    if not force_refresh and _CHUNKS_CACHE is not None and (now - _CACHE_TIME < _CACHE_TTL):
        return _CHUNKS_CACHE

    try:
        t0 = time.time()
        res = supabase.table("document_chunks").select(
            "id, document_id, page_number, content, embedding, documents(file_name, uploaded_by)"
        ).execute()
        raw = res.data or []
        parsed = []
        for ch in raw:
            f_name = "Document"
            uploaded_by = None
            if isinstance(ch.get("documents"), dict):
                f_name = ch["documents"].get("file_name", "Document")
                uploaded_by = ch["documents"].get("uploaded_by")
            parsed.append({
                "id": str(ch.get("id")),
                "document_id": str(ch.get("document_id")),
                "file_name": f_name,
                "uploaded_by": str(uploaded_by) if uploaded_by else None,
                "page_number": ch.get("page_number", 1),
                "content": ch.get("content", ""),
                "embedding": parse_vector(ch.get("embedding"))
            })
        _CHUNKS_CACHE = parsed
        _CACHE_TIME = now
        print(f"[RAG Cache] Cached {len(parsed)} chunks in {time.time() - t0:.2f}s")
        return _CHUNKS_CACHE
    except Exception as e:
        print(f"[RAG Cache] Error fetching chunks from Supabase: {e}")
        return _CHUNKS_CACHE or []

def rank_chunks(query_vector, chunks, top_k=5):
    """Fast similarity ranking using NumPy or math fallback."""
    if not chunks or not query_vector:
        return []

    valid = [c for c in chunks if c.get("embedding")]
    if not valid:
        return chunks[:top_k]

    if HAS_NUMPY:
        try:
            q = np.array(query_vector, dtype=np.float32)
            q_norm = np.linalg.norm(q)
            if q_norm > 0:
                q = q / q_norm

            emb_matrix = np.array([c["embedding"] for c in valid], dtype=np.float32)
            min_dim = min(emb_matrix.shape[1], len(q))
            emb_sub = emb_matrix[:, :min_dim]
            q_sub = q[:min_dim]

            norms = np.linalg.norm(emb_sub, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            emb_norm = emb_sub / norms

            sims = np.dot(emb_norm, q_sub)
            top_idx = np.argsort(sims)[::-1][:top_k]
            return [valid[i] for i in top_idx]
        except Exception as err:
            print(f"[RAG] NumPy ranking error ({err}), using math fallback.")

    # Pure Python math fallback
    scored = []
    for c in valid:
        emb = c["embedding"]
        min_len = min(len(query_vector), len(emb))
        v1 = query_vector[:min_len]
        v2 = emb[:min_len]
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(a * a for a in v1))
        n2 = math.sqrt(sum(b * b for b in v2))
        sim = dot / (n1 * n2) if (n1 > 0 and n2 > 0) else 0.0
        scored.append((sim, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for sim, c in scored[:top_k]]

def ask_knowledge_base(
    user_id: str,
    question: str,
    user_role: str = "viewer",
    filter_documents: list = None
) -> dict:
    t_start = time.time()

    # 1. Query Embedding
    try:
        t_emb = time.time()
        raw_query_vector = generate_embedding(question, task_type="retrieval_query")
        query_vector_768 = normalize_and_slice_vector(raw_query_vector, 768)
        print(f"[RAG Perf] Embedding generated in {time.time() - t_emb:.2f}s")
    except Exception as e:
        return {
            "answer": f"Embedding error: {str(e)}. කරුණාකර backend/.env එකේ ඇති GEMINI_API_KEY පරීක්ෂා කරන්න.",
            "citations": []
        }

    # 2. Fast retrieval from memory cache with User Isolation
    t_ret = time.time()
    all_chunks = get_cached_chunks()

    # User isolation: Non-admins only search their own documents
    if user_role != "admin":
        user_chunks = [c for c in all_chunks if c.get("uploaded_by") == str(user_id)]
    else:
        user_chunks = all_chunks

    # Optional document filter
    if filter_documents:
        filter_set = set(filter_documents)
        user_chunks = [c for c in user_chunks if c.get("file_name") in filter_set or c.get("document_id") in filter_set]

    if not user_chunks:
        if user_role != "admin":
            return {
                "answer": "ඔබගේ ගිණුමට අදාළ ලේඛන (PDF) කිසිවක් හමු නොවීය. කරුණාකර Documents පිටුවෙන් PDF එකක් upload කර ප්‍රශ්න අසන්න.",
                "citations": []
            }
        else:
            return {
                "answer": "Database එකේ ලේඛනවලට අදාළ chunks සොයාගත නොහැකි විය. කරුණාකර Documents tab එකෙන් PDF එකක් upload වී ඇති බව තහවුරු කරගන්න.",
                "citations": []
            }

    matched_chunks = rank_chunks(query_vector_768, user_chunks, top_k=5)
    print(f"[RAG Perf] Retrieval & ranking finished in {time.time() - t_ret:.3f}s (matched {len(matched_chunks)} chunks from {len(user_chunks)} available)")

    # 3. Build context & citations
    context_blocks = []
    citations = []
    seen_sources = set()

    for chunk in matched_chunks:
        doc_id = chunk.get("document_id", "")
        file_name = chunk.get("file_name", "Document")
        page_num = chunk.get("page_number", 1)
        content = chunk.get("content", "")

        if not content:
            continue

        context_blocks.append(
            f"[Document: {file_name}, Page: {page_num}]\n{content}"
        )
        
        source_key = f"{doc_id}_{page_num}"
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            citations.append({
                "document_id": doc_id,
                "file_name": file_name,
                "page_number": page_num,
                "snippet": content[:200] + "..." if len(content) > 200 else content
            })

    if not context_blocks:
        return {
            "answer": "ලේඛනවල අන්තර්ගතය කියවීමට නොහැකි විය.",
            "citations": []
        }

    context_text = "\n\n---\n\n".join(context_blocks)

    # 4. Prompt
    prompt = f"""You are an intelligent Corporate Knowledge Assistant.
Answer the user's question accurately using ONLY the information in the 'CONTEXT' section below.

Rules:
1. Do not invent any facts not mentioned in the CONTEXT.
2. If the user asks in English, answer in clear English. If in Sinhala, answer in Sinhala.
3. State facts clearly and concisely.
4. Mention relevant document names and page numbers if applicable.

CONTEXT:
{context_text}

QUESTION:
{question}
"""

    response_text = ""
    # Use the verified working models for your account
    verified_models = [
        "gemini-3.1-flash-lite",
        "gemma-4-26b-a4b-it",
        "gemma-4-31b-it"
    ]

    t_llm = time.time()
    if modern_client:
        for m in verified_models:
            try:
                resp = modern_client.models.generate_content(
                    model=m,
                    contents=prompt
                )
                if resp and resp.text:
                    response_text = resp.text.strip()
                    print(f"[RAG Perf] Generated with ({m}) in {time.time() - t_llm:.2f}s")
                    break
            except Exception as e:
                print(f"[RAG] Model '{m}' failed: {str(e)[:80]}")

    # Fallback to direct extractive content if all models are busy
    if not response_text and matched_chunks:
        top_snippet = matched_chunks[0].get("content", "").strip()
        lines = [line.strip() for line in top_snippet.split("\n") if line.strip()]
        preview_text = "\n".join(lines[:6])
        response_text = (
            f"*(Extracted directly from source:)*\n\n"
            f"> {preview_text}"
        )

    total_time = time.time() - t_start
    print(f"[RAG Perf] Total pipeline time: {total_time:.2f}s\n")

    return {
        "answer": response_text,
        "citations": citations
    }
