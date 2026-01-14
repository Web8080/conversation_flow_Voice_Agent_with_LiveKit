"""
Stage 1: Basic Single-Prompt Voice Agent

Simple voice agent that:
1. Joins LiveKit room
2. Listens to user's voice
3. Transcribes to text (STT)
4. Sends to LLM (single prompt, no state machine)
5. Synthesizes response to speech (TTS)
6. Plays audio back into room
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from livekit import rtc, agents
from livekit.agents import JobContext, WorkerOptions, cli
from agent.services.stt_service import create_stt_service
from agent.services.llm_service import create_llm_service
from agent.services.tts_service import create_tts_service
from config.settings import settings
from utils.logger import logger

# Simple system prompt for Stage 1 (natural conversation, no appointment scheduling)
STAGE1_SYSTEM_PROMPT = """You are a helpful and friendly voice assistant. 
Respond naturally to the user's questions and conversations. 
Keep your responses concise (1-2 sentences) suitable for voice interaction.
Be conversational and helpful."""


class Stage1VoiceAgent:
    def __init__(self, ctx: JobContext):
        self.ctx = ctx
        self.stt_service = None
        self.llm_service = None
        self.tts_service = None
        self.audio_source = None
        self.audio_track = None
        self.audio_buffer = []
        self.buffer_duration = 2.0
        self.last_audio_time = None
        self.conversation_history = []
    
    async def initialize(self):
        """Initialize all services"""
        try:
            logger.info("Initializing Stage 1 Voice Agent")
            
            self.stt_service = create_stt_service()
            self.llm_service = create_llm_service()
            self.tts_service = create_tts_service()
            
            self.audio_source = rtc.AudioSource(24000, 1)
            self.audio_track = rtc.LocalAudioTrack.create_audio_track(
                "agent-voice",
                self.audio_source
            )
            
            await self.ctx.room.local_participant.publish_track(
                self.audio_track,
                rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
            )
            
            logger.info("Stage 1 Voice Agent initialized successfully")
            
            # Send initial greeting
            greeting = "Hello! I'm your voice assistant. How can I help you today?"
            await self.say(greeting)
            
        except Exception as e:
            logger.error("Failed to initialize agent", error=str(e))
            raise
    
    async def process_audio_stream(self, track: rtc.Track):
        """Process incoming audio stream from user using AudioStream"""
        logger.info("Processing audio stream from participant", track_type=type(track).__name__)
        
        try:
            # For RemoteAudioTrack, we need to use AudioStream wrapper
            if isinstance(track, rtc.RemoteAudioTrack):
                # #region debug log
                logger.info("DEBUG: Creating AudioStream", track_type=type(track).__name__, hypothesis="F")
                # #endregion
                
                try:
                    # Create AudioStream from RemoteAudioTrack
                    audio_stream = rtc.AudioStream(track)
                    # #region debug log
                    logger.info("DEBUG: AudioStream created", has_audio_stream=True, hypothesis="F")
                    # #endregion
                except AttributeError as e:
                    # #region debug log
                    logger.error("DEBUG: AudioStream not available", error=str(e), hypothesis="F")
                    # #endregion
                    logger.error("AudioStream not available in this SDK version", error=str(e))
                    return
                except Exception as e:
                    # #region debug log
                    logger.error("DEBUG: Failed to create AudioStream", error=str(e), hypothesis="F")
                    # #endregion
                    logger.error("Failed to create AudioStream", error=str(e))
                    return
                
                try:
                    frame_count = 0
                    # Iterate directly over audio frames from the stream
                    async for audio_frame in audio_stream:
                        frame_count += 1
                        # #region debug log
                        if frame_count % 100 == 0:  # Log every 100 frames to avoid spam
                            logger.info("DEBUG: Processing audio frame", frame_count=frame_count, hypothesis="F")
                        # #endregion
                        
                        if isinstance(audio_frame, rtc.AudioFrame):
                            try:
                                self.audio_buffer.append(audio_frame)
                                current_time = asyncio.get_event_loop().time()
                                
                                if self.last_audio_time is None:
                                    self.last_audio_time = current_time
                                
                                # Process buffer every buffer_duration seconds
                                if current_time - self.last_audio_time >= self.buffer_duration:
                                    # #region debug log
                                    logger.info("DEBUG: Buffer ready for processing", buffer_size=len(self.audio_buffer), hypothesis="F")
                                    # #endregion
                                    # Process buffer (don't await here to avoid blocking)
                                    asyncio.create_task(self.process_audio_buffer())
                                    self.audio_buffer = []
                                    self.last_audio_time = current_time
                                    
                            except Exception as e:
                                logger.error("Error processing audio frame", error=str(e))
                    # #region debug log
                    logger.info("DEBUG: Audio stream iteration ended", total_frames=frame_count, hypothesis="F")
                    # #endregion
                except AttributeError as e:
                    # #region debug log
                    logger.error("DEBUG: AudioStream not async iterable", error=str(e), hypothesis="F")
                    # #endregion
                    logger.error("AudioStream is not async iterable", error=str(e))
                except Exception as e:
                    # #region debug log
                    logger.error("DEBUG: Error iterating AudioStream", error=str(e), error_type=type(e).__name__, hypothesis="F")
                    # #endregion
                    logger.error("Error iterating audio stream", error=str(e))
                finally:
                    # Close the audio stream when done
                    try:
                        if hasattr(audio_stream, 'aclose'):
                            await audio_stream.aclose()
                        elif hasattr(audio_stream, 'close'):
                            audio_stream.close()
                    except Exception as e:
                        logger.warning("Error closing audio stream", error=str(e))
            else:
                # For other track types, try direct async iteration
                async for frame in track:
                    if isinstance(frame, rtc.AudioFrame):
                        try:
                            self.audio_buffer.append(frame)
                            current_time = asyncio.get_event_loop().time()
                            
                            if self.last_audio_time is None:
                                self.last_audio_time = current_time
                            
                            # Process buffer every buffer_duration seconds
                            if current_time - self.last_audio_time >= self.buffer_duration:
                                asyncio.create_task(self.process_audio_buffer())
                                self.audio_buffer = []
                                self.last_audio_time = current_time
                                
                        except Exception as e:
                            logger.error("Error processing audio frame", error=str(e))
        except AttributeError as e:
            logger.error("Track does not support audio processing", error=str(e), track_type=type(track).__name__)
        except Exception as e:
            logger.error("Error processing audio stream", error=str(e), track_type=type(track).__name__)
    
    async def process_audio_buffer(self):
        """Process buffered audio frames: STT → LLM → TTS"""
        if not self.audio_buffer:
            # #region debug log
            logger.debug("DEBUG: Empty audio buffer, skipping", hypothesis="F")
            # #endregion
            return
        
        # #region debug log
        logger.info("DEBUG: Processing audio buffer", buffer_size=len(self.audio_buffer), hypothesis="F")
        # #endregion
        
        try:
            # Combine audio frames
            combined_audio = self.audio_buffer[0].data.tobytes()
            for frame in self.audio_buffer[1:]:
                combined_audio += frame.data.tobytes()
            
            # #region debug log
            logger.info("DEBUG: Combined audio data", audio_size=len(combined_audio), hypothesis="F")
            # #endregion
            
            # Step 1: Speech-to-Text
            user_text = await self.stt_service.transcribe(combined_audio)
            
            if not user_text or len(user_text.strip()) < 2:
                logger.debug("No meaningful text transcribed")
                return
            
            logger.info("User said", text=user_text[:100])
            
            # Step 2: LLM Response (simple single prompt, no state machine)
            response_text = await self.get_llm_response(user_text)
            
            if not response_text:
                response_text = "I'm sorry, I didn't understand. Could you repeat that?"
            
            # Step 3: Text-to-Speech
            await self.say(response_text)
            
            # Store in conversation history (for context)
            self.conversation_history.append({"role": "user", "content": user_text})
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            # Keep history limited (last 10 exchanges)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
                
        except Exception as e:
            logger.error("Error processing audio buffer", error=str(e))
            await self.say("I encountered an error. Please try again.")
    
    async def get_llm_response(self, user_text: str) -> str:
        """Get LLM response with simple single prompt"""
        try:
            # Build messages with system prompt and conversation history
            messages = [{"role": "system", "content": STAGE1_SYSTEM_PROMPT}]
            messages.extend(self.conversation_history)
            messages.append({"role": "user", "content": user_text})
            
            # Call LLM service
            context = {
                "system_prompt": STAGE1_SYSTEM_PROMPT,
                "history": self.conversation_history
            }
            
            response = await self.llm_service.generate_response(user_text, context)
            return response if response else None
            
        except Exception as e:
            logger.error("LLM response failed", error=str(e))
            return None
    
    async def say(self, text: str):
        """Synthesize and speak text"""
        try:
            logger.info("Agent responding", text=text[:100])
            audio_data = await self.tts_service.synthesize(text)
            
            if audio_data and self.audio_source:
                import numpy as np
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                samples = len(audio_array)
                
                audio_frame = rtc.AudioFrame(
                    data=audio_array.tobytes(),
                    sample_rate=24000,
                    num_channels=1,
                    samples_per_channel=samples
                )
                await self.audio_source.capture_frame(audio_frame)
                logger.debug("Audio response sent", text_length=len(text), samples=samples)
        except Exception as e:
            logger.error("Error synthesizing speech", error=str(e))


async def entrypoint(ctx: JobContext):
    """Main entrypoint for Stage 1 agent"""
    # #region debug log
    logger.info("DEBUG: Agent entrypoint called", 
                room=ctx.room.name,
                room_id=ctx.room.sid if hasattr(ctx.room, 'sid') else None,
                hypothesis="D")
    # #endregion
    
    logger.info("Stage 1 agent started", room=ctx.room.name)
    
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    
    # #region debug log
    logger.info("DEBUG: Agent connected to room", 
                room=ctx.room.name,
                local_identity=ctx.room.local_participant.identity,
                local_name=ctx.room.local_participant.name,
                remote_participants=len(ctx.room.remote_participants),
                hypothesis="D")
    # #endregion
    
    try:
        agent = Stage1VoiceAgent(ctx)
        await agent.initialize()
        
        logger.info("Agent initialized, waiting for participants...")
        
        def on_track_subscribed(
            track: rtc.Track, 
            publication: rtc.TrackPublication, 
            participant: rtc.RemoteParticipant
        ):
            # Synchronous callback wrapper - use asyncio.create_task inside
            # #region debug log
            logger.info("DEBUG: Track subscribed event", 
                       track_kind=track.kind, 
                       participant_identity=participant.identity,
                       track_type=type(track).__name__,
                       hypothesis="G")
            # #endregion
            
            # Check if this is an audio track from a non-agent participant
            is_audio = track.kind == rtc.TrackKind.KIND_AUDIO
            is_not_agent = participant.identity != "agent" and not participant.identity.startswith("agent-")
            
            # #region debug log
            logger.info("DEBUG: Track subscription check", 
                       is_audio=is_audio,
                       is_not_agent=is_not_agent,
                       participant_identity=participant.identity,
                       hypothesis="G")
            # #endregion
            
            if is_audio and is_not_agent:
                logger.info("Audio track subscribed", participant=participant.identity)
                # process_audio_stream is async - wrap in create_task
                # Works with any Track type that supports async iteration
                asyncio.create_task(agent.process_audio_stream(track))
            else:
                # #region debug log
                logger.debug("DEBUG: Skipping track", 
                           reason="not_audio" if not is_audio else "is_agent",
                           hypothesis="G")
                # #endregion
        
        ctx.room.on("track_subscribed", on_track_subscribed)
        
        # Handle existing tracks
        # #region debug log
        logger.info("DEBUG: Checking existing tracks", 
                   participant_count=len(ctx.room.remote_participants),
                   hypothesis="G")
        # #endregion
        
        for participant in ctx.room.remote_participants.values():
            # #region debug log
            logger.info("DEBUG: Checking participant tracks", 
                       participant_identity=participant.identity,
                       track_count=len(participant.track_publications),
                       hypothesis="G")
            # #endregion
            
            for publication in participant.track_publications.values():
                # #region debug log
                logger.info("DEBUG: Checking publication", 
                           publication_kind=publication.kind,
                           has_track=publication.track is not None,
                           hypothesis="G")
                # #endregion
                
                if publication.track and publication.kind == rtc.TrackKind.KIND_AUDIO:
                    # #region debug log
                    logger.info("DEBUG: Processing existing audio track", 
                               participant_identity=participant.identity,
                               hypothesis="G")
                    # #endregion
                    # Process any audio track (works with RemoteAudioTrack and others)
                    asyncio.create_task(agent.process_audio_stream(publication.track))
        
        # Wait for room to disconnect
        # Use room's disconnect event
        disconnect_event = asyncio.Event()
        
        def on_disconnected():
            disconnect_event.set()
        
        ctx.room.on("disconnected", on_disconnected)
        
        # Wait until disconnected
        await disconnect_event.wait()
        logger.info("Agent disconnected")
        
    except Exception as e:
        logger.error("Agent initialization failed", error=str(e))
        raise


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="appointment-scheduler"
    ))
