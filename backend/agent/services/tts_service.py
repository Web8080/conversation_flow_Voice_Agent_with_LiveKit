from abc import ABC, abstractmethod
from typing import Optional
import asyncio
from openai import OpenAI
from utils.logger import logger
from config.settings import settings


class TTSService(ABC):
    @abstractmethod
    async def synthesize(self, text: str, voice: Optional[str] = None) -> Optional[bytes]:
        pass


class OpenAITTSService(TTSService):
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.default_voice = settings.tts_voice
        logger.info("Initialized OpenAI TTS service", voice=self.default_voice)
    
    async def synthesize(self, text: str, voice: Optional[str] = None) -> Optional[bytes]:
        try:
            voice_name = voice or self.default_voice
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.audio.speech.create(
                    model="tts-1",
                    voice=voice_name,
                    input=text,
                    response_format="pcm"  # PCM for LiveKit compatibility
                )
            )
            audio_data = response.content
            logger.info("OpenAI TTS synthesis completed", text_length=len(text), audio_size=len(audio_data))
            return audio_data
        except Exception as e:
            logger.error("OpenAI TTS synthesis failed", error=str(e))
            return None


class GoogleTTSService(TTSService):
    def __init__(self):
        if not settings.google_api_key and not settings.google_application_credentials:
            raise ValueError("Google Cloud credentials not configured")
        logger.info("Initialized Google TTS service")
    
    async def synthesize(self, text: str, voice: Optional[str] = None) -> Optional[bytes]:
        try:
            from google.cloud import texttospeech
            
            client = texttospeech.TextToSpeechClient()
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice_config = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=voice or "en-US-Neural2-D",
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
            )
            
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice_config,
                audio_config=audio_config
            )
            
            logger.info("Google TTS synthesis completed", text_length=len(text))
            return response.audio_content
        except Exception as e:
            logger.error("Google TTS synthesis failed", error=str(e))
            return None


def create_tts_service() -> TTSService:
    if settings.tts_provider == "openai":
        return OpenAITTSService()
    elif settings.tts_provider == "google":
        return GoogleTTSService()
    else:
        logger.warning("Unknown TTS provider, defaulting to OpenAI", provider=settings.tts_provider)
        return OpenAITTSService()

