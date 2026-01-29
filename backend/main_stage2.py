"""
Stage 2: Structured Conversation Flow Agent

State-based voice agent that:
1. Uses a conversation state machine (DAG)
2. Handles appointment scheduling with structured flow
3. Integrates with Google Calendar for booking
4. Sends state updates to frontend
5. Properly handles fallback and terminal states
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
from agent.services.calendar_service import CalendarService
from agent.state_machine.state_machine import StateMachine
from agent.state_machine.state import ConfirmationState
from agent.state_machine.context import ConversationContext
from config.settings import settings
from utils.logger import logger


class Stage2VoiceAgent:
    def __init__(self, ctx: JobContext):
        self.ctx = ctx
        self.stt_service = None
        self.llm_service = None
        self.tts_service = None
        self.calendar_service = None
        self.state_machine = None
        self.context = None
        self.audio_source = None
        self.audio_track = None
        self.audio_buffer = []
        self.buffer_duration = 1.5
        self.last_audio_time = None
    
    async def initialize(self):
        """Initialize all services and state machine"""
        try:
            logger.info("Initializing Stage 2 Voice Agent")
            
            # Initialize services
            self.stt_service = create_stt_service()
            self.llm_service = create_llm_service()
            self.tts_service = create_tts_service()
            self.calendar_service = CalendarService()
            
            # Initialize state machine
            self.state_machine = StateMachine(self.llm_service)
            
            # Set calendar service for confirmation state
            confirmation_state = self.state_machine.states.get("confirmation")
            if confirmation_state and isinstance(confirmation_state, ConfirmationState):
                confirmation_state.set_calendar_service(self.calendar_service)
            
            # Initialize conversation context
            session_id = f"session_{id(self)}"
            self.context = ConversationContext(session_id=session_id)
            self.state_machine.reset_to_initial_state(self.context)
            
            # Setup audio output
            self.audio_source = rtc.AudioSource(24000, 1)
            self.audio_track = rtc.LocalAudioTrack.create_audio_track(
                "agent-voice",
                self.audio_source
            )
            
            await self.ctx.room.local_participant.publish_track(
                self.audio_track,
                rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
            )
            
            logger.info("Stage 2 Voice Agent initialized successfully")
            
            # Send initial greeting from greeting state
            initial_prompt = self.state_machine.get_initial_prompt(self.context)
            await self.say(initial_prompt)
            
            # Send state update to frontend
            await self.send_state_update(self.context.current_state, self.context.slots)
            
        except Exception as e:
            logger.error("Failed to initialize agent", error=str(e))
            raise
    
    async def send_state_update(self, state: str, slots: dict):
        """Send state update to frontend via data message"""
        try:
            import json
            await self.ctx.room.local_participant.publish_data(
                json.dumps({
                    "type": "state_update",
                    "state": state,
                    "slots": slots
                }).encode('utf-8'),
                reliable=True
            )
            logger.debug("State update sent", state=state, slots_count=len(slots))
        except Exception as e:
            logger.warning("Failed to send state update", error=str(e))
    
    async def process_audio_stream(self, track: rtc.Track):
        """Process incoming audio stream from user"""
        logger.info("Processing audio stream from participant", track_type=type(track).__name__)
        
        try:
            if isinstance(track, rtc.RemoteAudioTrack):
                audio_stream = rtc.AudioStream(track)
                
                async for audio_frame_event in audio_stream:
                    # Extract AudioFrame from event
                    audio_frame = None
                    if hasattr(audio_frame_event, 'frame'):
                        audio_frame = audio_frame_event.frame
                    elif hasattr(audio_frame_event, 'audio_frame'):
                        audio_frame = audio_frame_event.audio_frame
                    elif isinstance(audio_frame_event, rtc.AudioFrame):
                        audio_frame = audio_frame_event
                    
                    if audio_frame:
                        await self.process_audio_frame(audio_frame)
                        
        except Exception as e:
            logger.error("Error processing audio stream", error=str(e))
    
    async def process_audio_frame(self, audio_frame: rtc.AudioFrame):
        """Process a single audio frame"""
        current_time = asyncio.get_event_loop().time()
        
        if self.last_audio_time is None:
            self.last_audio_time = current_time
        
        self.audio_buffer.append(audio_frame)
        
        # Check if buffer duration reached
        time_diff = current_time - self.last_audio_time
        if time_diff >= self.buffer_duration:
            # Process buffer
            buffer_copy = list(self.audio_buffer)
            self.audio_buffer.clear()
            self.last_audio_time = current_time
            
            # Process in background
            asyncio.create_task(self.process_audio_buffer(buffer_copy))
    
    async def process_audio_buffer(self, audio_frames: list):
        """Process accumulated audio frames"""
        try:
            if not audio_frames:
                return
            
            # Combine audio frames
            sample_rate = audio_frames[0].sample_rate
            num_channels = audio_frames[0].num_channels
            
            combined_data = []
            for frame in audio_frames:
                audio_data = frame.data.tobytes()
                combined_data.append(audio_data)
            
            combined_audio = b''.join(combined_data)
            
            # Step 1: Speech-to-Text
            user_text = await self.stt_service.transcribe(
                combined_audio,
                sample_rate=sample_rate,
                num_channels=num_channels
            )
            
            if not user_text or len(user_text.strip()) == 0:
                return
            
            logger.info("User said", text=user_text)
            
            # Send user transcription to frontend
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
            
            # Step 2: Process through state machine
            response = await self.state_machine.process_user_input(
                user_text=user_text,
                context=self.context
            )
            
            response_text = response.response_text
            
            if not response_text:
                response_text = "I'm sorry, I didn't understand. Could you repeat that?"
            
            # Update state if changed
            if response.next_state and response.next_state != self.context.current_state:
                await self.send_state_update(response.next_state, self.context.slots)
            
            # Send agent transcription to frontend
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
            await self.say(response_text)
            
            # Check if conversation should end
            if not response.should_continue:
                logger.info("Conversation ended", state=self.context.current_state)
                await self.send_state_update("terminal", self.context.slots)
                
        except Exception as e:
            logger.error("Error processing audio buffer", error=str(e))
            await self.say("I encountered an error. Please try again.")
    
    async def say(self, text: str):
        """Synthesize and play text as speech"""
        try:
            audio_data = await self.tts_service.synthesize(text)
            if not audio_data:
                return
            
            # Convert audio data to AudioFrame and send
            import numpy as np
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Assuming 24kHz sample rate (adjust based on TTS service)
            sample_rate = 24000
            num_channels = 1
            
            # Split into chunks
            samples_per_channel = len(audio_array) // num_channels
            chunk_size = sample_rate // 10  # 100ms chunks
            
            for i in range(0, samples_per_channel, chunk_size):
                chunk = audio_array[i:i + chunk_size]
                if len(chunk) == 0:
                    break
                
                # Reshape for multi-channel if needed
                if num_channels > 1:
                    chunk = chunk.reshape(-1, num_channels)
                
                # Create AudioFrame
                audio_frame = rtc.AudioFrame(
                    data=chunk.tobytes(),
                    sample_rate=sample_rate,
                    num_channels=num_channels,
                    samples_per_channel=len(chunk) // num_channels
                )
                
                await self.audio_source.capture_frame(audio_frame)
                
        except Exception as e:
            logger.error("Error synthesizing speech", error=str(e))


async def entrypoint(ctx: JobContext):
    """Main entrypoint for Stage 2 agent"""
    logger.info("Stage 2 agent started", room=ctx.room.name)
    
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    
    logger.info("Agent connected to room", 
                room=ctx.room.name,
                local_identity=ctx.room.local_participant.identity)
    
    try:
        agent = Stage2VoiceAgent(ctx)
        await agent.initialize()
        
        logger.info("Agent initialized, waiting for participants...")
        
        def on_track_subscribed(
            track: rtc.Track, 
            publication: rtc.TrackPublication, 
            participant: rtc.RemoteParticipant
        ):
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                logger.info("Audio track subscribed", participant=participant.identity)
                asyncio.create_task(agent.process_audio_stream(track))
        
        ctx.room.on("track_subscribed", on_track_subscribed)
        
        # Process existing tracks
        for participant in ctx.room.remote_participants.values():
            for publication in participant.track_publications.values():
                if publication.track and publication.kind == rtc.TrackKind.KIND_AUDIO:
                    logger.info("Processing existing audio track", participant=participant.identity)
                    asyncio.create_task(agent.process_audio_stream(publication.track))
        
        # Wait for disconnect
        disconnect_event = asyncio.Event()
        def on_disconnected():
            disconnect_event.set()
        
        ctx.room.on("disconnected", on_disconnected)
        await disconnect_event.wait()
        
    except Exception as e:
        logger.error("Agent error", error=str(e))
        raise


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))


