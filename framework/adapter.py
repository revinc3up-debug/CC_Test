"""
LLM provider adapter layer.

Provides a pluggable interface for sending prompts to different LLM providers.
The framework generates prompts; adapters handle the actual API calls.
"""

import os
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    """Standard response from an LLM provider."""
    content: str
    role: str = "assistant"
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    raw: Any = None


class LLMAdapter(ABC):
    """Abstract base class for LLM provider adapters."""

    @abstractmethod
    def send(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        """Send a prompt to the LLM and return the response."""
        ...

    @abstractmethod
    def name(self) -> str:
        """Return the adapter name."""
        ...


class AnthropicAdapter(LLMAdapter):
    """
    Adapter for the Anthropic Claude API.

    Requires: pip install anthropic
    Set ANTHROPIC_API_KEY environment variable.
    """

    def __init__(self, model: str = "claude-sonnet-4-20250514", max_tokens: int = 4096):
        self.model = model
        self.max_tokens = max_tokens
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError:
                raise ImportError(
                    "anthropic package required. Install with: pip install anthropic"
                )
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def send(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        client = self._get_client()
        messages = [{"role": "user", "content": prompt}]

        params: dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "messages": messages,
        }
        if system_prompt:
            params["system"] = system_prompt

        response = client.messages.create(**params)

        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            raw=response,
        )

    def name(self) -> str:
        return f"anthropic:{self.model}"


class OpenAIAdapter(LLMAdapter):
    """
    Adapter for the OpenAI API (GPT models).

    Requires: pip install openai
    Set OPENAI_API_KEY environment variable.
    """

    def __init__(self, model: str = "gpt-4o", max_tokens: int = 4096):
        self.model = model
        self.max_tokens = max_tokens
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import openai
            except ImportError:
                raise ImportError(
                    "openai package required. Install with: pip install openai"
                )
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self._client = openai.OpenAI(api_key=api_key)
        return self._client

    def send(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        client = self._get_client()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=kwargs.get("model", self.model),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            messages=messages,
        )

        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model or self.model,
            usage={
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            raw=response,
        )

    def name(self) -> str:
        return f"openai:{self.model}"


class FileAdapter(LLMAdapter):
    """
    Adapter that saves prompts to files instead of calling an LLM.
    Useful for debugging, reviewing prompts, or offline workflows.
    """

    def __init__(self, output_dir: str = ".prompts"):
        self.output_dir = output_dir
        self._counter = 0
        os.makedirs(output_dir, exist_ok=True)

    def send(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        self._counter += 1
        filename = f"{self._counter:03d}_prompt.md"
        filepath = os.path.join(self.output_dir, filename)

        content_parts = []
        if system_prompt:
            content_parts.append(f"<!-- SYSTEM PROMPT -->\n{system_prompt}\n")
        content_parts.append(f"<!-- USER PROMPT -->\n{prompt}")

        full_content = "\n---\n\n".join(content_parts)

        with open(filepath, "w") as f:
            f.write(full_content)

        return LLMResponse(
            content=f"[Prompt saved to {filepath}]",
            model="file",
        )

    def name(self) -> str:
        return f"file:{self.output_dir}"


def create_adapter(provider: str = "anthropic", **kwargs) -> LLMAdapter:
    """Factory function to create an LLM adapter by provider name."""
    adapters = {
        "anthropic": AnthropicAdapter,
        "openai": OpenAIAdapter,
        "file": FileAdapter,
    }
    if provider not in adapters:
        available = ", ".join(adapters.keys())
        raise ValueError(f"Unknown provider '{provider}'. Available: {available}")
    return adapters[provider](**kwargs)
