"use client"

import { useEffect, useState } from "react"
import { ChatContainer, ChatForm, ChatMessages } from "@/components/ui/chat"
import { MessageInput } from "@/components/ui/message-input"
import { MessageList } from "@/components/ui/message-list"
import { PromptSuggestions } from "@/components/ui/prompt-suggestions"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"
import { getModels, sendChatQuery } from "@/lib/api"
import { Message, MessageWithId } from "@/lib/dataclasses"


export function ChatInterface() {
    const [messages, setMessages] = useState<MessageWithId[]>([])
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

    const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
        setInput(e.target.value)
    }

    const handleSubmit = async (event?: { preventDefault?: () => void }) => {
        event?.preventDefault?.();
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            role: "user",
            content: input,
            createdAt: new Date(),
            citations: []
        };

        const updatedHistory = [...messages, { ...userMessage, id: Date.now().toString() }];

        setMessages(updatedHistory as MessageWithId[]);
        setInput("");
        setIsLoading(true);

        try {
            const historyForBackend = updatedHistory.map(({ role, content, createdAt, citations }) => ({ role, content, createdAt, citations }));

            const response = await sendChatQuery(historyForBackend, selectedModel);
            const responseWithoutCitation = response.content.replace(/cite=\[.*?\]/g, "").replace(/\s{2,}/g, " ").trim();

            const assistantMessage = {
                id: (Date.now() + 1).toString(),
                role: "assistant" as const,
                content: responseWithoutCitation,
                createdAt: new Date(),
                citations: response.citations
            };

            setMessages((prev) => [...prev, assistantMessage]);
        } catch (error) {
            console.error(error)
            const assistantMessage = {
                id: (Date.now() + 1).toString(),
                role: "assistant" as const,
                content: "Something went wrong. Please refresh the page and try again!",
                createdAt: new Date(),
                citations: []
            };

            setMessages((prev) => [...prev, assistantMessage]);
            setIsLoading(true)
        } finally {
            setIsLoading(false);
        }
    }

    const append = (message: Omit<Message, 'id' | 'createdAt' | 'citations'>) => {
        setInput(message.content)
        // You could also trigger handleSubmit(undefined) here if you want it to send immediately
    }

    const isEmpty = messages.length === 0
    const isTyping = isLoading // In this custom setup, loading = typing

    return (
        <ChatContainer className="flex-1 overflow-y-auto">
        {isEmpty ? (
            <div className="flex flex-col">
                <Select value={selectedModel} onValueChange={setSelectedModel}>
                    <SelectTrigger className="w-[180px] ms-auto mt-4">
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
                    suggestions={["How to address the ethical limitations of placebo-controlled trials?", "When can the appropriateness of trial be conducted?"]}
                />
            </div>
        ) : null}

        {!isEmpty ? (
            <ChatMessages messages={messages}>
                <MessageList messages={messages} isTyping={isTyping}/>
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
