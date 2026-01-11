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
    
    async def process_audio_stream(self, track: rtc.RemoteAudioTrack):
        """Process incoming audio stream from user"""
        logger.info("Processing audio stream from participant")
        
        async for audio_frame in track:
            try:
                self.audio_buffer.append(audio_frame)
                current_time = asyncio.get_event_loop().time()
                
                if self.last_audio_time is None:
                    self.last_audio_time = current_time
                
                # Process buffer every buffer_duration seconds
                if current_time - self.last_audio_time >= self.buffer_duration:
                    await self.process_audio_buffer()
                    self.audio_buffer = []
                    self.last_audio_time = current_time
                    
            except Exception as e:
                logger.error("Error processing audio frame", error=str(e))
    
    async def process_audio_buffer(self):
        """Process buffered audio frames: STT → LLM → TTS"""
        if not self.audio_buffer:
            return
        
        try:
            # Combine audio frames
            combined_audio = self.audio_buffer[0].data.tobytes()
            for frame in self.audio_buffer[1:]:
                combined_audio += frame.data.tobytes()
            
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
    logger.info("Stage 1 agent started", room=ctx.room.name)
    
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    
    try:
        agent = Stage1VoiceAgent(ctx)
        await agent.initialize()
        
        logger.info("Agent initialized, waiting for participants...")
        
        async def on_track_subscribed(
            track: rtc.Track, 
            publication: rtc.TrackPublication, 
            participant: rtc.RemoteParticipant
        ):
            if track.kind == rtc.TrackKind.KIND_AUDIO and participant.identity != "agent":
                logger.info("Audio track subscribed", participant=participant.identity)
                if isinstance(track, rtc.RemoteAudioTrack):
                    asyncio.create_task(agent.process_audio_stream(track))
        
        ctx.room.on("track_subscribed", on_track_subscribed)
        
        # Handle existing tracks
        for participant in ctx.room.remote_participants.values():
            for publication in participant.track_publications.values():
                if publication.track and publication.kind == rtc.TrackKind.KIND_AUDIO:
                    if isinstance(publication.track, rtc.RemoteAudioTrack):
                        asyncio.create_task(agent.process_audio_stream(publication.track))
        
        await ctx.wait_until_disconnected()
        logger.info("Agent disconnected")
        
    except Exception as e:
        logger.error("Agent initialization failed", error=str(e))
        raise


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="appointment-scheduler"
    ))
