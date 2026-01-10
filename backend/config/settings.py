from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # LiveKit Configuration
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    
    # Groq Configuration
    groq_api_key: Optional[str] = None
    
    # Google Cloud Configuration
    google_application_credentials: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # Service Selection
    llm_provider: str = "openai"  # openai, ollama, groq (openai is primary, ollama is fallback)
    stt_provider: str = "openai"  # openai, google
    tts_provider: str = "openai"  # openai, google
    
    # Application Configuration
    log_level: str = "INFO"
    max_retry_attempts: int = 3
    conversation_timeout: int = 300
    audio_buffer_duration: float = 2.0  # seconds
    
    # LLM Configuration
    llm_temperature: float = 0.7
    llm_max_tokens: int = 500
    
    # TTS Configuration
    tts_voice: str = "alloy"  # openai voices: alloy, echo, fable, onyx, nova, shimmer
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

