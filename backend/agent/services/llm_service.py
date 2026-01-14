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
        self.api_key = settings.google_api_key
        # Use REST API directly to avoid deprecated package issues
        # Use v1beta as it supports more models
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
        # Discover available models by calling ListModels API
        self.models_to_try = self._discover_available_models()
        
        if not self.models_to_try:
            # Fallback to common model names if discovery fails
            logger.warning("Failed to discover models, using fallback list")
            self.models_to_try = [
                "gemini-pro",
                "gemini-1.5-flash",
                "gemini-1.5-pro"
            ]
        
        logger.info("Initialized Google Gemini LLM service (using REST API)", 
                   models=self.models_to_try)
    
    def _discover_available_models(self) -> list:
        """Call ListModels API to discover available models"""
        try:
            import asyncio
            import httpx
            
            url = f"{self.base_url}/models"
            headers = {"Content-Type": "application/json"}
            
            # Use sync call in __init__ (we'll make it async if needed)
            import httpx as sync_httpx
            with sync_httpx.Client(timeout=10.0) as client:
                response = client.get(
                    url,
                    headers=headers,
                    params={"key": self.api_key}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    if "models" in data:
                        for model in data["models"]:
                            name = model.get("name", "")
                            # Extract model name (format: "models/gemini-pro")
                            if name.startswith("models/"):
                                model_name = name.replace("models/", "")
                                # Only include models that support generateContent
                                supported_methods = model.get("supportedGenerationMethods", [])
                                if "generateContent" in supported_methods:
                                    models.append(model_name)
                    
                    logger.info("Discovered available Google Gemini models", 
                               models=models, 
                               total=len(models))
                    return models
                else:
                    logger.warning("Failed to list models", 
                                 status_code=response.status_code,
                                 error=response.text[:200])
                    return []
        except Exception as e:
            logger.warning("Error discovering models", error=str(e))
            return []
    
    async def generate_response(self, user_text: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        try:
            import json
            
            # Build messages for chat format (REST API v1beta uses chat format)
            messages = []
            
            if context:
                system_prompt = context.get("system_prompt", "You are a helpful voice assistant.")
                # Add system instruction as first message
                messages.append({
                    "role": "user",
                    "parts": [{"text": system_prompt}]
                })
                messages.append({
                    "role": "model",
                    "parts": [{"text": "I understand. I'm ready to help."}]
                })
                
                conversation_history = context.get("history", [])
                for msg in conversation_history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        messages.append({
                            "role": "user",
                            "parts": [{"text": content}]
                        })
                    elif role == "assistant":
                        messages.append({
                            "role": "model",
                            "parts": [{"text": content}]
                        })
            
            # Add current user message
            messages.append({
                "role": "user",
                "parts": [{"text": user_text}]
            })
            
            logger.info("DEBUG: Calling Google Gemini REST API",
                       models_to_try=self.models_to_try,
                       prompt_length=len(user_text),
                       user_text=user_text[:100],
                       messages_count=len(messages),
                       has_context=context is not None,
                       hypothesis="LLM_GOOGLE_CALL")
            
            # Try each model in order
            last_error = None
            response_data = None
            
            for model_name in self.models_to_try:
                try:
                    logger.info("DEBUG: Trying Google Gemini model via REST API",
                               model=model_name,
                               hypothesis="LLM_GOOGLE_MODEL_TRY")
                    
                    # Use the correct API endpoint format
                    # For REST API, model names should be in format: models/gemini-1.5-flash
                    url = f"{self.base_url}/models/{model_name}:generateContent"
                    payload = {
                        "contents": messages,
                        "generationConfig": {
                            "temperature": settings.llm_temperature,
                            "maxOutputTokens": settings.llm_max_tokens,
                        }
                    }
                    
                    headers = {
                        "Content-Type": "application/json",
                    }
                    
                    # Use httpx for async HTTP requests
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(
                            url,
                            json=payload,
                            headers=headers,
                            params={"key": self.api_key}
                        )
                        
                        logger.info("DEBUG: Google Gemini REST API response",
                                   model=model_name,
                                   status_code=response.status_code,
                                   hypothesis="LLM_GOOGLE_RESPONSE")
                        
                        if response.status_code == 200:
                            response_data = response.json()
                            logger.info("DEBUG: Google Gemini REST API success",
                                       model=model_name,
                                       hypothesis="LLM_GOOGLE_SUCCESS")
                            break
                        else:
                            error_text = response.text[:200]
                            logger.warning("DEBUG: Google Gemini REST API failed",
                                         model=model_name,
                                         status_code=response.status_code,
                                         error=error_text,
                                         hypothesis="LLM_GOOGLE_MODEL_FAILED")
                            last_error = Exception(f"HTTP {response.status_code}: {error_text}")
                            continue
                            
                except Exception as model_error:
                    logger.warning("DEBUG: Google Gemini model request failed",
                                 model=model_name,
                                 error=str(model_error),
                                 error_type=type(model_error).__name__,
                                 hypothesis="LLM_GOOGLE_MODEL_FAILED")
                    last_error = model_error
                    continue
            
            if response_data is None:
                raise last_error if last_error else Exception("All Google Gemini models failed")
            
            # Extract text from response
            # Response format: {"candidates": [{"content": {"parts": [{"text": "..."}]}}]}
            if "candidates" in response_data and len(response_data["candidates"]) > 0:
                candidate = response_data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        text = parts[0]["text"]
                        
                        logger.info("DEBUG: Google Gemini text extracted",
                                   text=text[:100] if text else "None",
                                   text_length=len(text) if text else 0,
                                   hypothesis="LLM_GOOGLE_SUCCESS")
                        
                        if not text or len(text.strip()) == 0:
                            logger.warning("DEBUG: Google Gemini returned empty text",
                                         hypothesis="LLM_GOOGLE_EMPTY")
                            return None
                        
                        logger.info("Google Gemini LLM response generated", response_length=len(text))
                        return text.strip()
            
            logger.error("DEBUG: Google Gemini response has unexpected format",
                       response_data_keys=list(response_data.keys()) if isinstance(response_data, dict) else None,
                       hypothesis="LLM_GOOGLE_FORMAT_ERROR")
            return None
            
        except Exception as e:
            logger.error("DEBUG: Google Gemini LLM request failed with exception",
                        error=str(e),
                        error_type=type(e).__name__,
                        error_traceback=str(e.__traceback__) if hasattr(e, '__traceback__') else None,
                        hypothesis="LLM_GOOGLE_ERROR")
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


class LLMFallbackService(LLMService):
    """Wrapper service that tries multiple LLM providers with runtime fallback"""
    def __init__(self, primary: LLMService, fallbacks: List[LLMService]):
        self.primary = primary
        self.fallbacks = fallbacks
        logger.info("Initialized LLM fallback service", 
                   primary=type(primary).__name__,
                   fallbacks=[type(f).__name__ for f in fallbacks])
    
    async def generate_response(self, user_text: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        # Try primary first
        try:
            logger.info("DEBUG: Trying primary LLM", provider=type(self.primary).__name__, hypothesis="LLM_FALLBACK_PRIMARY")
            result = await self.primary.generate_response(user_text, context)
            if result:
                logger.info("DEBUG: Primary LLM succeeded", provider=type(self.primary).__name__, hypothesis="LLM_FALLBACK_SUCCESS")
                return result
            else:
                logger.warning("DEBUG: Primary LLM returned None, trying fallback", provider=type(self.primary).__name__, hypothesis="LLM_FALLBACK_NONE")
        except Exception as e:
            logger.warning("DEBUG: Primary LLM failed, trying fallback",
                         provider=type(self.primary).__name__,
                         error=str(e),
                         error_type=type(e).__name__,
                         hypothesis="LLM_FALLBACK_ERROR")
        
        # Try fallbacks in order
        for fallback in self.fallbacks:
            try:
                logger.info("DEBUG: Trying fallback LLM", provider=type(fallback).__name__, hypothesis="LLM_FALLBACK_TRY")
                result = await fallback.generate_response(user_text, context)
                if result:
                    logger.info("DEBUG: Fallback LLM succeeded", provider=type(fallback).__name__, hypothesis="LLM_FALLBACK_SUCCESS")
                    return result
                else:
                    logger.warning("DEBUG: Fallback LLM returned None", provider=type(fallback).__name__, hypothesis="LLM_FALLBACK_NONE")
            except Exception as e:
                logger.warning("DEBUG: Fallback LLM failed",
                             provider=type(fallback).__name__,
                             error=str(e),
                             error_type=type(e).__name__,
                             hypothesis="LLM_FALLBACK_ERROR")
                continue
        
        logger.error("DEBUG: All LLM providers failed", hypothesis="LLM_FALLBACK_ALL_FAILED")
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
        try:
            providers.append(("google", GoogleLLMService()))
        except Exception as e:
            logger.warning("Google LLM not available", error=str(e))
    
    # OpenAI is fallback (high quality, production-ready)
    if settings.openai_api_key:
        try:
            providers.append(("openai", OpenAILLMService()))
        except Exception as e:
            logger.warning("OpenAI LLM not available", error=str(e))
    
    # Ollama is fallback (local, free, reliable)
    try:
        providers.append(("ollama", OllamaLLMService()))
    except Exception as e:
        logger.warning("Ollama not available", error=str(e))
    
    # Groq is optional (very fast, but requires API key)
    if settings.groq_api_key:
        try:
            providers.append(("groq", GroqLLMService()))
        except Exception as e:
            logger.warning("Groq LLM not available", error=str(e))
    
    if not providers:
        raise ValueError("No LLM provider configured. Please set up at least Google, OpenAI, or Ollama.")
    
    # If only one provider, return it directly
    if len(providers) == 1:
        logger.info("Using LLM provider", provider=providers[0][0])
        return providers[0][1]
    
    # Multiple providers: use first as primary, rest as fallbacks
    primary = providers[0][1]
    fallbacks = [p[1] for p in providers[1:]]
    logger.info("Using LLM provider with runtime fallback", 
               primary=providers[0][0],
               fallbacks=[p[0] for p in providers[1:]])
    return LLMFallbackService(primary, fallbacks)

