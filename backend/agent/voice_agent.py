import asyncio
import io
from typing import Optional, Dict
from livekit import rtc, agents
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.agents import llm
from livekit.agents.pipeline import VoicePipelineAgent, VoicePipelineAgentState
from livekit.agents.voice_assistant import VoiceAssistant

from agent.services.stt_service import create_stt_service, STTService
from agent.services.llm_service import create_llm_service, LLMService
from agent.services.tts_service import create_tts_service, TTSService
from agent.state_machine.state_machine import StateMachine
from agent.state_machine.context import ConversationContext
from config.settings import settings
from utils.logger import logger


class VoiceAgent:
    def __init__(self):
        self.stt_service: Optional[STTService] = None
        self.llm_service: Optional[LLMService] = None
        self.tts_service: Optional[TTSService] = None
        self.state_machine: Optional[StateMachine] = None
        self.context: Optional[ConversationContext] = None
        logger.info("VoiceAgent initialized")
    
    async def initialize(self):
        try:
            self.stt_service = create_stt_service()
            self.llm_service = create_llm_service()
            self.tts_service = create_tts_service()
            self.state_machine = StateMachine(self.llm_service)
            logger.info("VoiceAgent services initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize VoiceAgent services", error=str(e))
            raise
    
    async def process_audio_frame(self, audio_frame: rtc.AudioFrame) -> Optional[bytes]:
        try:
            audio_data = audio_frame.data.tobytes()
            
            text = await self.stt_service.transcribe(audio_data)
            if not text:
                logger.warning("STT returned empty text")
                return None
            
            logger.info("User input transcribed", text=text[:100])
            
            if not self.context:
                session_id = f"session_{id(self)}"
                self.context = ConversationContext(session_id=session_id)
                self.state_machine.reset_to_initial_state(self.context)
            
            if not self.context.history:
                initial_prompt = self.state_machine.get_initial_prompt(self.context)
                self.context.add_turn(self.context.__class__.Turn(role="agent", text=initial_prompt))
                response_text = initial_prompt
            else:
                response = await self.state_machine.process_user_input(text, self.context)
                response_text = response.response_text
                
                if not response.should_continue:
                    logger.info("Conversation ended", state=self.state_machine.current_state_name)
            
            if not response_text:
                response_text = "I'm sorry, I didn't understand. Could you repeat that?"
            
            audio_response = await self.tts_service.synthesize(response_text)
            if audio_response:
                logger.info("TTS synthesis completed", response_length=len(response_text))
                return audio_response
            
            return None
        except Exception as e:
            logger.error("Error processing audio frame", error=str(e))
            return None


async def entrypoint(ctx: JobContext):
    logger.info("Agent job started", room=ctx.room.name)
    
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    agent = VoiceAgent()
    await agent.initialize()
    
    participant = None
    for participant in ctx.room.remote_participants.values():
        if participant.identity != "agent":
            break
    
    if not participant:
        logger.warning("No remote participants found")
        return
    
    audio_source = rtc.AudioSource(24000, 1)
    track = rtc.LocalAudioTrack.create_audio_track("agent-voice", audio_source)
    options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
    await ctx.room.local_participant.publish_track(track, options)
    
    async def on_audio_frame(frame: rtc.AudioFrame):
        try:
            response_audio = await agent.process_audio_frame(frame)
            if response_audio:
                audio_buffer = io.BytesIO(response_audio)
                audio_frame_data = rtc.AudioFrame(
                    data=audio_buffer.read(),
                    sample_rate=24000,
                    num_channels=1,
                    samples_per_channel=len(response_audio) // 2
                )
                await audio_source.capture_frame(audio_frame_data)
        except Exception as e:
            logger.error("Error handling audio frame", error=str(e))
    
    participant.on("track_subscribed", lambda track, *_args: asyncio.create_task(
        handle_track_subscribed(track, on_audio_frame)
    ) if track.kind == rtc.TrackKind.KIND_AUDIO else None)
    
    async def handle_track_subscribed(track: rtc.Track, callback):
        async for frame in track:
            if isinstance(frame, rtc.AudioFrame):
                await callback(frame)
    
    logger.info("Agent ready and listening")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))


