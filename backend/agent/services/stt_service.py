from abc import ABC, abstractmethod
from typing import Optional
import asyncio
from openai import OpenAI
from utils.logger import logger
from config.settings import settings


class STTService(ABC):
    @abstractmethod
    async def transcribe(self, audio_data: bytes, language: str = "en") -> Optional[str]:
        pass


class OpenAISTTService(STTService):
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.client = OpenAI(api_key=settings.openai_api_key)
        logger.info("Initialized OpenAI STT service")
    
    async def transcribe(self, audio_data: bytes, language: str = "en") -> Optional[str]:
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=("audio.wav", audio_data, "audio/wav"),
                    language=language,
                    response_format="text"
                )
            )
            text = result if isinstance(result, str) else result.text
            logger.info("STT transcription completed", text_length=len(text))
            return text.strip()
        except Exception as e:
            logger.error("STT transcription failed", error=str(e))
            return None


class GoogleSTTService(STTService):
    def __init__(self):
        if not settings.google_api_key and not settings.google_application_credentials:
            raise ValueError("Google Cloud credentials not configured")
        logger.info("Initialized Google STT service")
    
    async def transcribe(self, audio_data: bytes, language: str = "en") -> Optional[str]:
        try:
            from google.cloud import speech
            client = speech.SpeechClient()
            
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language,
            )
            
            audio = speech.RecognitionAudio(content=audio_data)
            response = client.recognize(config=config, audio=audio)
            
            if response.results:
                text = response.results[0].alternatives[0].transcript
                logger.info("Google STT transcription completed", text_length=len(text))
                return text.strip()
            return None
        except Exception as e:
            logger.error("Google STT transcription failed", error=str(e))
            return None


def create_stt_service() -> STTService:
    if settings.stt_provider == "openai":
        return OpenAISTTService()
    elif settings.stt_provider == "google":
        return GoogleSTTService()
    else:
        logger.warning("Unknown STT provider, defaulting to OpenAI", provider=settings.stt_provider)
        return OpenAISTTService()

