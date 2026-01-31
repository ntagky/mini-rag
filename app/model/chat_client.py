import ollama
from enum import Enum
from openai import OpenAI
from typing import List, Union
from abc import ABC, abstractmethod
from typing import Literal
from typing_extensions import TypedDict
from dataclasses import dataclass
from openai.types.chat import (
    ChatCompletionUserMessageParam, ChatCompletionSystemMessageParam, ChatCompletionAssistantMessageParam
)
from ..config.logger import get_logger
from ..config.configer import (
    OLLAMA_BASE_URL, OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL, OPENAI_COMPLETION_MODEL, OLLAMA_CHAT_MODEL, OPENAI_EMBEDDING_DIMENSIONS
)

logger = get_logger("mini-rag." + __name__)

OpenAIMessage = Union[
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
]


@dataclass
class ChatContent(TypedDict, total=False):
    text: str
    image: bytes


@dataclass
class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: List[ChatContent]


class LlmModel(Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


DEFAULT_LLM_MODEL = LlmModel.OPENAI


class BaseLLM(ABC):
    @abstractmethod
    def chat(self, messages: List[ChatMessage]) -> str:
        pass

    @abstractmethod
    def chat_streaming(self, messages: List[ChatMessage]) -> str:
        pass


class ChatClient:
    def __init__(self, model: LlmModel, temperature: float = 0.0):
        if model == LlmModel.OPENAI:
            self.llm: BaseLLM = OpenAILLM(temperature=temperature)
        else:
            self.llm: BaseLLM = OllamaLLM(temperature=temperature)

    def chat(self, messages: List[ChatMessage], stream: bool = False) -> str:
        if stream:
            return self.llm.chat_streaming(messages)
        return self.llm.chat(messages)


class OllamaLLM(BaseLLM):
    def __init__(self, temperature: float = 0.0):
        self.model = OLLAMA_CHAT_MODEL
        self.base_url = OLLAMA_BASE_URL
        self.temperature = temperature

    def chat(self, messages: list[ChatMessage]) -> str:
        messages = self._to_ollama_messages(messages)

        response = ollama.chat(
            model=self.model,
            messages=messages,
            options={
                "temperature": self.temperature,
            }
        )

        return response["message"]["content"]

    def chat_streaming(self, messages: List[ChatMessage]):
        ollama_messages = self._to_ollama_messages(messages)

        stream = ollama.chat(
            model=self.model,
            messages=ollama_messages,
            options={
                "temperature": self.temperature,
            },
            stream=True,
        )

        full_response = []

        for chunk in stream:
            token = chunk["message"].get("content", "")
            if token:
                full_response.append(token)
                print(token, end="", flush=True)
        print()

        response = "".join(full_response)
        _log_response(self.model, response)
        return response

    @staticmethod
    def _to_ollama_messages(messages: list[ChatMessage]):
        ollama_messages = []

        for msg in messages:
            text_parts = []
            images = []

            for item in msg["content"]:
                if "text" in item:
                    text_parts.append(item["text"])
                elif "image" in item:
                    images.append(item["image"])

            ollama_msg = {
                "role": msg["role"],
                "content": "\n".join(text_parts) if text_parts else "",
            }

            if images:
                ollama_msg["images"] = images

            ollama_messages.append(ollama_msg)

        return ollama_messages


class OpenAILLM(BaseLLM):
    def __init__(self, temperature: float = 0.0):
        self.model = OPENAI_COMPLETION_MODEL

        self.temperature = temperature
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def chat(self, messages: List[ChatMessage]) -> str:
        openai_messages = self._to_openai_messages(messages)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            max_tokens=4096
        )

        return response.choices[0].message.content

    def chat_streaming(self, messages: List[ChatMessage]) -> str:
        openai_messages = self._to_openai_messages(messages)

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            max_tokens=4096,
            stream=True,
            stream_options={
                "include_usage": True
            }
        )

        full_response = []
        for chunk in stream:
            if len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    token = delta.content
                    full_response.append(token)
                    print(token, end="", flush=True)
        print()

        response = "".join(full_response)
        _log_response(self.model, response)
        return response

    @staticmethod
    def _to_openai_messages(messages: list[ChatMessage]) -> List[OpenAIMessage]:
        converted: List[OpenAIMessage] = []

        for msg in messages:
            content_list = []

            for item in msg.get("content", []):
                if "text" in item:
                    # Text block
                    content_list.append({"type": "text", "text": item["text"]})
                elif "image" in item:
                    content_list.append({"type": "image_url", "image_url": {"url": item["image"]}})

            # Only add message if there is content
            if content_list:
                converted.append({
                    "role": msg["role"],
                    "content": content_list
                })

        return converted

    def embed(self, texts: list[str]):
        response = self.client.embeddings.create(input=texts, model=OPENAI_EMBEDDING_MODEL, dimensions=OPENAI_EMBEDDING_DIMENSIONS)
        arr = [data.embedding for data in response.data]
        return arr


def _log_response(model: str, response: str):
    logger.debug(
        f"{model} completed response",
        extra={
            "extra": {
                "event": "llm_response",
                "response": response
            }
        }
    )
