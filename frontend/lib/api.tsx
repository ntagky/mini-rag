import { Message, Response } from "./dataclasses";

export async function getModels(): Promise<string[]> {
  const response = await fetch("http://localhost:8000/api/v1/models");
  if (!response.ok) throw new Error("Failed to fetch models");
  return response.json(); // Expecting ["model-a", "model-b", ...]
}

export async function sendChatQuery(messages: Message[], model: string): Promise<Response> {
  const response = await fetch("http://localhost:8000/api/v1/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages,
      model,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to fetch response from server");
  }

  const data = await response.json();
  return data as Response;
}
