export type UserRole = 'admin' | 'editor' | 'viewer';

export interface User {
  id: string;
  email: string;
  full_name?: string;
  role: UserRole;
  is_active: boolean;
}

export interface DocumentItem {
  id: string;
  filename: string;
  file_type: string;
  page_count: number;
  chunk_count: number;
  upload_date: string;
  uploaded_by?: string;
  size_bytes?: number;
}

export interface Citation {
  document_name: string;
  page_number: number;
  snippet: string;
  score?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  model_used: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  role: UserRole;
  user_id: string;
}
