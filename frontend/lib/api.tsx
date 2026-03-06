import { DocumentsResponse, IngestionStatusResponse, Message, Response } from "./dataclasses";

export async function getModels(): Promise<string[]> {
  const response = await fetch("http://localhost:8000/api/v1/models");
  if (!response.ok) throw new Error("Failed to fetch models");
  return response.json();
}

export async function getDocuments(): Promise<DocumentsResponse> {
  const response = await fetch("http://localhost:8000/api/v1/documents");
  if (!response.ok) throw new Error("Failed to fetch documents");
  return response.json();
}

export async function ingestCorpus(reset: boolean): Promise<number> {
  const response = await fetch("http://localhost:8000/api/v1/ingest?reset="+reset, {
    method: "POST"
  });
  if (!response.ok) throw new Error("Failed to ingest corpus");
  return response.json();
}

export async function getIngestionStatus(): Promise<IngestionStatusResponse> {
  const response = await fetch("http://localhost:8000/api/v1/ingestion-status")
  if (!response.ok) throw new Error("Failed to fetch ingestion status")
  return response.json()
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

export async function uploadPdf(file: File): Promise<void> {
  const formData = new FormData()
  formData.append("file", file)

  const response = await fetch(
    "http://localhost:8000/api/v1/upload",
    {
      method: "POST",
      body: formData,
    }
  )

  if (!response.ok) throw new Error("File upload failed")
}
