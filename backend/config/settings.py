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
    
    # Replicate Configuration (for F5-TTS)
    replicate_api_key: Optional[str] = None
    
    # Service Selection
    llm_provider: str = "google"  # google, openai, ollama, groq (google is primary)
    stt_provider: str = "google"  # google, openai
    tts_provider: str = "google"  # google, openai
    
    # Application Configuration
    log_level: str = "INFO"
    max_retry_attempts: int = 3
    conversation_timeout: int = 300
    audio_buffer_duration: float = 2.0  # seconds (legacy, used by stage1/stage2)
    agent_stage: str = "stage1"  # stage1, stage2, or stage3 (stage3 recommended)
    
    # LLM Configuration
    llm_temperature: float = 0.7
    llm_max_tokens: int = 500
    
    # TTS Configuration
    tts_voice: str = "alloy"  # openai voices: alloy, echo, fable, onyx, nova, shimmer
    
    # VAD Configuration (Stage 3)
    vad_enabled: bool = True
    vad_threshold: float = 0.5  # Speech probability threshold (0.0-1.0)
    vad_silence_threshold_ms: int = 600  # Silence duration to detect end of speech
    vad_min_speech_duration_ms: int = 250  # Minimum speech to process
    
    # Flow Configuration (Stage 3)
    flow_path: Optional[str] = None  # Path to flow JSON file
    allow_interruptions: bool = True  # Allow user to interrupt agent
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

