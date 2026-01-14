from abc import ABC, abstractmethod
from typing import Optional
import asyncio
from openai import OpenAI
from utils.logger import logger
from config.settings import settings


class STTService(ABC):
    @abstractmethod
    async def transcribe(self, audio_data: bytes, sample_rate: int, num_channels: int, language: str = "en") -> Optional[str]:
        pass


class OpenAISTTService(STTService):
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.client = OpenAI(api_key=settings.openai_api_key)
        logger.info("Initialized OpenAI STT service")
    
    async def transcribe(self, audio_data: bytes, sample_rate: int, num_channels: int, language: str = "en") -> Optional[str]:
        try:
            import io
            import wave
            
            logger.info("DEBUG: OpenAI STT transcribe called",
                       audio_size=len(audio_data),
                       language=language,
                       sample_rate=sample_rate,
                       num_channels=num_channels,
                       hypothesis="STT_OPENAI")
            
            # Convert raw audio to WAV format for OpenAI
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(num_channels)
                wav_file.setsampwidth(2)  # 16-bit audio
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data)
            wav_buffer.seek(0)
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=("audio.wav", wav_buffer.read(), "audio/wav"),
                    language=language,
                    response_format="text"
                )
            )
            text = result if isinstance(result, str) else result.text
            logger.info("STT transcription completed", 
                       text_length=len(text),
                       text_preview=text[:50] if text else None,
                       hypothesis="STT_OPENAI")
            return text.strip() if text else None
        except Exception as e:
            logger.error("STT transcription failed",
                        error=str(e),
                        error_type=type(e).__name__,
                        hypothesis="STT_OPENAI")
            return None


class GoogleSTTService(STTService):
    def __init__(self):
        # Google Cloud Speech requires service account credentials, not just API key
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
                "Google Cloud Speech requires service account credentials. "
                "Set one of:\n"
                "  - GOOGLE_APPLICATION_CREDENTIALS (path to JSON file)\n"
                "  - GOOGLE_APPLICATION_CREDENTIALS_JSON (JSON content as string)\n"
                "  - GOOGLE_APPLICATION_CREDENTIALS_BASE64 (base64 encoded JSON)\n"
                "Or run: gcloud auth application-default login\n"
                "Get service account: https://console.cloud.google.com/iam-admin/serviceaccounts"
            )
        
        self.openai_fallback = None
        # Initialize OpenAI fallback if available
        if settings.openai_api_key:
            try:
                self.openai_fallback = OpenAISTTService()
                logger.info("Initialized Google STT service with OpenAI fallback")
            except Exception:
                logger.info("Initialized Google STT service (no fallback)")
        else:
            logger.info("Initialized Google STT service (no fallback)")
    
    async def transcribe(self, audio_data: bytes, sample_rate: int, num_channels: int, language: str = "en") -> Optional[str]:
        try:
            from google.cloud import speech
            import io
            import wave
            
            logger.info("DEBUG: Google STT transcribe called",
                       audio_size=len(audio_data),
                       language=language,
                       provided_sample_rate=sample_rate,
                       num_channels=num_channels,
                       hypothesis="STT_GOOGLE")
            
            # SpeechClient will use GOOGLE_APPLICATION_CREDENTIALS environment variable
            client = speech.SpeechClient()
            
            # Prioritize the provided sample rate, then try common rates
            sample_rates_to_try = [sample_rate] if sample_rate else []
            sample_rates_to_try.extend([16000, 24000, 48000])
            sample_rates_to_try = list(dict.fromkeys(sample_rates_to_try))  # Remove duplicates
            
            # Convert raw audio to WAV format for Google STT
            logger.info("DEBUG: Converting audio to WAV format",
                       raw_audio_size=len(audio_data),
                       sample_rate=sample_rate,
                       num_channels=num_channels,
                       hypothesis="STT_WAV_CONVERT")
            
            wav_buffer = io.BytesIO()
            try:
                with wave.open(wav_buffer, 'wb') as wav_file:
                    wav_file.setnchannels(num_channels)
                    wav_file.setsampwidth(2)  # 16-bit audio
                    wav_file.setframerate(sample_rate)  # Use the provided sample rate for WAV header
                    wav_file.writeframes(audio_data)
                wav_buffer.seek(0)
                wav_data = wav_buffer.read()
                
                logger.info("DEBUG: WAV conversion successful",
                           wav_size=len(wav_data),
                           hypothesis="STT_WAV_SUCCESS")
            except Exception as wav_error:
                logger.error("DEBUG: WAV conversion failed",
                           error=str(wav_error),
                           error_type=type(wav_error).__name__,
                           hypothesis="STT_WAV_ERROR")
                raise
            
            audio = speech.RecognitionAudio(content=wav_data)
            
            for sr in sample_rates_to_try:
                try:
                    logger.info("DEBUG: Trying Google STT with sample rate",
                               audio_size=len(audio_data),
                               hypothesis="STT_GOOGLE",
                               sample_rate=sr)
                    
                    config = speech.RecognitionConfig(
                        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                        sample_rate_hertz=sr,
                        language_code=language,
                        audio_channel_count=num_channels,
                        enable_automatic_punctuation=True,
                    )
                    
                    response = client.recognize(config=config, audio=audio)
                    
                    logger.info("DEBUG: Google STT response received",
                               results_count=len(response.results) if response.results else 0,
                               sample_rate=sr,
                               hypothesis="STT_GOOGLE")
                    
                    if response.results:
                        text = response.results[0].alternatives[0].transcript
                        confidence = response.results[0].alternatives[0].confidence
                        logger.info("DEBUG: Google STT transcription successful", 
                                   text=text,
                                   text_repr=repr(text),
                                   text_length=len(text),
                                   text_stripped_length=len(text.strip()),
                                   sample_rate=sr,
                                   confidence=confidence,
                                   hypothesis="STT_GOOGLE_SUCCESS")
                        return text.strip()
                    else:
                        logger.warning("DEBUG: Google STT returned no results",
                                     sample_rate=sr,
                                     audio_size=len(audio_data),
                                     hypothesis="STT_GOOGLE_NO_RESULTS")
                except Exception as rate_error:
                    logger.warning("DEBUG: Google STT failed for sample rate",
                                 sample_rate=sr,
                                 error=str(rate_error),
                                 error_type=type(rate_error).__name__,
                                 hypothesis="STT_GOOGLE")
                    continue
            
            logger.warning("Google STT failed for all sample rates, trying OpenAI fallback")
            if self.openai_fallback:
                try:
                    logger.info("DEBUG: Trying OpenAI STT fallback", hypothesis="STT_FALLBACK", sample_rate=sample_rate)
                    result = await self.openai_fallback.transcribe(audio_data, sample_rate, num_channels, language)
                    logger.info("DEBUG: OpenAI STT fallback result",
                               has_result=result is not None,
                               text_length=len(result) if result else 0,
                               hypothesis="STT_FALLBACK")
                    return result
                except Exception as fallback_error:
                    logger.error("OpenAI STT fallback also failed", 
                               error=str(fallback_error),
                               error_type=type(fallback_error).__name__,
                               hypothesis="STT_OPENAI_FALLBACK_ERROR")
            return None
        except Exception as e:
            logger.error("Google STT transcription failed with exception",
                        error=str(e),
                        error_type=type(e).__name__,
                        error_traceback=str(e.__traceback__) if hasattr(e, '__traceback__') else None,
                        hypothesis="STT_ERROR")
            if self.openai_fallback:
                try:
                    logger.info("DEBUG: Trying OpenAI STT fallback after exception", 
                               sample_rate=sample_rate,
                               hypothesis="STT_FALLBACK")
                    return await self.openai_fallback.transcribe(audio_data, sample_rate, num_channels, language)
                except Exception as fallback_error:
                    logger.error("OpenAI STT fallback also failed", 
                               error=str(fallback_error),
                               error_type=type(fallback_error).__name__)
            return None


def create_stt_service() -> STTService:
    """
    Creates STT service with fallback strategy:
    Primary: Google STT (if credentials configured)
    Fallback: OpenAI (if API key configured)
    """
    providers = []
    
    # Google STT is primary (requires service account credentials, not just API key)
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
            providers.append(("google", GoogleSTTService()))
        except Exception as e:
            logger.warning("Google STT not available", error=str(e))
    
    # OpenAI STT is fallback (high quality, reliable)
    if settings.openai_api_key:
        try:
            providers.append(("openai", OpenAISTTService()))
        except Exception as e:
            logger.warning("OpenAI STT not available", error=str(e))
    
    if not providers:
        raise ValueError("No STT provider configured. Please set up at least Google or OpenAI STT.")
    
    # If only one provider, return it directly
    if len(providers) == 1:
        logger.info("Using STT provider", provider=providers[0][0])
        return providers[0][1]
    
    # Multiple providers: return primary (Google) with manual fallback in service
    # Google service already has OpenAI fallback built-in
    logger.info("Using STT provider", provider=providers[0][0], fallback=providers[1][0] if len(providers) > 1 else None)
    return providers[0][1]  # Return Google as primary, OpenAI fallback happens in GoogleSTTService

