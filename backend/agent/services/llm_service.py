from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import asyncio
import httpx
from openai import OpenAI
from utils.logger import logger
from config.settings import settings


class LLMService(ABC):
    @abstractmethod
    async def generate_response(self, user_text: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        pass


class OllamaLLMService(LLMService):
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        logger.info("Initialized Ollama LLM service", base_url=self.base_url, model=self.model)
    
    async def generate_response(self, user_text: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        try:
            messages = []
            
            if context:
                system_prompt = context.get("system_prompt", "You are a helpful voice assistant.")
                conversation_history = context.get("history", [])
                
                messages.append({"role": "system", "content": system_prompt})
                messages.extend(conversation_history)
            
            messages.append({"role": "user", "content": user_text})
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": settings.llm_temperature,
                            "num_predict": settings.llm_max_tokens,
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                text = result.get("message", {}).get("content", "")
                logger.info("Ollama LLM response generated", response_length=len(text))
                return text.strip()
        except httpx.TimeoutException:
            logger.error("Ollama LLM request timed out")
            return None
        except Exception as e:
            logger.error("Ollama LLM request failed", error=str(e))
            return None


class GroqLLMService(LLMService):
    def __init__(self):
        if not settings.groq_api_key:
            raise ValueError("Groq API key not configured")
        self.client = OpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = "llama-3.1-70b-versatile"
        logger.info("Initialized Groq LLM service", model=self.model)
    
    async def generate_response(self, user_text: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        try:
            messages = []
            
            if context:
                system_prompt = context.get("system_prompt", "You are a helpful voice assistant.")
                conversation_history = context.get("history", [])
                
                messages.append({"role": "system", "content": system_prompt})
                messages.extend(conversation_history)
            
            messages.append({"role": "user", "content": user_text})
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=settings.llm_temperature,
                    max_tokens=settings.llm_max_tokens,
                )
            )
            text = response.choices[0].message.content
            logger.info("Groq LLM response generated", response_length=len(text))
            return text.strip()
        except Exception as e:
            logger.error("Groq LLM request failed", error=str(e))
            return None


class GoogleLLMService(LLMService):
    def __init__(self):
        if not settings.google_api_key:
            raise ValueError("Google API key not configured")
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.google_api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            logger.info("Initialized Google Gemini LLM service", model="gemini-1.5-flash")
        except ImportError:
            raise ValueError("google-generativeai not installed. Run: pip install google-generativeai")
    
    async def generate_response(self, user_text: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        try:
            import google.generativeai as genai
            
            # Build prompt with system message and history
            prompt_parts = []
            
            if context:
                system_prompt = context.get("system_prompt", "You are a helpful voice assistant.")
                prompt_parts.append(system_prompt)
                
                conversation_history = context.get("history", [])
                for msg in conversation_history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "system":
                        prompt_parts.append(f"System: {content}")
                    elif role == "user":
                        prompt_parts.append(f"User: {content}")
                    elif role == "assistant":
                        prompt_parts.append(f"Assistant: {content}")
            
            prompt_parts.append(f"User: {user_text}")
            prompt = "\n".join(prompt_parts)
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=settings.llm_temperature,
                        max_output_tokens=settings.llm_max_tokens,
                    )
                )
            )
            text = response.text
            logger.info("Google Gemini LLM response generated", response_length=len(text))
            return text.strip()
        except Exception as e:
            logger.error("Google Gemini LLM request failed", error=str(e))
            return None


class OpenAILLMService(LLMService):
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"
        logger.info("Initialized OpenAI LLM service", model=self.model)
    
    async def generate_response(self, user_text: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        try:
            messages = []
            
            if context:
                system_prompt = context.get("system_prompt", "You are a helpful voice assistant.")
                conversation_history = context.get("history", [])
                
                messages.append({"role": "system", "content": system_prompt})
                messages.extend(conversation_history)
            
            messages.append({"role": "user", "content": user_text})
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=settings.llm_temperature,
                    max_tokens=settings.llm_max_tokens,
                )
            )
            text = response.choices[0].message.content
            logger.info("OpenAI LLM response generated", response_length=len(text))
            return text.strip()
        except Exception as e:
            logger.error("OpenAI LLM request failed", error=str(e))
            return None


def create_llm_service() -> LLMService:
    """
    Creates LLM service with fallback strategy:
    Primary: Google Gemini (if API key configured)
    Fallback: OpenAI, Ollama, Groq
    """
    providers = []
    
    # Google Gemini is primary (if API key configured)
    if settings.google_api_key:
        providers.append(("google", GoogleLLMService))
    
    # OpenAI is fallback (high quality, production-ready)
    if settings.openai_api_key:
        providers.append(("openai", OpenAILLMService))
    
    # Ollama is fallback (local, free, reliable)
    try:
        # Try to connect to Ollama to verify it's available
        providers.append(("ollama", OllamaLLMService))
    except Exception:
        logger.warning("Ollama not available for fallback")
    
    # Groq is optional (very fast, but requires API key)
    if settings.groq_api_key:
        providers.append(("groq", GroqLLMService))
    
    if not providers:
        raise ValueError("No LLM provider configured. Please set up at least Google, OpenAI, or Ollama.")
    
    # Use primary provider (Google if available, otherwise first available)
    primary_provider_name, primary_provider_class = providers[0]
    logger.info("Using primary LLM provider", provider=primary_provider_name, fallbacks=[p[0] for p in providers[1:]])
    
    try:
        return primary_provider_class()
    except Exception as e:
        logger.warning("Primary LLM provider failed, trying fallback", provider=primary_provider_name, error=str(e))
        # Try fallback providers in order
        for fallback_name, fallback_class in providers[1:]:
            try:
                logger.info("Trying fallback LLM provider", provider=fallback_name)
                return fallback_class()
            except Exception as fallback_error:
                logger.warning("Fallback provider also failed", provider=fallback_name, error=str(fallback_error))
                continue
        
        # All providers failed
        raise RuntimeError(f"All LLM providers failed. Primary: {primary_provider_name}, Fallbacks tried: {[p[0] for p in providers[1:]]}")

