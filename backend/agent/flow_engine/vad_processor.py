"""
Voice Activity Detection (VAD) Processor

Solves the "bot responds too fast" problem by:
1. Detecting speech start/end using Silero VAD
2. Only processing audio after user finishes speaking
3. Configurable silence thresholds for different use cases

This replaces the fixed 1.5-second buffer approach with intelligent
end-of-speech detection.
"""

import asyncio
import io
import wave
from typing import Optional, Callable, List, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

from utils.logger import logger


class SpeechState(Enum):
    """Current state of speech detection"""
    SILENCE = "silence"           # No speech detected
    SPEAKING = "speaking"         # User is actively speaking
    PAUSE = "pause"               # Brief pause, might continue
    SPEECH_COMPLETE = "complete"  # Speech finished, ready to process


@dataclass
class VADConfig:
    """Configuration for Voice Activity Detection"""
    # Silero VAD threshold (0.0-1.0, higher = more strict)
    threshold: float = 0.5
    
    # Minimum speech duration to consider valid (ms)
    min_speech_duration_ms: int = 250
    
    # Silence duration to detect end of speech (ms)
    silence_threshold_ms: int = 500
    
    # Maximum pause within speech before considering it separate utterances (ms)
    max_pause_duration_ms: int = 800
    
    # Padding around speech (ms) - adds buffer before/after detected speech
    speech_pad_ms: int = 100
    
    # Sample rate (must match audio stream)
    sample_rate: int = 24000
    
    # Frame duration for VAD (Silero works best with 30ms frames)
    frame_duration_ms: int = 30
    
    # Enable energy-based pre-filtering (faster, catches obvious silence)
    energy_filter_enabled: bool = True
    energy_threshold: float = 0.01  # Normalized energy threshold


@dataclass
class AudioBuffer:
    """Buffer for accumulating audio frames"""
    frames: List[bytes] = field(default_factory=list)
    total_duration_ms: float = 0.0
    speech_start_ms: Optional[float] = None
    speech_end_ms: Optional[float] = None
    
    def clear(self):
        self.frames.clear()
        self.total_duration_ms = 0.0
        self.speech_start_ms = None
        self.speech_end_ms = None
    
    def add_frame(self, frame_data: bytes, duration_ms: float):
        self.frames.append(frame_data)
        self.total_duration_ms += duration_ms
    
    def get_audio_bytes(self) -> bytes:
        """Get combined audio as bytes"""
        return b''.join(self.frames)
    
    def get_speech_segment(self, sample_rate: int) -> Optional[bytes]:
        """Get only the speech segment (with padding)"""
        if self.speech_start_ms is None:
            return None
        
        all_audio = self.get_audio_bytes()
        if not all_audio:
            return None
        
        # Calculate byte positions (16-bit audio = 2 bytes per sample)
        bytes_per_ms = (sample_rate * 2) / 1000
        
        start_byte = max(0, int(self.speech_start_ms * bytes_per_ms))
        end_byte = int((self.speech_end_ms or self.total_duration_ms) * bytes_per_ms)
        
        return all_audio[start_byte:end_byte]


class VADProcessor:
    """
    Voice Activity Detection processor using Silero VAD.
    
    Usage:
        vad = VADProcessor(config)
        await vad.initialize()
        
        # Process audio frames
        result = await vad.process_frame(audio_frame)
        if result.is_speech_complete:
            audio_data = result.audio_data
            # Process the complete utterance
    """
    
    def __init__(self, config: Optional[VADConfig] = None):
        self.config = config or VADConfig()
        self._vad_model = None
        self._initialized = False
        
        # State tracking
        self._state = SpeechState.SILENCE
        self._buffer = AudioBuffer()
        self._silence_frames = 0
        self._speech_frames = 0
        
        # Callbacks
        self._on_speech_start: Optional[Callable] = None
        self._on_speech_end: Optional[Callable] = None
        
        # Calculate frame parameters
        self._samples_per_frame = int(
            self.config.sample_rate * self.config.frame_duration_ms / 1000
        )
        self._silence_frame_threshold = int(
            self.config.silence_threshold_ms / self.config.frame_duration_ms
        )
        self._min_speech_frames = int(
            self.config.min_speech_duration_ms / self.config.frame_duration_ms
        )
        
        logger.info("VADProcessor created", 
                   threshold=self.config.threshold,
                   silence_ms=self.config.silence_threshold_ms,
                   min_speech_ms=self.config.min_speech_duration_ms,
                   sample_rate=self.config.sample_rate)
    
    async def initialize(self):
        """Initialize VAD model (lazy loading)"""
        if self._initialized:
            return
        
        try:
            # Try to use Silero VAD via torch or ONNX
            self._vad_model = await self._load_vad_model()
            self._initialized = True
            logger.info("VAD model initialized successfully")
        except Exception as e:
            logger.warning("Failed to load Silero VAD, falling back to energy-based VAD",
                         error=str(e))
            self._vad_model = None
            self._initialized = True
    
    async def _load_vad_model(self):
        """Load Silero VAD model"""
        try:
            # Try LiveKit's Silero plugin first
            from livekit.plugins import silero
            vad = silero.VAD.load()
            logger.info("Loaded Silero VAD via LiveKit plugin")
            return vad
        except ImportError:
            pass
        
        try:
            # Try direct torch loading
            import torch
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False
            )
            logger.info("Loaded Silero VAD via torch hub")
            return {"model": model, "utils": utils}
        except ImportError:
            pass
        
        # Return None to use energy-based fallback
        logger.warning("No VAD model available, using energy-based detection")
        return None
    
    def reset(self):
        """Reset VAD state for new conversation turn"""
        self._state = SpeechState.SILENCE
        self._buffer.clear()
        self._silence_frames = 0
        self._speech_frames = 0
        logger.debug("VAD state reset")
    
    def set_callbacks(
        self,
        on_speech_start: Optional[Callable] = None,
        on_speech_end: Optional[Callable] = None
    ):
        """Set callbacks for speech events"""
        self._on_speech_start = on_speech_start
        self._on_speech_end = on_speech_end
    
    async def process_frame(self, audio_frame: Any) -> 'VADResult':
        """
        Process a single audio frame.
        
        Returns VADResult with:
        - is_speech_complete: True when user finished speaking
        - audio_data: Complete audio bytes (only when is_speech_complete)
        - state: Current speech state
        """
        if not self._initialized:
            await self.initialize()
        
        # Extract audio data from frame
        if hasattr(audio_frame, 'data'):
            frame_data = audio_frame.data.tobytes() if hasattr(audio_frame.data, 'tobytes') else audio_frame.data
        else:
            frame_data = audio_frame
        
        # Calculate frame duration
        frame_samples = len(frame_data) // 2  # 16-bit audio
        frame_duration_ms = (frame_samples / self.config.sample_rate) * 1000
        
        # Detect speech in this frame
        is_speech = await self._detect_speech(frame_data)
        
        # Update state machine
        result = await self._update_state(is_speech, frame_data, frame_duration_ms)
        
        return result
    
    async def _detect_speech(self, frame_data: bytes) -> bool:
        """Detect if frame contains speech"""
        # Quick energy filter first
        if self.config.energy_filter_enabled:
            if not self._energy_check(frame_data):
                return False
        
        # Use VAD model if available
        if self._vad_model is not None:
            return await self._silero_detect(frame_data)
        
        # Fallback to energy-based detection
        return self._energy_check(frame_data, threshold=self.config.energy_threshold * 2)
    
    def _energy_check(self, frame_data: bytes, threshold: Optional[float] = None) -> bool:
        """Simple energy-based speech detection"""
        threshold = threshold or self.config.energy_threshold
        
        try:
            samples = np.frombuffer(frame_data, dtype=np.int16)
            energy = np.sqrt(np.mean(samples.astype(float) ** 2))
            normalized_energy = energy / 32768.0  # Normalize for int16
            return normalized_energy > threshold
        except Exception as e:
            logger.warning("Energy check failed", error=str(e))
            return True  # Assume speech on error
    
    async def _silero_detect(self, frame_data: bytes) -> bool:
        """Use Silero VAD for speech detection"""
        try:
            # Check if it's LiveKit's Silero
            if hasattr(self._vad_model, 'is_speech'):
                # LiveKit plugin interface
                samples = np.frombuffer(frame_data, dtype=np.int16).astype(np.float32) / 32768.0
                return self._vad_model.is_speech(samples, self.config.sample_rate)
            
            # Torch model interface
            if isinstance(self._vad_model, dict) and "model" in self._vad_model:
                import torch
                model = self._vad_model["model"]
                samples = np.frombuffer(frame_data, dtype=np.int16).astype(np.float32) / 32768.0
                tensor = torch.from_numpy(samples)
                speech_prob = model(tensor, self.config.sample_rate).item()
                return speech_prob > self.config.threshold
            
            return self._energy_check(frame_data)
        except Exception as e:
            logger.warning("Silero detection failed, using energy fallback", error=str(e))
            return self._energy_check(frame_data)
    
    async def _update_state(
        self, 
        is_speech: bool, 
        frame_data: bytes, 
        frame_duration_ms: float
    ) -> 'VADResult':
        """Update state machine based on speech detection"""
        
        # Add frame to buffer
        self._buffer.add_frame(frame_data, frame_duration_ms)
        
        previous_state = self._state
        audio_data = None
        
        if self._state == SpeechState.SILENCE:
            if is_speech:
                # Speech started
                self._state = SpeechState.SPEAKING
                self._speech_frames = 1
                self._silence_frames = 0
                self._buffer.speech_start_ms = max(
                    0, 
                    self._buffer.total_duration_ms - frame_duration_ms - self.config.speech_pad_ms
                )
                
                if self._on_speech_start:
                    try:
                        self._on_speech_start()
                    except Exception as e:
                        logger.warning("Speech start callback failed", error=str(e))
                
                logger.debug("Speech started", 
                           buffer_duration_ms=self._buffer.total_duration_ms)
            else:
                # Still silence, trim buffer to prevent memory growth
                if self._buffer.total_duration_ms > 5000:  # Keep max 5 seconds
                    # Keep only last 500ms for padding
                    self._trim_buffer(500)
        
        elif self._state == SpeechState.SPEAKING:
            if is_speech:
                # Continue speaking
                self._speech_frames += 1
                self._silence_frames = 0
            else:
                # Pause in speech
                self._silence_frames += 1
                if self._silence_frames >= self._silence_frame_threshold:
                    # Silence threshold reached - speech complete
                    self._state = SpeechState.SPEECH_COMPLETE
                    self._buffer.speech_end_ms = (
                        self._buffer.total_duration_ms - 
                        (self._silence_frames * frame_duration_ms) +
                        self.config.speech_pad_ms
                    )
        
        elif self._state == SpeechState.PAUSE:
            if is_speech:
                # Resume speaking
                self._state = SpeechState.SPEAKING
                self._speech_frames += 1
                self._silence_frames = 0
            else:
                self._silence_frames += 1
                if self._silence_frames >= self._silence_frame_threshold:
                    self._state = SpeechState.SPEECH_COMPLETE
                    self._buffer.speech_end_ms = (
                        self._buffer.total_duration_ms - 
                        (self._silence_frames * frame_duration_ms) +
                        self.config.speech_pad_ms
                    )
        
        # Handle speech complete
        is_speech_complete = False
        if self._state == SpeechState.SPEECH_COMPLETE:
            # Check if we have enough speech
            if self._speech_frames >= self._min_speech_frames:
                is_speech_complete = True
                # #region agent log
                try:
                    import json
                    with open("/Users/user/Fortell_AI_Product/.cursor/debug.log", "a") as _f:
                        _f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H3,H5","location":"vad_processor.py:SPEECH_COMPLETE","message":"VAD marked speech complete","data":{"silence_frames":self._silence_frames,"speech_frames":self._speech_frames,"silence_frame_threshold":self._silence_frame_threshold,"silence_threshold_ms":self.config.silence_threshold_ms},"timestamp":__import__("time").time()*1000}) + "\n")
                except Exception:
                    pass
                # #endregion
                audio_data = self._buffer.get_speech_segment(self.config.sample_rate)
                
                if self._on_speech_end:
                    try:
                        self._on_speech_end()
                    except Exception as e:
                        logger.warning("Speech end callback failed", error=str(e))
                
                logger.info("Speech complete",
                          speech_frames=self._speech_frames,
                          duration_ms=self._speech_frames * self.config.frame_duration_ms,
                          audio_size=len(audio_data) if audio_data else 0)
            else:
                logger.debug("Speech too short, ignoring",
                           speech_frames=self._speech_frames,
                           min_required=self._min_speech_frames)
            
            # Reset for next utterance
            self.reset()
        
        return VADResult(
            is_speech_complete=is_speech_complete,
            audio_data=audio_data,
            state=self._state,
            is_speaking=is_speech,
            speech_duration_ms=self._speech_frames * self.config.frame_duration_ms
        )
    
    def _trim_buffer(self, keep_ms: float):
        """Trim buffer to keep only last N milliseconds"""
        if not self._buffer.frames:
            return
        
        # Calculate how many frames to keep
        bytes_per_ms = (self.config.sample_rate * 2) / 1000
        keep_bytes = int(keep_ms * bytes_per_ms)
        
        all_audio = self._buffer.get_audio_bytes()
        if len(all_audio) > keep_bytes:
            trimmed = all_audio[-keep_bytes:]
            self._buffer.frames = [trimmed]
            self._buffer.total_duration_ms = keep_ms


@dataclass
class VADResult:
    """Result from processing an audio frame"""
    is_speech_complete: bool = False
    audio_data: Optional[bytes] = None
    state: SpeechState = SpeechState.SILENCE
    is_speaking: bool = False
    speech_duration_ms: float = 0.0
    
    def __bool__(self):
        """Allow using as boolean - True when speech complete"""
        return self.is_speech_complete


# Convenience function for one-off VAD processing
async def process_audio_with_vad(
    audio_frames: List[Any],
    config: Optional[VADConfig] = None
) -> List[bytes]:
    """
    Process a list of audio frames and return speech segments.
    
    Args:
        audio_frames: List of audio frames (with .data attribute)
        config: VAD configuration
    
    Returns:
        List of audio byte segments (one per detected utterance)
    """
    vad = VADProcessor(config)
    await vad.initialize()
    
    segments = []
    for frame in audio_frames:
        result = await vad.process_frame(frame)
        if result.is_speech_complete and result.audio_data:
            segments.append(result.audio_data)
    
    return segments
