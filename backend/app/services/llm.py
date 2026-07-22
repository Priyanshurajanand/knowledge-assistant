from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Optional
from openai import AsyncOpenAI
import google.generativeai as genai
from anthropic import AsyncAnthropic
from groq import AsyncGroq
from app.core.config import settings

class BaseLLM(ABC):
    """Base interface for all LLM providers (OpenAI, Gemini, Anthropic, Groq)."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> str:
        """Standard text generation (blocking/non-streaming)."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Streaming text generation using Server-Sent Events (SSE)."""
        pass


class OpenAIProvider(BaseLLM):
    """
    OpenAI integration provider.
    - API Key: Loaded from OPENAI_API_KEY in the .env file.
    - Default Model: 'gpt-4o' (Used if no custom model is chosen in the chat selection dropdown).
    """
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.default_model = "gpt-4o"  # <-- UPDATE THIS to change default OpenAI model

    async def generate(
        self,
        prompt: str,
        system_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> str:
        """Sends a standard non-streaming text generation request to OpenAI."""
        model_name = model or self.default_model
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=False
        )
        return response.choices[0].message.content or ""

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Streams text generation chunks from OpenAI as they arrive (using Server-Sent Events)."""
        model_name = model or self.default_model
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=True
        )
        async for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


class GeminiProvider(BaseLLM):
    """
    Google Gemini integration provider.
    - API Key: Loaded from GEMINI_API_KEY in the .env file.
    - Default Model: 'gemini-1.5-flash' (Fast and cost-effective).
    """
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.default_model = "gemini-1.5-flash"  # <-- UPDATE THIS to change default Gemini model

    def _prepare_contents(
        self, 
        prompt: str, 
        history: Optional[List[Dict[str, str]]] = None
    ) -> List[Any]:
        """Reformats chat history into the structured list format expected by the Google GenAI SDK."""
        contents = []
        if history:
            for msg in history:
                role = "model" if msg["role"] == "assistant" else "user"
                contents.append(
                    {"role": role, "parts": [msg["content"]]}
                )
        contents.append({"role": "user", "parts": [prompt]})
        return contents

    async def generate(
        self,
        prompt: str,
        system_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> str:
        """Sends a standard text generation request to Gemini."""
        model_name = model or self.default_model
        gemini_model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt
        )
        contents = self._prepare_contents(prompt, history)
        
        response = await gemini_model.generate_content_async(contents)
        return response.text

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Streams content segments asynchronously from Gemini API."""
        model_name = model or self.default_model
        gemini_model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt
        )
        contents = self._prepare_contents(prompt, history)
        
        response = await gemini_model.generate_content_async(contents, stream=True)
        async for chunk in response:
            if chunk.text:
                yield chunk.text


class ClaudeProvider(BaseLLM):
    """
    Anthropic Claude integration provider.
    - API Key: Loaded from ANTHROPIC_API_KEY in the .env file.
    - Default Model: 'claude-3-5-sonnet-20240620' (High intelligence and reasoning).
    """
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.default_model = "claude-3-5-sonnet-20240620"  # <-- UPDATE THIS to change default Claude model

    def _prepare_messages(
        self, 
        prompt: str, 
        history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, Any]]:
        """Maps default 'assistant'/'user' roles into standard Anthropic messages array."""
        messages = []
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})
        return messages

    async def generate(
        self,
        prompt: str,
        system_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> str:
        """Issues chat message generation request to Anthropic Claude."""
        model_name = model or self.default_model
        messages = self._prepare_messages(prompt, history)
        
        response = await self.client.messages.create(
            model=model_name,
            max_tokens=4096,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text if response.content else ""

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Streams word segments from Claude's text_stream generator."""
        model_name = model or self.default_model
        messages = self._prepare_messages(prompt, history)
        
        async with self.client.messages.stream(
            model=model_name,
            max_tokens=4096,
            system=system_prompt,
            messages=messages
        ) as stream:
            async for text in stream.text_stream:
                yield text


class GroqProvider(BaseLLM):
    """
    Groq integration provider (Default).
    - API Key: Loaded from GROQ_API_KEY in the .env file.
    - Default Model: 'llama-3.3-70b-versatile' (Ultra fast open-weights LLM).
    """
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.default_model = "llama-3.3-70b-versatile"  # <-- UPDATE THIS to change default Groq model

    async def generate(
        self,
        prompt: str,
        system_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> str:
        """Sends non-streaming request using Groq's high-speed LPU pipeline."""
        model_name = model or self.default_model
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=False
        )
        return response.choices[0].message.content or ""

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Streams tokens dynamically from Groq completions."""
        model_name = model or self.default_model
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=True
        )
        async for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


class LLMFactory:
    """
    Factory pattern to resolve and instantiate LLM providers at runtime.
    - If you add a new model provider (e.g. Cohere or local Ollama), implement its provider class
      inheriting from `BaseLLM` and add the matching branch mapping below.
    """
    @staticmethod
    def get_provider(provider_name: str) -> BaseLLM:
        name = provider_name.lower()
        if name == "openai":
            return OpenAIProvider()
        elif name == "gemini":
            return GeminiProvider()
        elif name == "claude" or name == "anthropic":
            return ClaudeProvider()
        elif name == "groq":
            return GroqProvider()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
