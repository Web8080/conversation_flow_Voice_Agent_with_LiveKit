"""
Example Unit Test Structure
This demonstrates the testing patterns for the voice agent
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from agent.services.stt_service import OpenAISTTService
from agent.services.llm_service import OllamaLLMService
from agent.state_machine.state_machine import StateMachine
from agent.state_machine.context import ConversationContext, Turn


class TestSTTService:
    """Unit tests for STT Service"""
    
    @pytest.fixture
    def stt_service(self):
        """Create STT service instance"""
        with patch('agent.services.stt_service.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            service = OpenAISTTService()
            return service
    
    @pytest.mark.asyncio
    async def test_transcribe_success(self, stt_service):
        """Test successful transcription"""
        audio_data = b"fake audio data"
        expected_text = "Hello, this is a test"
        
        with patch.object(stt_service.client.audio.transcriptions, 'create') as mock_create:
            mock_create.return_value = expected_text
            
            result = await stt_service.transcribe(audio_data)
            
            assert result == expected_text
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transcribe_failure(self, stt_service):
        """Test transcription failure handling"""
        audio_data = b"fake audio data"
        
        with patch.object(stt_service.client.audio.transcriptions, 'create') as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            result = await stt_service.transcribe(audio_data)
            
            assert result is None


class TestStateMachine:
    """Unit tests for State Machine"""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service"""
        service = Mock()
        service.generate_response = AsyncMock(return_value="John Doe")
        return service
    
    @pytest.fixture
    def state_machine(self, mock_llm_service):
        """Create state machine instance"""
        return StateMachine(mock_llm_service)
    
    @pytest.fixture
    def context(self):
        """Create conversation context"""
        return ConversationContext(session_id="test-session")
    
    @pytest.mark.asyncio
    async def test_greeting_state_transition(self, state_machine, context):
        """Test greeting state to collect date transition"""
        state_machine.reset_to_initial_state(context)
        
        response = await state_machine.process_user_input("My name is John", context)
        
        assert response.next_state == "collect_date"
        assert "John" in response.response_text
        assert context.get_slot("name") == "John"
    
    @pytest.mark.asyncio
    async def test_retry_logic(self, state_machine, context):
        """Test retry mechanism on unclear input"""
        state_machine.transition_to("collect_date", context)
        
        # Simulate unclear input multiple times
        for _ in range(2):
            response = await state_machine.process_user_input("I don't know", context)
            assert response.next_state == "collect_date"
        
        # Third retry should trigger fallback
        response = await state_machine.process_user_input("Still unclear", context)
        assert response.next_state == "fallback"


class TestTokenService:
    """Unit tests for Token Service"""
    
    @pytest.fixture
    def token_service(self):
        """Create token service instance"""
        with patch('agent.auth.token_service.settings') as mock_settings:
            mock_settings.livekit_api_key = "test-key"
            mock_settings.livekit_api_secret = "test-secret"
            from auth.token_service import TokenService
            return TokenService()
    
    def test_validate_room_name_valid(self, token_service):
        """Test valid room name validation"""
        assert token_service._validate_room_name("valid-room-123") == True
        assert token_service._validate_room_name("test_room") == True
    
    def test_validate_room_name_invalid(self, token_service):
        """Test invalid room name validation"""
        assert token_service._validate_room_name("") == False
        assert token_service._validate_room_name("room with spaces") == False
        assert token_service._validate_room_name("admin") == False  # Reserved
        assert token_service._validate_room_name("A" * 101) == False  # Too long
    
    def test_generate_token(self, token_service):
        """Test token generation"""
        token = token_service.generate_room_token(
            room_name="test-room",
            user_id="user-123"
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0


# Pytest configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


