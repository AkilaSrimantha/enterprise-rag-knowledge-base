from pydantic_settings import BaseSettings, SettingsConfigDict
from supabase import create_client, Client
import google.generativeai as genai

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    GEMINI_API_KEY: str
    SECRET_KEY: str = "replace-with-a-very-secure-random-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ADMIN_EMAIL: str = "admin@ragkb.com"
    EDITOR_EMAIL: str = "editor@ragkb.com"
    ADMIN_INITIAL_PASSWORD: str = "AdminPassword123!"
    EDITOR_INITIAL_PASSWORD: str = "EditorPassword123!"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()

# Supabase Admin Client (RLS bypass කර backend වැඩ කිරීමට)
supabase: Client = create_client(
    settings.SUPABASE_URL, 
    settings.SUPABASE_SERVICE_ROLE_KEY
)

# Gemini AI Configuration
genai.configure(api_key=settings.GEMINI_API_KEY)