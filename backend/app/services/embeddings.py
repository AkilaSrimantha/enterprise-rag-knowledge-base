from langchain_text_splitters import RecursiveCharacterTextSplitter
import google.generativeai as genai
import math
from app.core.config import supabase

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ".", " ", ""]
)

EMBEDDING_MODELS = [
    "models/gemini-embedding-001",
    "models/gemini-embedding-2",
    "models/gemini-embedding-2-preview"
]

def normalize_and_slice_vector(vec: list[float], target_dim: int = 768) -> list[float]:
    """
    Matryoshka representation learning: Truncates and normalizes vector
    to match the database column dimension (e.g. 768).
    """
    if not vec:
        return []
    if len(vec) == target_dim:
        return vec
    if len(vec) > target_dim:
        sliced = vec[:target_dim]
        norm = math.sqrt(sum(x * x for x in sliced))
        if norm > 0:
            return [x / norm for x in sliced]
        return sliced
    return vec

def generate_embedding(text: str, task_type: str = "retrieval_query") -> list[float]:
    """
    Generate vector embeddings using Google's active gemini-embedding models.
    """
    last_err = None
    for model_name in EMBEDDING_MODELS:
        try:
            res = genai.embed_content(
                model=model_name,
                content=text,
                task_type=task_type
            )
            return res["embedding"]
        except Exception as e:
            last_err = e
            continue

    raise last_err if last_err else RuntimeError("Could not generate embedding.")

def process_and_store_embeddings(
    document_id: str, 
    org_id: str, 
    pages_data: list[dict]
):
    chunks_to_insert = []

    for page in pages_data:
        page_num = page["page_number"]
        chunks = text_splitter.split_text(page["text"])

        for idx, chunk_text in enumerate(chunks):
            raw_vector = generate_embedding(chunk_text, task_type="retrieval_document")
            # Default to 768-dim (standard for Supabase RAG templates)
            vector_768 = normalize_and_slice_vector(raw_vector, 768)

            chunks_to_insert.append({
                "document_id": document_id,
                "content": chunk_text,
                "page_number": page_num,
                "chunk_index": idx,
                "embedding": vector_768
            })

    if not chunks_to_insert:
        print("[Warning] No chunks extracted from document.")
        return

    # Attempt 1: Insert as 768-dimension vectors
    try:
        supabase.table("document_chunks").insert(chunks_to_insert).execute()
        print(f"[Success] Inserted {len(chunks_to_insert)} chunks as 768-dim vectors into document_chunks.")
        return
    except Exception as e768:
        print(f"[Retry] 768-dim insert failed: {e768}")

    # Attempt 2: If table expects original 3072-dim vectors
    try:
        # Re-generate or use original vectors
        chunks_orig = []
        for c in chunks_to_insert:
            c_copy = dict(c)
            # Re-generate full dimension
            c_copy["embedding"] = generate_embedding(c["content"], task_type="retrieval_document")
            chunks_orig.append(c_copy)
        supabase.table("document_chunks").insert(chunks_orig).execute()
        print(f"[Success] Inserted {len(chunks_orig)} chunks as 3072-dim vectors into document_chunks.")
        return
    except Exception as e_orig:
        print(f"[Error] Failed inserting chunks with both 768 and 3072 dimensions: {e_orig}")
        raise e_orig
