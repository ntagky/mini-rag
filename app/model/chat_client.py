import os
import ollama
from enum import Enum
from openai import OpenAI
from typing import List, Union, NotRequired
from abc import ABC, abstractmethod
from typing import Literal, cast
from typing_extensions import TypedDict
from dataclasses import dataclass
from openai.types.chat import (
    ChatCompletionUserMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartImageParam,
)
from app.config.logger import get_logger
from app.config.configer import (
    OPENAI_EMBEDDING_MODEL,
    OPENAI_COMPLETION_MODEL,
    OLLAMA_CHAT_MODEL,
    OPENAI_EMBEDDING_DIMENSIONS,
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
    image: str


@dataclass
class OllamaMessage(TypedDict):
    role: str
    content: str
    images: NotRequired[List[str]]


@dataclass
class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: List[ChatContent]


class LlmModel(Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"

    @classmethod
    def has_value(cls, value) -> bool:
        """
        Check if a given value exists in the enum.

        Args:
            value (str): The value to check.

        Returns:
            bool: True if the value exists in the enum, False otherwise.
        """
        return value in cls._value2member_map_


DEFAULT_LLM_MODEL = LlmModel.OPENAI


class BaseLLM(ABC):
    @abstractmethod
    def chat(self, messages: List[ChatMessage]) -> str:
        """
        Abstract method to generate a response from the LLM given messages.

        Args:
            messages (List[ChatMessage]): List of messages to send to the model.

        Returns:
            str: Generated response text from the model.
        """
        pass

    @abstractmethod
    def chat_streaming(self, messages: List[ChatMessage]) -> str:
        """
        Abstract method to generate a streaming response from the LLM.

        Args:
            messages (List[ChatMessage]): List of messages to send to the model.

        Returns:
            str: Generated response text from the model.
        """
        pass


class ChatClient:
    llm_model: BaseLLM

    def __init__(self, model: LlmModel, temperature: float = 0.0):
        """
        Initialize the chat client with the selected LLM model.

        Args:
            model (LlmModel): The model type to use (OPENAI or OLLAMA).
            temperature (float, optional): Temperature setting for generation. Defaults to 0.0.
        """
        if model == LlmModel.OPENAI:
            self.llm_model = OpenAILLM(temperature=temperature)
        else:
            self.llm_model = OllamaLLM(temperature=temperature)

    def chat(self, messages: List[ChatMessage], stream: bool = False) -> str:
        """
        Send messages to the LLM and receive a response.

        Args:
            messages (List[ChatMessage]): List of messages to send.
            stream (bool, optional): Whether to stream the response. Defaults to False.

        Returns:
            str: Generated response text.
        """
        if stream:
            return self.llm_model.chat_streaming(messages)
        return self.llm_model.chat(messages)


class OllamaLLM(BaseLLM):
    def __init__(self, temperature: float = 0.0):
        """
        Initialize the Ollama LLM client.

        Args:
            temperature (float, optional): Temperature setting for generation. Defaults to 0.0.
        """
        self.model = OLLAMA_CHAT_MODEL
        self.base_url = os.getenv("OLLAMA_URL")
        self.temperature = temperature

    def chat(self, messages: list[ChatMessage]) -> str:
        """
        Generate a response from Ollama LLM for a list of messages.

        Args:
            messages (List[ChatMessage]): Messages to send to the LLM.

        Returns:
            str: Generated response text.
        """
        ollama_messages = self._to_ollama_messages(messages)

        response = ollama.chat(
            model=self.model,
            messages=ollama_messages,
            options={
                "temperature": self.temperature,
            },
        )

        return response["message"]["content"]

    def chat_streaming(self, messages: List[ChatMessage]) -> str:
        """
        Generate a streaming response from Ollama LLM and print tokens as they arrive.

        Args:
            messages (List[ChatMessage]): Messages to send to the LLM.

        Returns:
            str: Generated response text.
        """
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
    def _to_ollama_messages(messages: list[ChatMessage]) -> List[OllamaMessage]:
        """
        Convert internal ChatMessage format to Ollama-compatible message structure.

        Args:
            messages (List[ChatMessage]): Messages to convert.

        Returns:
            List[OllamaMessage]: Messages formatted for Ollama API.
        """
        ollama_messages: list[OllamaMessage] = []

        for msg in messages:
            text_parts = []
            images = []

            for item in msg["content"]:
                if "text" in item:
                    text_parts.append(item["text"])
                elif "image" in item:
                    images.append(item["image"])

            ollama_msg: OllamaMessage = {
                "role": msg["role"],
                "content": "\n".join(text_parts) if text_parts else "",
            }

            if images:
                ollama_msg["images"] = images

            ollama_messages.append(ollama_msg)

        return ollama_messages


class OpenAILLM(BaseLLM):
    def __init__(self, temperature: float = 0.0):
        """
        Initialize the OpenAI LLM client.

        Args:
            temperature (float, optional): Temperature setting for generation. Defaults to 0.0.
        """
        self.model = OPENAI_COMPLETION_MODEL

        self.temperature = temperature
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def chat(self, messages: List[ChatMessage]) -> str:
        """
        Generate a response from OpenAI LLM for a list of messages.

        Args:
            messages (List[ChatMessage]): Messages to send to the LLM.

        Returns:
            str: Generated response text.
        """
        openai_messages = self._to_openai_messages(messages)

        response = self.client.chat.completions.create(
            model=self.model, messages=openai_messages, max_tokens=4096
        )

        return response.choices[0].message.content

    def chat_streaming(self, messages: List[ChatMessage]) -> str:
        """
        Generate a streaming response from OpenAI LLM and print tokens as they arrive.

        Args:
            messages (List[ChatMessage]): Messages to send to the LLM.

        Returns:
            str: Generated response text.
        """
        openai_messages = self._to_openai_messages(messages)

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            max_tokens=4096,
            stream=True,
            stream_options={"include_usage": True},
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
        """
        Convert internal ChatMessage format to OpenAI-compatible message structure.

        Args:
            messages (List[ChatMessage]): Messages to convert.

        Returns:
            List[OpenAIMessage]: Messages formatted for OpenAI API.
        """
        converted: List[OpenAIMessage] = []

        for msg in messages:
            content_list = []

            for item in msg.get("content", []):
                if "text" in item:
                    # Text block
                    content_list.append({"type": "text", "text": item["text"]})
                elif "image" in item:
                    bytes_url: str = item["image"]
                    content_list.append(
                        cast(
                            ChatCompletionContentPartImageParam,
                            {"type": "image_url", "image_url": {"url": bytes_url}},
                        )
                    )

            # Only add message if there is content
            if content_list:
                converted.append({"role": msg["role"], "content": content_list})

        return converted

    def embed(self, texts: list[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using OpenAI embeddings API.

        Args:
            texts (List[str]): List of text strings to embed.

        Returns:
            List[List[float]]: List of embeddings corresponding to the input texts.
        """
        response = self.client.embeddings.create(
            input=texts,
            model=OPENAI_EMBEDDING_MODEL,
            dimensions=OPENAI_EMBEDDING_DIMENSIONS,
        )
        arr = [data.embedding for data in response.data]
        return arr


def _log_response(model: str, response: str):
    """
    Log the LLM response to the debug logger in structured JSON format.

    Args:
        model (str): Name of the model generating the response.
        response (str): The generated response text.
    """
    logger.debug(
        f"{model} completed response",
        extra={"extra": {"event": "llm_response", "response": response}},
    )
