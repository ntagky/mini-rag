"use client"

import { useEffect, useState } from "react"
import { ChatContainer, ChatForm, ChatMessages } from "@/components/ui/chat"
import { MessageInput } from "@/components/ui/message-input"
import { MessageList } from "@/components/ui/message-list"
import { PromptSuggestions } from "@/components/ui/prompt-suggestions"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"
import { getModels } from "@/lib/api"


type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [models, setModels] = useState<string[]>([]);
    const [selectedModel, setSelectedModel] = useState<string>("");

    useEffect(() => {
        const loadModels = async () => {
            const cached = sessionStorage.getItem("chat_models");

            if (cached) {
                const parsedModels = JSON.parse(cached);
                setModels(parsedModels);
                if (parsedModels.length > 0) {
                    console.log("They were cached")
                    setSelectedModel(parsedModels[0]);
                    return;
                };
            }

            try {
                const data = await getModels();
                setModels(data);
                if (data.length > 0) {
                    setSelectedModel(data[0]);
                    sessionStorage.setItem("chat_models", JSON.stringify(data));
                }
            } catch (error) {
                console.error("Error loading models:", error);
            }
        };
        loadModels();
    }, []);

    // 1. Handle input changes
    const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
        setInput(e.target.value)
    }

    // 2. The custom fetch logic
    const handleSubmit = async (event?: { preventDefault?: () => void }) => {
        event?.preventDefault?.();
        if (!input.trim() || isLoading) return

        const userMessage: Message = {
        id: Date.now().toString(),
        role: "user",
        content: input,
        }

        // Update UI immediately
        setMessages((prev) => [...prev, userMessage])
        setInput("")
        setIsLoading(true)

        try {
        const response = await fetch("http://localhost:8000/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: userMessage.content }), // Adjust key to match your backend
        })

        if (!response.ok) throw new Error("Failed to fetch")

        const data = await response.json()
        
        const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: data.response || data.content || "No response received",
        }

        setMessages((prev) => [...prev, assistantMessage])
        } catch (error) {
        console.error("Chat Error:", error)
        // Optional: Add an error message to the chat UI here
        } finally {
        setIsLoading(false)
        }
    }

    // 3. Helper for suggestions
    const append = (message: Omit<Message, 'id'>) => {
        setInput(message.content)
        // You could also trigger handleSubmit(undefined) here if you want it to send immediately
    }

    const isEmpty = messages.length === 0
    const isTyping = isLoading // In this custom setup, loading = typing

    return (
        <ChatContainer className="flex-1 py-4">
        {isEmpty ? (
            <div className="flex flex-col">
                <Select value={selectedModel} onValueChange={setSelectedModel}>
                    <SelectTrigger className="w-[180px] ms-auto">
                        <SelectValue placeholder="Select a model" />
                    </SelectTrigger>
                    <SelectContent>
                        {models.map((model) => (
                        <SelectItem key={model} value={model}>
                            {model}
                        </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
                <PromptSuggestions
                    label="Looking for something?"
                    append={append}
                    suggestions={["What is the capital of France?", "Tell me a joke"]}
                />
            </div>
            
            
        ) : null}

        {!isEmpty ? (
            <ChatMessages messages={messages}>
            <MessageList messages={messages} isTyping={isTyping} />
            </ChatMessages>
        ) : null}
            
        <ChatForm
            className="mt-auto"
            isPending={isLoading}
            handleSubmit={handleSubmit}
        >
            {() => (
            <MessageInput
                value={input}
                onChange={handleInputChange}
                isGenerating={isLoading}
                placeholder="Type your message..."
            />
            )}
        </ChatForm>
        </ChatContainer>
    )
}