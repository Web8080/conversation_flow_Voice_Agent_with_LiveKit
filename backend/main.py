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
import json
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
        self.buffer_duration = 1.5  # Reduced from 2.0 for faster responses
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
                logger.info("DEBUG: Creating AudioStream", track_type=type(track).__name__, hypothesis="H1")
                
                try:
                    # Create AudioStream from RemoteAudioTrack
                    audio_stream = rtc.AudioStream(track)
                    logger.info("DEBUG: AudioStream created", has_audio_stream=True, hypothesis="H1")
                except AttributeError as e:
                    logger.error("DEBUG: AudioStream not available", error=str(e), hypothesis="H1")
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
                    async for audio_frame_event in audio_stream:
                        frame_count += 1
                        
                        # Extract AudioFrame from AudioFrameEvent
                        # AudioStream yields AudioFrameEvent objects, not AudioFrame directly
                        audio_frame = None
                        if isinstance(audio_frame_event, rtc.AudioFrame):
                            audio_frame = audio_frame_event
                        else:
                            # Try multiple ways to extract AudioFrame from AudioFrameEvent
                            # AudioFrameEvent might have .frame, .audio_frame, or be directly accessible
                            if hasattr(audio_frame_event, 'frame'):
                                try:
                                    potential_frame = audio_frame_event.frame
                                    if isinstance(potential_frame, rtc.AudioFrame):
                                        audio_frame = potential_frame
                                except Exception as e:
                                    if frame_count == 1:
                                        logger.debug("Failed to access .frame", error=str(e), hypothesis="H2")
                            
                            if audio_frame is None and hasattr(audio_frame_event, 'audio_frame'):
                                try:
                                    potential_frame = audio_frame_event.audio_frame
                                    if isinstance(potential_frame, rtc.AudioFrame):
                                        audio_frame = potential_frame
                                except Exception as e:
                                    if frame_count == 1:
                                        logger.debug("Failed to access .audio_frame", error=str(e), hypothesis="H2")
                            
                            # Try using AudioFrameEvent directly if it has AudioFrame-like interface
                            if audio_frame is None and hasattr(audio_frame_event, 'data'):
                                try:
                                    # Check if it has the same interface as AudioFrame
                                    if hasattr(audio_frame_event, 'sample_rate') and hasattr(audio_frame_event, 'num_channels'):
                                        # Treat as AudioFrame-like object
                                        audio_frame = audio_frame_event
                                except:
                                    pass
                            
                            # Log structure on first frame for debugging
                            if audio_frame is None and frame_count == 1:
                                attrs = [a for a in dir(audio_frame_event) if not a.startswith('_')]
                                logger.info("DEBUG: AudioFrameEvent structure", 
                                           event_type=type(audio_frame_event).__name__,
                                           has_data=hasattr(audio_frame_event, 'data'),
                                           has_frame=hasattr(audio_frame_event, 'frame'),
                                           has_audio_frame=hasattr(audio_frame_event, 'audio_frame'),
                                           attrs=attrs[:20],
                                           hypothesis="H2")
                        
                        # Final check: ensure we have a valid AudioFrame or AudioFrame-like object
                        if audio_frame is None:
                            # Skip invalid frames but continue processing
                            if frame_count % 500 == 0:  # Log less frequently
                                logger.warning("DEBUG: Skipping invalid frame", 
                                             frame_count=frame_count,
                                             event_type=type(audio_frame_event).__name__,
                                             hypothesis="H2")
                            continue
                        
                        # Verify audio_frame has required attributes
                        if not hasattr(audio_frame, 'data'):
                            if frame_count % 500 == 0:
                                logger.warning("DEBUG: Frame missing data attribute", 
                                             frame_count=frame_count,
                                             frame_type=type(audio_frame).__name__,
                                             hypothesis="H2")
                            continue
                        
                        try:
                            # Log audio frame format on first frame
                            if frame_count == 1:
                                sample_rate = getattr(audio_frame, 'sample_rate', None)
                                num_channels = getattr(audio_frame, 'num_channels', None)
                                samples_per_channel = getattr(audio_frame, 'samples_per_channel', None)
                                data_size = len(audio_frame.data.tobytes()) if hasattr(audio_frame, 'data') else None
                                logger.info("DEBUG: First audio frame format", 
                                           sample_rate=sample_rate,
                                           num_channels=num_channels,
                                           samples_per_channel=samples_per_channel,
                                           data_size=data_size,
                                           frame_type=type(audio_frame).__name__,
                                           hypothesis="AUDIO_FORMAT")
                            
                            self.audio_buffer.append(audio_frame)
                            current_time = asyncio.get_event_loop().time()
                            
                            if self.last_audio_time is None:
                                logger.info("DEBUG: Initializing last_audio_time", current_time=current_time, hypothesis="H2")
                                self.last_audio_time = current_time
                            
                            # Process buffer every buffer_duration seconds
                            time_diff = current_time - self.last_audio_time
                            
                            # Log timing info every 100 frames to see what's happening
                            if frame_count % 100 == 0:
                                logger.info("DEBUG: Time check", 
                                           frame_count=frame_count,
                                           buffer_size=len(self.audio_buffer),
                                           current_time=current_time,
                                           last_audio_time=self.last_audio_time,
                                           time_diff=time_diff,
                                           buffer_duration=self.buffer_duration,
                                           should_process=time_diff >= self.buffer_duration,
                                           hypothesis="H2")
                            
                            if time_diff >= self.buffer_duration:
                                logger.info("DEBUG: Buffer ready for processing", 
                                          buffer_size=len(self.audio_buffer), 
                                          buffer_duration=self.buffer_duration,
                                          time_diff=time_diff,
                                          hypothesis="H2")
                                # Copy buffer before clearing (avoid race condition)
                                buffer_to_process = self.audio_buffer.copy()
                                self.audio_buffer = []
                                self.last_audio_time = current_time
                                # Process buffer (don't await here to avoid blocking)
                                asyncio.create_task(self.process_audio_buffer(buffer_to_process))
                                    
                        except Exception as e:
                            logger.error("Error processing audio frame", error=str(e), hypothesis="H2")
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
    
    async def process_audio_buffer(self, buffer_to_process=None):
        """Process buffered audio frames: STT → LLM → TTS"""
        # Use provided buffer or fall back to instance buffer
        if buffer_to_process is None:
            buffer_to_process = self.audio_buffer
        
        if not buffer_to_process:
            logger.info("DEBUG: Empty audio buffer, skipping", hypothesis="H2")
            return
        
        logger.info("DEBUG: Processing audio buffer", buffer_size=len(buffer_to_process), hypothesis="H2")
        
        try:
            # Log audio frame format before combining
            sample_rate = None
            num_channels = None
            if buffer_to_process:
                first_frame = buffer_to_process[0]
                sample_rate = getattr(first_frame, 'sample_rate', None)
                num_channels = getattr(first_frame, 'num_channels', None)
                logger.info("DEBUG: Audio buffer format before combining",
                           sample_rate=sample_rate,
                           num_channels=num_channels,
                           frame_count=len(buffer_to_process),
                           first_frame_type=type(first_frame).__name__,
                           first_frame_attrs=[a for a in dir(first_frame) if not a.startswith('_')][:10],
                           hypothesis="AUDIO_FORMAT")
            
            # Validate audio format parameters
            if not sample_rate or sample_rate <= 0:
                logger.error("DEBUG: Invalid sample_rate", 
                           sample_rate=sample_rate,
                           hypothesis="AUDIO_INVALID")
                return
            
            if not num_channels or num_channels <= 0:
                logger.error("DEBUG: Invalid num_channels", 
                           num_channels=num_channels,
                           hypothesis="AUDIO_INVALID")
                return
            
            # Combine audio frames
            combined_audio = buffer_to_process[0].data.tobytes()
            for frame in buffer_to_process[1:]:
                combined_audio += frame.data.tobytes()
            
            # #region debug log
            logger.info("DEBUG: Combined audio data", audio_size=len(combined_audio), hypothesis="F")
            # #endregion
            
            # Step 1: Speech-to-Text
            logger.info("DEBUG: Calling STT transcribe", 
                       audio_size=len(combined_audio),
                       sample_rate=sample_rate,
                       num_channels=num_channels,
                       hypothesis="STT_CALL")
            
            # Pass sample_rate and num_channels to STT service
            user_text = await self.stt_service.transcribe(combined_audio, sample_rate, num_channels)
            
            logger.info("DEBUG: STT transcribe completed", 
                       user_text=user_text if user_text else "None",
                       user_text_repr=repr(user_text) if user_text else "None",
                       text_length=len(user_text) if user_text else 0,
                       text_stripped_length=len(user_text.strip()) if user_text else 0,
                       hypothesis="STT_RESULT")
            
            if not user_text:
                logger.warning("DEBUG: STT returned None - returning early", 
                             hypothesis="STT_NONE")
                return
            
            if len(user_text.strip()) < 2:
                logger.warning("DEBUG: STT returned text too short - returning early", 
                             user_text=user_text,
                             user_text_repr=repr(user_text),
                             text_length=len(user_text),
                             text_stripped_length=len(user_text.strip()),
                             hypothesis="STT_TOO_SHORT")
                return
            
            logger.info("DEBUG: User text passed validation", 
                       user_text=user_text[:100],
                       text_length=len(user_text),
                       hypothesis="STT_VALID")
            
            logger.info("User said", text=user_text[:100])
            
            # Send user transcription to frontend via data message
            try:
                import json
                await self.ctx.room.local_participant.publish_data(
                    json.dumps({
                        "type": "user_transcription",
                        "text": user_text
                    }).encode('utf-8'),
                    reliable=True
                )
            except Exception as e:
                logger.warning("Failed to send user transcription", error=str(e))
            
            # Step 2: LLM Response (simple single prompt, no state machine)
            logger.info("DEBUG: Calling LLM get_llm_response", 
                       user_text=user_text[:100],
                       user_text_full=user_text,
                       hypothesis="LLM_CALL")
            
            response_text = await self.get_llm_response(user_text)
            
            logger.info("DEBUG: LLM response received", 
                       response_text=response_text if response_text else "None",
                       response_text_repr=repr(response_text) if response_text else "None",
                       response_length=len(response_text) if response_text else 0,
                       hypothesis="LLM_RESULT")
            
            if not response_text:
                logger.warning("DEBUG: LLM returned empty response - using fallback", 
                             hypothesis="LLM_EMPTY")
                response_text = "I'm sorry, I didn't understand. Could you repeat that?"
            
            # Send agent transcription to frontend via data message
            try:
                import json
                await self.ctx.room.local_participant.publish_data(
                    json.dumps({
                        "type": "agent_transcription",
                        "text": response_text
                    }).encode('utf-8'),
                    reliable=True
                )
            except Exception as e:
                logger.warning("Failed to send agent transcription", error=str(e))
            
            # Step 3: Text-to-Speech
            logger.info("DEBUG: Calling TTS say", response_text=response_text[:100], hypothesis="H5")
            
            await self.say(response_text)
            
            logger.info("DEBUG: TTS say completed", hypothesis="H5")
            
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
            logger.info("DEBUG: Building LLM messages", 
                       user_text=user_text,
                       history_length=len(self.conversation_history),
                       hypothesis="LLM_BUILD")
            
            # Build messages with system prompt and conversation history
            messages = [{"role": "system", "content": STAGE1_SYSTEM_PROMPT}]
            messages.extend(self.conversation_history)
            messages.append({"role": "user", "content": user_text})
            
            logger.info("DEBUG: Messages built", 
                       total_messages=len(messages),
                       last_user_message=messages[-1]["content"] if messages else None,
                       hypothesis="LLM_BUILD")
            
            # Call LLM service
            context = {
                "system_prompt": STAGE1_SYSTEM_PROMPT,
                "history": self.conversation_history
            }
            
            logger.info("DEBUG: Calling LLM service generate_response", 
                       user_text=user_text,
                       hypothesis="LLM_GENERATE")
            
            response = await self.llm_service.generate_response(user_text, context)
            
            logger.info("DEBUG: LLM service returned", 
                       response=response if response else "None",
                       response_repr=repr(response) if response else "None",
                       response_type=type(response).__name__,
                       hypothesis="LLM_RETURN")
            
            return response if response else None
            
        except Exception as e:
            logger.error("DEBUG: LLM response failed with exception", 
                        error=str(e),
                        error_type=type(e).__name__,
                        error_traceback=str(e.__traceback__) if hasattr(e, '__traceback__') else None,
                        hypothesis="LLM_ERROR")
            return None
    
    async def say(self, text: str):
        """Synthesize and speak text"""
        try:
            logger.info("Agent responding", text=text[:100])
            
            logger.info("DEBUG: TTS synthesize called", text=text[:100], hypothesis="H5")
            
            audio_data = await self.tts_service.synthesize(text)
            
            logger.info("DEBUG: TTS synthesize completed", 
                       audio_data_size=len(audio_data) if audio_data else 0,
                       has_audio_source=self.audio_source is not None,
                       hypothesis="H5")
            
            if audio_data and self.audio_source:
                import numpy as np
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                samples = len(audio_array)
                
                logger.debug("DEBUG: Preparing audio frame for capture", samples=samples, hypothesis="H5")
                
                audio_frame = rtc.AudioFrame(
                    data=audio_array.tobytes(),
                    sample_rate=24000,
                    num_channels=1,
                    samples_per_channel=samples
                )
                await self.audio_source.capture_frame(audio_frame)
                
                logger.info("DEBUG: Audio frame captured successfully", samples=samples, hypothesis="H5")
                
                logger.debug("Audio response sent", text_length=len(text), samples=samples)
        except Exception as e:
            logger.error("Error synthesizing speech", error=str(e), hypothesis="H5")


async def entrypoint(ctx: JobContext):
    """Main entrypoint - routes to Stage 1 or Stage 2 based on configuration"""
    # #region debug log
    logger.info("DEBUG: Agent entrypoint called", 
                room=ctx.room.name,
                room_id=ctx.room.sid if hasattr(ctx.room, 'sid') else None,
                hypothesis="D")
    # #endregion
    
    # Route to appropriate stage based on configuration
    # #region agent log
    try:
        with open("/Users/user/Fortell_AI_Product/.cursor/debug.log", "a") as _f:
            _f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1","location":"main.py:route","message":"Stage routing","data":{"agent_stage":getattr(settings,"agent_stage",None)},"timestamp":__import__("time").time()*1000}) + "\n")
    except Exception:
        pass
    # #endregion
    if settings.agent_stage == "stage3":
        # #region agent log
        try:
            with open("/Users/user/Fortell_AI_Product/.cursor/debug.log", "a") as _f:
                _f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1","location":"main.py:stage3","message":"Entered Stage 3","data":{"branch":"stage3"},"timestamp":__import__("time").time()*1000}) + "\n")
        except Exception:
            pass
        # #endregion
        logger.info("Routing to Stage 3 agent (JSON flows + VAD)", room=ctx.room.name)
        from main_stage3 import entrypoint as stage3_entrypoint
        await stage3_entrypoint(ctx)
        return
    elif settings.agent_stage == "stage2":
        logger.info("Routing to Stage 2 agent", room=ctx.room.name)
        from main_stage2 import entrypoint as stage2_entrypoint
        await stage2_entrypoint(ctx)
        return
    
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
    # Remove agent_name to enable auto-join (workaround for Twirp API not working)
    # Agents without agent_name automatically join rooms when users connect
    # This bypasses the need for programmatic dispatch via Twirp API
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        # agent_name="appointment-scheduler"  # Disabled to enable auto-join
    ))
