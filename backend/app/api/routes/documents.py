from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
import uuid
import traceback
from app.core.config import supabase
from app.services.parser import extract_text_with_pages
from app.services.embeddings import process_and_store_embeddings
from app.schemas.models import DocumentItem, DocumentUploadResponse, UserResponse, UserRole
from app.services.rag_engine import invalidate_chunks_cache
from app.api.dependencies import get_current_user

router = APIRouter()

@router.get("", response_model=List[DocumentItem])
@router.get("/", response_model=List[DocumentItem])
async def list_documents(current_user: UserResponse = Depends(get_current_user)):
    """
    Retrieve indexed documents.
    - Admins see all documents across the system.
    - Non-admins only see documents they personally uploaded.
    """
    try:
        query = supabase.table("documents").select("*").order("created_at", desc=True)
        if current_user.role != UserRole.ADMIN:
            query = query.eq("uploaded_by", current_user.id)

        response = query.execute()
        items = []
        for d in (response.data or []):
            created_at_val = d.get("created_at")
            if isinstance(created_at_val, str):
                try:
                    dt = datetime.fromisoformat(created_at_val.replace("Z", "+00:00"))
                except Exception:
                    dt = datetime.now()
            else:
                dt = datetime.now()

            uploader_id = d.get("uploaded_by")
            if uploader_id == current_user.id:
                uploader_name = "Me"
            elif current_user.role == UserRole.ADMIN:
                uploader_name = "Admin / User"
            else:
                uploader_name = "User"

            items.append(DocumentItem(
                id=str(d.get("id")),
                filename=d.get("file_name") or d.get("filename") or "Document",
                file_type=d.get("file_type") or "pdf",
                page_count=d.get("total_pages") or 1,
                chunk_count=d.get("chunk_count") or (d.get("total_pages", 1) * 2),
                upload_date=dt,
                uploaded_by=uploader_name,
                size_bytes=d.get("size_bytes") or 0
            ))
        return items
    except Exception as e:
        print(f"Error listing documents: {e}")
        return []

@router.post("/upload")
async def upload_documents(
    files: Optional[List[UploadFile]] = File(None),
    file: Optional[UploadFile] = File(None),
    org_id: Optional[str] = Form(None),
    role_ids: Optional[str] = Form(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload and index documents linked to current user."""
    upload_list = []
    if files:
        upload_list.extend(files)
    if file:
        upload_list.append(file)

    if not upload_list:
        raise HTTPException(status_code=400, detail="No files provided for upload.")

    processed = []
    failed = []

    for f in upload_list:
        filename = f.filename or "uploaded_file"
        file_ext = filename.split(".")[-1].lower()

        if file_ext not in ["pdf", "docx"]:
            failed.append({"filename": filename, "error": "Only PDF and DOCX files are supported."})
            continue

        try:
            file_bytes = await f.read()
            if not file_bytes:
                failed.append({"filename": filename, "error": "Empty file received."})
                continue

            unique_id = str(uuid.uuid4())
            storage_path = f"{unique_id}_{filename}"

            # 1. Supabase Storage upload
            try:
                supabase.storage.from_("company-documents").upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={"content-type": f.content_type or "application/octet-stream"}
                )
                file_url = supabase.storage.from_("company-documents").get_public_url(storage_path)
            except Exception as st_err:
                print(f"[Warning] Supabase storage upload failed: {st_err}")
                file_url = ""

            # 2. Extract pages
            pages_data = extract_text_with_pages(file_bytes, file_ext)
            if not pages_data:
                failed.append({"filename": filename, "error": "Could not extract text from document (it may be empty or an image-only scan)."})
                continue

            # 3. Insert record in documents table with current user's UUID
            doc_record = {
                "file_name": filename,
                "file_type": file_ext,
                "file_url": file_url,
                "total_pages": len(pages_data),
                "status": "processing",
                "uploaded_by": current_user.id
            }
            if org_id:
                doc_record["org_id"] = org_id

            try:
                doc_res = supabase.table("documents").insert(doc_record).execute()
            except Exception as ins_err:
                print(f"[Retry] Insert failed with {ins_err}, trying minimal payload...")
                doc_record_clean = {
                    "file_name": filename,
                    "file_type": file_ext,
                    "total_pages": len(pages_data),
                    "status": "processing",
                    "uploaded_by": current_user.id
                }
                doc_res = supabase.table("documents").insert(doc_record_clean).execute()

            document_id = str(doc_res.data[0]["id"])

            # 4. Role Permissions (RBAC)
            if role_ids:
                role_list = [r.strip() for r in role_ids.split(",") if r.strip()]
                permissions_data = [{"document_id": document_id, "role_id": r_id} for r_id in role_list]
                if permissions_data:
                    try:
                        supabase.table("document_permissions").insert(permissions_data).execute()
                    except Exception as p_err:
                        print(f"[Warning] document_permissions insert failed: {p_err}")

            # 5. Embeddings
            process_and_store_embeddings(document_id, org_id or str(uuid.uuid4()), pages_data)

            # 6. Mark as completed
            try:
                supabase.table("documents").update({"status": "completed"}).eq("id", document_id).execute()
            except Exception:
                pass

            doc_item = DocumentItem(
                id=document_id,
                filename=filename,
                file_type=file_ext,
                page_count=len(pages_data),
                chunk_count=len(pages_data) * 2,
                upload_date=datetime.now(),
                uploaded_by="Me",
                size_bytes=len(file_bytes)
            )
            processed.append(doc_item)
            print(f"[Success] Document '{filename}' indexed successfully for user '{current_user.email}'.")

        except Exception as exc:
            print(f"[Error] Failed to process document '{filename}':")
            traceback.print_exc()
            failed.append({"filename": filename, "error": str(exc)})

    if not processed and failed:
        err_msg = "; ".join([f"{f['filename']}: {f['error']}" for f in failed])
        raise HTTPException(status_code=400, detail=f"Upload failed: {err_msg}")

    if processed:
        invalidate_chunks_cache()

    return {
        "message": f"Successfully processed {len(processed)} document(s).",
        "processed_documents": processed,
        "failed_documents": failed
    }

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Remove a document and its embeddings from the vector store."""
    try:
        # Check ownership unless Admin
        if current_user.role != UserRole.ADMIN:
            doc_res = supabase.table("documents").select("uploaded_by").eq("id", doc_id).execute()
            if not doc_res.data or doc_res.data[0].get("uploaded_by") != current_user.id:
                raise HTTPException(status_code=403, detail="You do not have permission to delete this document.")

        supabase.table("document_chunks").delete().eq("document_id", doc_id).execute()
        supabase.table("document_permissions").delete().eq("document_id", doc_id).execute()
        supabase.table("documents").delete().eq("id", doc_id).execute()
        invalidate_chunks_cache()
        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
