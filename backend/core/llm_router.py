"""
DeepClaw Multi-LLM Router
Gère le routage dynamique entre différents fournisseurs LLM
"""
import os
import time
import logging
from typing import Dict, Any, Optional, List, AsyncIterator
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseLLM(ABC):
    """Interface abstraite pour tous les LLM"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def provider(self) -> str:
        pass


class OpenAILLM(BaseLLM):
    """OpenAI LLM Wrapper"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o", temperature: float = 0.3):
        import openai
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            **kwargs
        )
        return response.choices[0].message.content or ""
    
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        async for chunk in self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            stream=True,
            **kwargs
        ):
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    @property
    def model_name(self) -> str:
        return self.model
    
    @property
    def provider(self) -> str:
        return "openai"


class AnthropicLLM(BaseLLM):
    """Anthropic LLM Wrapper"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", temperature: float = 0.3):
        import anthropic
        self.client = anthropic.AsyncClient(api_key=api_key)
        self.model = model
        self.temperature = temperature
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        async for chunk in self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **kwargs
        ):
            if chunk.type == "content_delta" and chunk.text:
                yield chunk.text
    
    @property
    def model_name(self) -> str:
        return self.model
    
    @property
    def provider(self) -> str:
        return "anthropic"


class GoogleLLM(BaseLLM):
    """Google Gemini LLM Wrapper"""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro-latest", temperature: float = 0.3):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self._model_name = model
        self.client = genai.GenerativeModel(model)
        self.temperature = temperature
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.generate_content_async(prompt, generation_config={
            "temperature": self.temperature,
            **kwargs
        })
        return response.text
    
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        response = await self.client.generate_content_stream(prompt, generation_config={
            "temperature": self.temperature,
            **kwargs
        })
        async for chunk in response:
            if chunk.text:
                yield chunk.text
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    @property
    def provider(self) -> str:
        return "google"


class LLMRouter:
    """Router dynamique qui sélectionne le meilleur LLM pour la tâche"""
    
    def __init__(self, settings_instance=None):
        if settings_instance is None:
            from ..config import settings
            self.settings = settings
        else:
            self.settings = settings_instance
        self._llms: Dict[str, BaseLLM] = {}
        self._load_llms()
    
    def _load_llms(self):
        """Charge les LLM disponibles selon les clés API"""
        # OpenAI
        if getattr(self.settings, "openai_api_key", None):
            try:
                self._llms["openai"] = OpenAILLM(
                    api_key=self.settings.openai_api_key,
                    model=self.settings.openai_model,
                    temperature=self.settings.openai_temperature
                )
                logger.info("OpenAI LLM loaded")
            except Exception as e:
                logger.warning(f"Impossible d'initialiser OpenAI LLM: {e}")
        
        # Anthropic
        if getattr(self.settings, "anthropic_api_key", None):
            try:
                self._llms["anthropic"] = AnthropicLLM(
                    api_key=self.settings.anthropic_api_key,
                    model=self.settings.anthropic_model,
                    temperature=self.settings.anthropic_temperature
                )
                logger.info("Anthropic LLM loaded")
            except Exception as e:
                logger.warning(f"Impossible d'initialiser Anthropic LLM: {e}")
        
        # Google
        if getattr(self.settings, "google_api_key", None):
            try:
                self._llms["google"] = GoogleLLM(
                    api_key=self.settings.google_api_key,
                    model=self.settings.google_model,
                    temperature=self.settings.google_temperature
                )
                logger.info("Google Gemini LLM loaded")
            except Exception as e:
                logger.warning(f"Impossible d'initialiser Google Gemini LLM: {e}")
    
    def get_llm(self, provider: str = None) -> Optional[BaseLLM]:
        """Obtient un LLM par provider"""
        if provider:
            return self._llms.get(provider)
        
        # Choisir le meilleur LLM disponible
        for name, llm in self._llms.items():
            return llm
        
        return None
    
    async def generate(self, prompt: str, provider: str = None, **kwargs) -> str:
        """Générer du texte avec le LLM spécifié ou le meilleur disponible"""
        llm = self.get_llm(provider)
        if llm is None:
            raise ValueError("No LLM available. Check your API keys.")
        return await llm.generate(prompt, **kwargs)
    
    async def stream_generate(self, prompt: str, provider: str = None, **kwargs) -> AsyncIterator[str]:
        """Générer du texte en streaming"""
        llm = self.get_llm(provider)
        if llm is None:
            raise ValueError("No LLM available. Check your API keys.")
        async for chunk in llm.stream_generate(prompt, **kwargs):
            yield chunk
    
    def get_available_providers(self) -> List[str]:
        """Retourne la liste des providers disponibles"""
        return list(self._llms.keys())


_router_instance: Optional[LLMRouter] = None

def get_llm_router() -> LLMRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = LLMRouter()
    return _router_instance
