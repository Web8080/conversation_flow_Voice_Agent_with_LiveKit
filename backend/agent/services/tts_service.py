from abc import ABC, abstractmethod
from typing import Optional
import asyncio
import httpx
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
        # Google Cloud TTS requires service account credentials, not just API key
        # GOOGLE_API_KEY works for Gemini, but Speech/TTS need GOOGLE_APPLICATION_CREDENTIALS
        import os
        import json
        import tempfile
        
        # Handle different credential formats for LiveKit Cloud deployment
        credentials_path = None
        
        # Option 1: JSON content as environment variable (for LiveKit Cloud)
        credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if credentials_json:
            try:
                # Write JSON content to temp file
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                json.dump(json.loads(credentials_json), temp_file)
                temp_file.close()
                credentials_path = temp_file.name
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
                logger.info("Using Google credentials from GOOGLE_APPLICATION_CREDENTIALS_JSON")
            except Exception as e:
                logger.error("Failed to parse GOOGLE_APPLICATION_CREDENTIALS_JSON", error=str(e))
        
        # Option 2: Base64 encoded JSON (for LiveKit Cloud)
        if not credentials_path:
            credentials_base64 = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_BASE64")
            if credentials_base64:
                try:
                    import base64
                    json_content = base64.b64decode(credentials_base64).decode('utf-8')
                    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                    temp_file.write(json_content)
                    temp_file.close()
                    credentials_path = temp_file.name
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
                    logger.info("Using Google credentials from GOOGLE_APPLICATION_CREDENTIALS_BASE64")
                except Exception as e:
                    logger.error("Failed to decode GOOGLE_APPLICATION_CREDENTIALS_BASE64", error=str(e))
        
        # Option 3: File path (for local development)
        if not credentials_path:
            if settings.google_application_credentials:
                if os.path.exists(settings.google_application_credentials):
                    credentials_path = settings.google_application_credentials
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
                    logger.info("Using Google credentials from file path")
                else:
                    logger.warning("Google credentials file not found", path=settings.google_application_credentials)
        
        # Option 4: Application Default Credentials (if already set up via gcloud)
        if not credentials_path and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            # Try to use ADC - will work if user ran 'gcloud auth application-default login'
            logger.info("Attempting to use Application Default Credentials")
        
        # Final check
        if not credentials_path and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            raise ValueError(
                "Google Cloud TTS requires service account credentials. "
                "Set one of:\n"
                "  - GOOGLE_APPLICATION_CREDENTIALS (path to JSON file)\n"
                "  - GOOGLE_APPLICATION_CREDENTIALS_JSON (JSON content as string)\n"
                "  - GOOGLE_APPLICATION_CREDENTIALS_BASE64 (base64 encoded JSON)\n"
                "Or run: gcloud auth application-default login\n"
                "Get service account: https://console.cloud.google.com/iam-admin/serviceaccounts"
            )
        
        logger.info("Initialized Google TTS service")
    
    async def synthesize(self, text: str, voice: Optional[str] = None) -> Optional[bytes]:
        try:
            from google.cloud import texttospeech
            
            # TextToSpeechClient will use GOOGLE_APPLICATION_CREDENTIALS environment variable
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


class F5TTSService(TTSService):
    """
    F5-TTS service via Replicate API.
    Free TTS option, but requires Replicate API key and may be slower.
    """
    def __init__(self):
        if not hasattr(settings, 'replicate_api_key') or not settings.replicate_api_key:
            raise ValueError("Replicate API key not configured. Get one at https://replicate.com/account/api-tokens")
        self.replicate_api_key = settings.replicate_api_key
        # F5-TTS via Replicate is complex - requires reference audio for voice cloning
        # For simple TTS without voice cloning, Google TTS is better
        # Disabling F5-TTS for now - use Google TTS as fallback instead
        raise ValueError("F5-TTS via Replicate requires reference audio. Use Google TTS as fallback instead.")
    
    async def synthesize(self, text: str, voice: Optional[str] = None) -> Optional[bytes]:
        try:
            # F5-TTS via Replicate API
            # Note: F5-TTS typically requires reference audio for voice cloning
            # For simple TTS, we'll use default settings
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Start prediction
                response = await client.post(
                    f"https://api.replicate.com/v1/models/{self.model}/predictions",
                    headers={
                        "Authorization": f"Token {self.replicate_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "input": {
                            "text": text,
                            # F5-TTS requires reference audio, but we'll use default voice
                            # For production, you'd want to provide a reference audio URL
                        }
                    }
                )
                
                if response.status_code != 201:
                    error_text = response.text
                    logger.error("F5-TTS API request failed", status=response.status_code, error=error_text)
                    return None
                
                prediction = response.json()
                prediction_id = prediction["id"]
                
                # Poll for result (Replicate is async)
                import time
                max_wait = 60  # 60 seconds max
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    status_response = await client.get(
                        f"https://api.replicate.com/v1/predictions/{prediction_id}",
                        headers={"Authorization": f"Token {self.replicate_api_key}"}
                    )
                    
                    status_data = status_response.json()
                    status = status_data.get("status")
                    
                    if status == "succeeded":
                        output_url = status_data.get("output")
                        if output_url:
                            # Download audio file
                            audio_response = await client.get(output_url)
                            if audio_response.status_code == 200:
                                audio_data = audio_response.content
                                logger.info("F5-TTS synthesis completed", text_length=len(text), audio_size=len(audio_data))
                                return audio_data
                    
                    elif status == "failed":
                        error = status_data.get("error", "Unknown error")
                        logger.error("F5-TTS prediction failed", error=error)
                        return None
                    
                    # Wait before next poll
                    await asyncio.sleep(2)
                
                logger.error("F5-TTS prediction timeout")
                return None
                
        except Exception as e:
            logger.error("F5-TTS synthesis failed", error=str(e))
            return None


class TTSFallbackService(TTSService):
    """
    TTS service with automatic fallback between providers.
    Tries primary provider first, then falls back to others on failure.
    """
    def __init__(self, primary: TTSService, fallbacks: list[TTSService]):
        self.primary = primary
        self.fallbacks = fallbacks
        logger.info("Initialized TTS service with fallback", 
                   primary=type(primary).__name__, 
                   fallbacks=[type(f).__name__ for f in fallbacks])
    
    async def synthesize(self, text: str, voice: Optional[str] = None) -> Optional[bytes]:
        # Try primary provider first
        try:
            result = await self.primary.synthesize(text, voice)
            if result:
                return result
        except Exception as e:
            logger.warning("Primary TTS provider failed, trying fallback", 
                         provider=type(self.primary).__name__, 
                         error=str(e))
        
        # Try fallback providers in order
        for fallback in self.fallbacks:
            try:
                logger.info("Trying fallback TTS provider", provider=type(fallback).__name__)
                result = await fallback.synthesize(text, voice)
                if result:
                    logger.info("Fallback TTS provider succeeded", provider=type(fallback).__name__)
                    return result
            except Exception as e:
                logger.warning("Fallback TTS provider also failed", 
                             provider=type(fallback).__name__, 
                             error=str(e))
                continue
        
        # All providers failed
        logger.error("All TTS providers failed", 
                    primary=type(self.primary).__name__,
                    fallbacks=[type(f).__name__ for f in self.fallbacks])
        return None


def create_tts_service() -> TTSService:
    """
    Creates TTS service with fallback strategy:
    Primary: Google TTS (if credentials configured)
    Fallback: OpenAI (if API key configured)
    
    Note: Ollama does NOT support TTS, only LLM.
    """
    providers = []
    
    # Google TTS is primary (requires service account credentials, not just API key)
    # Check for service account credentials (file path, JSON string, or base64)
    import os
    has_google_creds = (
        settings.google_application_credentials or
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON") or
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS_BASE64") or
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    )
    if has_google_creds:
        try:
            providers.append(("google", GoogleTTSService()))
        except Exception as e:
            logger.warning("Google TTS not available", error=str(e))
    
    # OpenAI is fallback (highest quality, production-ready)
    if settings.openai_api_key:
        try:
            providers.append(("openai", OpenAITTSService()))
        except Exception as e:
            logger.warning("OpenAI TTS not available", error=str(e))
    
    # F5-TTS via Replicate is disabled - requires reference audio which complicates simple TTS
    # If you want F5-TTS, you'd need to implement reference audio handling
    # For now, Google TTS is the best free fallback option
    # if hasattr(settings, 'replicate_api_key') and settings.replicate_api_key:
    #     try:
    #         providers.append(("f5-tts", F5TTSService()))
    #     except Exception as e:
    #         logger.warning("F5-TTS not available", error=str(e))
    
    if not providers:
        raise ValueError("No TTS provider configured. Please set up at least OpenAI, Google TTS, or F5-TTS.")
    
    # If only one provider, return it directly
    if len(providers) == 1:
        logger.info("Using TTS provider", provider=providers[0][0])
        return providers[0][1]
    
    # Multiple providers: use fallback wrapper
    primary = providers[0][1]
    fallbacks = [p[1] for p in providers[1:]]
    return TTSFallbackService(primary, fallbacks)

