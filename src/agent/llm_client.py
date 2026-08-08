from abc import ABC, abstractmethod
from typing import TypeVar

import anthropic
from pydantic import BaseModel

from agent.config import settings

T = TypeVar("T", bound=BaseModel)


class LLMClient(ABC):
    @abstractmethod
    def complete(self, system: str, prompt: str) -> str:
        """Return a raw text completion."""

    @abstractmethod
    def complete_structured(self, system: str, prompt: str, schema: type[T]) -> T:
        """Return a validated instance of `schema`."""


def _pydantic_to_tool(schema: type[BaseModel], tool_name: str = "return_result") -> dict:
    return {
        "name": tool_name,
        "description": f"Return a {schema.__name__} object matching the given schema.",
        "input_schema": schema.model_json_schema(),
    }


class AnthropicLLMClient(LLMClient):
    def __init__(self, model: str | None = None, max_tokens: int = 2048):
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = model or settings.anthropic_model
        self._max_tokens = max_tokens

    def complete(self, system: str, prompt: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")

    def complete_structured(self, system: str, prompt: str, schema: type[T]) -> T:
        tool = _pydantic_to_tool(schema)
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]},
        )
        for block in response.content:
            if block.type == "tool_use":
                return schema.model_validate(block.input)
        raise RuntimeError("Model did not return a tool_use block")


class FakeLLMClient(LLMClient):
    """Test double: returns pre-queued responses instead of calling any API."""

    def __init__(self, text_responses=None, structured_responses=None):
        self._text_responses = list(text_responses or [])
        self._structured_responses = list(structured_responses or [])
        self.calls: list[tuple] = []

    def complete(self, system: str, prompt: str) -> str:
        self.calls.append(("complete", system, prompt))
        if not self._text_responses:
            raise AssertionError("FakeLLMClient: no more text responses queued")
        return self._text_responses.pop(0)

    def complete_structured(self, system: str, prompt: str, schema: type[T]) -> T:
        self.calls.append(("complete_structured", system, prompt, schema))
        if not self._structured_responses:
            raise AssertionError("FakeLLMClient: no more structured responses queued")
        result = self._structured_responses.pop(0)
        if not isinstance(result, schema):
            raise TypeError(f"Queued response {result!r} is not an instance of {schema}")
        return result
