import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print(f"Connecting to Supabase: {url}")
sb = create_client(url, key)

print("\n--- 1. Checking 'documents' Table ---")
try:
    docs = sb.table("documents").select("*").execute()
    print(f"Found {len(docs.data)} row(s) in documents:")
    for d in docs.data:
        print(f"  * ID: {d.get('id')} | File: {d.get('file_name')} | Status: {d.get('status')} | Total Pages: {d.get('total_pages')}")
except Exception as e:
    print(f"Error querying 'documents': {e}")

print("\n--- 2. Checking 'document_chunks' Table ---")
try:
    chunks = sb.table("document_chunks").select("id, document_id, page_number, chunk_index, content").execute()
    print(f"Found {len(chunks.data)} chunk(s) in document_chunks:")
    for c in chunks.data[:5]:
        print(f"  * Chunk ID: {c.get('id')} | Doc ID: {c.get('document_id')} | Page: {c.get('page_number')} | Content preview: {c.get('content', '')[:60]}...")
except Exception as e:
    print(f"Error querying 'document_chunks': {e}")

if not chunks.data:
    print("\n--- 3. Testing Embedding Insert Dimensions on 'document_chunks' ---")
    # Test if table expects 768 or 3072 or 1536
    dummy_doc_id = docs.data[0]["id"] if (docs and docs.data) else None
    if dummy_doc_id:
        for dim in [768, 3072, 1536]:
            try:
                test_vec = [0.01] * dim
                res = sb.table("document_chunks").insert({
                    "document_id": dummy_doc_id,
                    "content": "Dimension test",
                    "page_number": 1,
                    "chunk_index": 9999,
                    "embedding": test_vec
                }).execute()
                print(f"-> SUCCESS inserting vector of dimension {dim}!")
                # Delete test chunk
                sb.table("document_chunks").delete().eq("chunk_index", 9999).execute()
                break
            except Exception as dim_err:
                print(f"-> Dimension {dim} failed: {dim_err}")
