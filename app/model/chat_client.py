import ollama
from openai import OpenAI
from typing import List, Union
from abc import ABC, abstractmethod
from typing import TypedDict, Literal
from ..config.configer import OLLAMA_BASE_URL, OPENAI_API_KEY
from openai.types.chat import ChatCompletionUserMessageParam, ChatCompletionSystemMessageParam, ChatCompletionAssistantMessageParam
from ..config.logger import get_logger

logger = get_logger("mini-rag." + __name__)

OpenAIMessage = Union[
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
]


class ChatContent(TypedDict, total=False):
    text: str
    image: bytes


class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: List[ChatContent]


class BaseLLM(ABC):
    @abstractmethod
    def chat(self, messages: List[ChatMessage]) -> str:
        pass

    def chat_streaming(self, messages: List[ChatMessage]) -> str:
        pass


class ChatClient:
    def __init__(self, model: str, temperature: float = 0.0):
        if model.startswith("gpt-"):
            self.llm: BaseLLM = OpenAILLM(
                model=model,
                temperature=temperature,
            )
        else:
            self.llm: BaseLLM = OllamaLLM(
                model=model,
                temperature=temperature,
            )

    def chat(self, messages: List[ChatMessage], stream: bool = False) -> str:
        if stream:
            return self.llm.chat_streaming(messages)
        return self.llm.chat(messages)


class OllamaLLM(BaseLLM):
    def __init__(self, model: str = "llava:7b", temperature: float = 0.0):
        self.model = model
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
            stream=True,  # ← THIS enables streaming
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

    def _to_ollama_messages(self, messages: list[ChatMessage]):
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
    def __init__(self, model: str = "gpt-4.1-mini", temperature: float = 0.0):
        self.model = model
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

    def _to_openai_messages(self, messages: list[ChatMessage]) -> List[OpenAIMessage]:
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
