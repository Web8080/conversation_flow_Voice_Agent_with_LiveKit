"""
Stage 3: JSON-Driven Conversational Flow Agent with VAD

Advanced voice agent that:
1. Loads conversation flows from JSON (Retell-style)
2. Uses Voice Activity Detection (VAD) to properly detect end-of-speech
3. Supports multiple node types (conversation, function, logic_split, end, transfer)
4. Dynamic variable extraction and transition conditions
5. Proper barge-in handling and interruption support

This solves the "bot responds too fast" problem by using VAD instead of
fixed time-based audio buffering.
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
from agent.flow_engine import FlowEngine, VADProcessor, VADConfig
from config.settings import settings
from utils.logger import logger


class Stage3VoiceAgent:
    """
    Stage 3 Voice Agent with JSON flows and VAD.
    
    Key improvements over Stage 2:
    1. VAD-based end-of-speech detection (no more fixed buffers)
    2. JSON-configurable conversation flows
    3. Proper transition conditions with LLM evaluation
    4. Dynamic variable extraction
    """
    
    def __init__(self, ctx: JobContext):
        self.ctx = ctx
        self.stt_service = None
        self.llm_service = None
        self.tts_service = None
        self.calendar_service = None
        self.flow_engine = None
        self.vad_processor = None
        self.session_state = None
        self.audio_source = None
        self.audio_track = None
        
        # State for handling agent speech (for barge-in)
        self._is_speaking = False
        self._current_speech_task = None
        
    async def initialize(self):
        """Initialize all services, flow engine, and VAD"""
        try:
            logger.info("Initializing Stage 3 Voice Agent")
            
            # Initialize services
            self.stt_service = create_stt_service()
            self.llm_service = create_llm_service()
            self.tts_service = create_tts_service()
            self.calendar_service = CalendarService()
            
            # Initialize flow engine
            self.flow_engine = FlowEngine(
                self.llm_service,
                function_registry={}
            )
            
            # Register calendar function
            self.flow_engine.register_function(
                "create_calendar_event",
                self._create_calendar_event
            )
            
            # Load flow from JSON
            flow_path = Path(__file__).parent / "flows" / "appointment_booking.json"
            if flow_path.exists():
                await self.flow_engine.load_flow_from_file(str(flow_path))
                logger.info("Flow loaded from JSON", path=str(flow_path))
            else:
                logger.warning("Flow file not found, using default flow", path=str(flow_path))
                await self._load_default_flow()
            
            # Initialize VAD
            vad_config = VADConfig(
                threshold=0.5,
                min_speech_duration_ms=250,
                silence_threshold_ms=600,
                sample_rate=24000,
                energy_filter_enabled=True
            )
            self.flow_engine.enable_vad(vad_config)
            await self.flow_engine.initialize_vad()
            self.vad_processor = self.flow_engine.vad_processor
            
            # Set callbacks for state changes
            self.flow_engine.set_callbacks(
                on_state_change=self._on_state_change,
                on_response=self._on_response
            )
            
            # Create session
            session_id = f"session_{id(self)}"
            self.session_state = self.flow_engine.create_session(session_id)
            
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
            
            logger.info("Stage 3 Voice Agent initialized successfully")
            
            # Start the flow (send initial greeting)
            result = await self.flow_engine.start(self.session_state)
            if result.response_text:
                await self.say(result.response_text)
            
            # Send initial state to frontend
            await self._send_state_update()
            
        except Exception as e:
            logger.error("Failed to initialize agent", error=str(e))
            raise
    
    async def _load_default_flow(self):
        """Load a default minimal flow if JSON file not found"""
        default_flow = {
            "id": "default-flow",
            "name": "Default Flow",
            "version": "1.0.0",
            "global_settings": {
                "system_prompt": "You are a helpful voice assistant for scheduling appointments.",
                "vad_enabled": True,
                "silence_threshold_ms": 600
            },
            "start_node_id": "greeting",
            "nodes": [
                {
                    "id": "greeting",
                    "type": "conversation",
                    "name": "Greeting",
                    "instruction": "Greet the user and offer to help schedule an appointment.",
                    "response_template": "Hello! I can help you schedule an appointment. What's your name?",
                    "extract_variables": ["name"],
                    "edges": [
                        {
                            "id": "greeting-default",
                            "target_node_id": "greeting",
                            "is_default": True
                        }
                    ]
                }
            ]
        }
        await self.flow_engine.load_flow_from_dict(default_flow)
    
    async def _create_calendar_event(
        self,
        name: str,
        date: str,
        time: str,
        duration_minutes: int = 30
    ) -> dict:
        """Create a calendar event"""
        try:
            if not self.calendar_service or not self.calendar_service.is_enabled():
                logger.warning("Calendar service not enabled")
                return {"success": False, "error": "Calendar not configured"}
            
            from datetime import date as date_type
            import dateutil.parser
            
            # Parse date and time
            appointment_date = dateutil.parser.parse(date).date()
            appointment_time = dateutil.parser.parse(time).time()
            
            # Create event
            result = await self.calendar_service.create_appointment(
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                summary=f"Appointment - {name}",
                description=f"Appointment scheduled via voice agent for {name}",
                duration_minutes=duration_minutes
            )
            
            if result:
                logger.info("Calendar event created", event_id=result.get('event_id'))
                return {"success": True, "event": result}
            else:
                return {"success": False, "error": "Failed to create event"}
                
        except Exception as e:
            logger.error("Calendar event creation failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _on_state_change(self, state, node_id: str):
        """Callback when flow state changes"""
        logger.info("State changed", node_id=node_id)
        await self._send_state_update()
    
    async def _on_response(self, state, response_text: str):
        """Callback when flow generates a response"""
        logger.debug("Flow response", text=response_text[:50] if response_text else "")
    
    async def _send_state_update(self):
        """Send state update to frontend via data message"""
        try:
            import json
            
            state_data = {
                "type": "state_update",
                "state": self.session_state.current_node_id,
                "slots": self.session_state.variables.get_all(),
                "is_complete": self.session_state.is_complete
            }
            
            await self.ctx.room.local_participant.publish_data(
                json.dumps(state_data).encode('utf-8'),
                reliable=True
            )
            logger.debug("State update sent", state=state_data["state"])
        except Exception as e:
            logger.warning("Failed to send state update", error=str(e))
    
    async def process_audio_stream(self, track: rtc.Track):
        """Process incoming audio stream with VAD"""
        logger.info("Processing audio stream with VAD", 
                   track_type=type(track).__name__)
        
        try:
            if isinstance(track, rtc.RemoteAudioTrack):
                audio_stream = rtc.AudioStream(track)
                
                async for audio_frame_event in audio_stream:
                    # Extract AudioFrame
                    audio_frame = self._extract_audio_frame(audio_frame_event)
                    if audio_frame is None:
                        continue
                    
                    # Process through VAD
                    await self._process_audio_frame_with_vad(audio_frame)
                    
        except Exception as e:
            logger.error("Error processing audio stream", error=str(e))
    
    def _extract_audio_frame(self, event) -> rtc.AudioFrame:
        """Extract AudioFrame from various event types"""
        if isinstance(event, rtc.AudioFrame):
            return event
        
        if hasattr(event, 'frame'):
            return event.frame
        if hasattr(event, 'audio_frame'):
            return event.audio_frame
        if hasattr(event, 'data') and hasattr(event, 'sample_rate'):
            return event
        
        return None
    
    async def _process_audio_frame_with_vad(self, audio_frame: rtc.AudioFrame):
        """Process a single audio frame through VAD pipeline"""
        
        # Check for barge-in (user speaking while agent is speaking)
        if self._is_speaking and self.flow_engine.flow.global_settings.allow_interruptions:
            # Quick energy check for potential interruption
            frame_data = audio_frame.data.tobytes() if hasattr(audio_frame.data, 'tobytes') else audio_frame.data
            if self._check_energy(frame_data, threshold=0.02):
                logger.info("Barge-in detected, stopping agent speech")
                await self._stop_speaking()
        
        # Process through VAD
        vad_result = await self.vad_processor.process_frame(audio_frame)
        
        if vad_result.is_speech_complete and vad_result.audio_data:
            # Speech complete - process the utterance
            await self._process_complete_utterance(
                vad_result.audio_data,
                audio_frame.sample_rate,
                audio_frame.num_channels
            )
    
    def _check_energy(self, frame_data: bytes, threshold: float = 0.01) -> bool:
        """Quick energy check for barge-in detection"""
        try:
            import numpy as np
            samples = np.frombuffer(frame_data, dtype=np.int16)
            energy = np.sqrt(np.mean(samples.astype(float) ** 2))
            normalized_energy = energy / 32768.0
            return normalized_energy > threshold
        except:
            return False
    
    async def _stop_speaking(self):
        """Stop current agent speech (for barge-in handling)"""
        self._is_speaking = False
        if self._current_speech_task:
            self._current_speech_task.cancel()
            self._current_speech_task = None
        
        # Reset VAD for new utterance
        if self.vad_processor:
            self.vad_processor.reset()
    
    async def _process_complete_utterance(
        self,
        audio_data: bytes,
        sample_rate: int,
        num_channels: int
    ):
        """Process a complete speech utterance"""
        try:
            logger.info("Processing complete utterance",
                       audio_size=len(audio_data),
                       sample_rate=sample_rate)
            
            # Step 1: Speech-to-Text
            user_text = await self.stt_service.transcribe(
                audio_data, sample_rate, num_channels
            )
            
            if not user_text or len(user_text.strip()) < 2:
                logger.debug("STT returned empty or short text, ignoring")
                return
            
            logger.info("User said", text=user_text[:100])
            
            # Send user transcription to frontend
            await self._send_transcription("user", user_text)
            
            # Step 2: Process through flow engine
            result = await self.flow_engine.process_input(
                self.session_state,
                user_text
            )
            
            # Step 3: Handle response
            if result.response_text:
                await self._send_transcription("agent", result.response_text)
                await self.say(result.response_text)
            
            # Update state in frontend
            await self._send_state_update()
            
            # Check if conversation ended
            if self.session_state.is_complete:
                logger.info("Conversation completed",
                           reason=self.session_state.end_reason)
            
        except Exception as e:
            logger.error("Error processing utterance", error=str(e))
            await self.say("I'm sorry, I encountered an error. Could you please repeat that?")
    
    async def _send_transcription(self, role: str, text: str):
        """Send transcription to frontend"""
        try:
            import json
            await self.ctx.room.local_participant.publish_data(
                json.dumps({
                    "type": f"{role}_transcription",
                    "text": text
                }).encode('utf-8'),
                reliable=True
            )
        except Exception as e:
            logger.warning("Failed to send transcription", error=str(e))
    
    async def say(self, text: str):
        """Synthesize and speak text with barge-in support"""
        try:
            logger.info("Agent speaking", text=text[:50])
            
            self._is_speaking = True
            
            # Synthesize audio
            audio_data = await self.tts_service.synthesize(text)
            if not audio_data or not self.audio_source:
                self._is_speaking = False
                return
            
            # Convert to audio frames and send
            import numpy as np
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            sample_rate = 24000
            chunk_size = sample_rate // 10  # 100ms chunks
            
            for i in range(0, len(audio_array), chunk_size):
                if not self._is_speaking:
                    logger.debug("Speech interrupted")
                    break
                
                chunk = audio_array[i:i + chunk_size]
                if len(chunk) == 0:
                    break
                
                audio_frame = rtc.AudioFrame(
                    data=chunk.tobytes(),
                    sample_rate=sample_rate,
                    num_channels=1,
                    samples_per_channel=len(chunk)
                )
                
                await self.audio_source.capture_frame(audio_frame)
            
            self._is_speaking = False
            
        except Exception as e:
            logger.error("Error synthesizing speech", error=str(e))
            self._is_speaking = False


async def entrypoint(ctx: JobContext):
    """Main entrypoint for Stage 3 agent"""
    logger.info("Stage 3 agent started", room=ctx.room.name)
    
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    
    logger.info("Agent connected to room",
                room=ctx.room.name,
                local_identity=ctx.room.local_participant.identity)
    
    try:
        agent = Stage3VoiceAgent(ctx)
        await agent.initialize()
        
        logger.info("Agent initialized, waiting for participants...")
        
        def on_track_subscribed(
            track: rtc.Track,
            publication: rtc.TrackPublication,
            participant: rtc.RemoteParticipant
        ):
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                is_not_agent = not participant.identity.startswith("agent")
                if is_not_agent:
                    logger.info("Audio track subscribed", participant=participant.identity)
                    asyncio.create_task(agent.process_audio_stream(track))
        
        ctx.room.on("track_subscribed", on_track_subscribed)
        
        # Process existing tracks
        for participant in ctx.room.remote_participants.values():
            for publication in participant.track_publications.values():
                if publication.track and publication.kind == rtc.TrackKind.KIND_AUDIO:
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
