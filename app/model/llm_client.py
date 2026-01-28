import ollama
import base64
from pathlib import Path
from typing import List, Dict, Any


class LLMClient:
    def __init__(self, model: str = "llava:7b", base_url: str = "http://localhost:11434", temperature: float = 0.0):
        self.model = model
        self.base_url = base_url
        self.temperature = temperature

    def generate_text(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        messages = self._build_text_messages(system_prompt, user_prompt)
        response = self._call_ollama(messages)
        return self._parse_response(response)

    def generate_multimodal(self, system_prompt: str, user_prompt: str, images: List[Path]) -> Dict[str, Any]:
        image_payloads = self._load_images(images)
        messages = self._build_multimodal_messages(
            system_prompt,
            user_prompt,
            image_payloads,
        )
        response = self._call_ollama(messages)
        return self._parse_response(response)

    def _build_text_messages(self, system_prompt: str, user_prompt: str) -> List[Dict[str, Any]]:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _build_multimodal_messages(self, system_prompt: str, user_prompt: str, images: List[str]) -> List[Dict[str, Any]]:
        return [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_prompt,
                "images": images,
            },
        ]

    def _call_ollama(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        return ollama.chat(
            model=self.model,
            messages=messages,
            options={
                "temperature": self.temperature,
            },
        )

    def _load_images(self, images: List[Path]) -> List[str]:
        encoded_images = []

        for image_path in images:
            if not image_path.exists():
                raise FileNotFoundError(f"Image not found: {image_path}")

            with open(image_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                encoded_images.append(encoded)

        return encoded_images

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        message = response.get("message", {})
        content = message.get("content", "")

        return {
            "text": content,
            "model": response.get("model"),
            "done": response.get("done", False),
            "total_duration": response.get("total_duration"),
            "eval_count": response.get("eval_count"),
        }
