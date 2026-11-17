from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
try:
    import email_validator
    from pydantic import EmailStr
except ImportError:
    EmailStr = str
from datetime import datetime


class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


# Auth Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None


# Document Schemas
class DocumentItem(BaseModel):
    id: str
    filename: str
    file_type: str
    page_count: int
    chunk_count: int
    upload_date: datetime
    uploaded_by: Optional[str] = None
    size_bytes: Optional[int] = None


class DocumentUploadResponse(BaseModel):
    message: str
    processed_documents: List[DocumentItem]
    failed_documents: List[Dict[str, str]] = []


# RAG & Citation Schemas
class Citation(BaseModel):
    document_name: str
    page_number: int
    snippet: str
    score: Optional[float] = None


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    query: str
    history: Optional[List[ChatMessage]] = []
    filter_documents: Optional[List[str]] = None
    temperature: Optional[float] = 0.2


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    model_used: str
