import { ConfettiButton } from "@/components/ui/confetti";
import { AnimatedSpan, Terminal, TypingAnimation } from "@/components/ui/terminal";
import { SquareTerminal } from "lucide-react";

export default function CliPage() {
    return (
        <div className="flex-1 flex flex-col items-start p-2 pt-4 gap-4">
            <div className="flex flex-row items-center">
                <h2 className="text-xl font-semibold tracking-tight">
                    MiniRag is also available via <span className="font-bold">CLI</span>. Download it via 
                </h2>
                <ConfettiButton className="ms-1 text-xl font-semibold">
                    <SquareTerminal></SquareTerminal>
                    pip
                </ConfettiButton>
            </div>
            
            <Terminal className="flex-1">
                <TypingAnimation>$ python main.py cli</TypingAnimation>
                <AnimatedSpan className="text-green-500">
                    ✔ Preflight checks.
                </AnimatedSpan>
                <AnimatedSpan className="text-green-500">
                    ✔ Verifying framework.
                </AnimatedSpan>
                <AnimatedSpan className="text-green-500">
                    ✔ Validating integrations (SQLite, ElasticSearch, TF-IFD)
                </AnimatedSpan>
                <AnimatedSpan className="text-green-500">
                    ✔ Checking OpenAI credentials
                </AnimatedSpan>
                <AnimatedSpan className="text-green-500">
                    ✔ Installing dependencies.
                </AnimatedSpan>
                <AnimatedSpan className="text-blue-500">
                    <span>ℹ Downloaded 1 model from Hugging Face:</span>
                    <span className="pl-2">- sentence-transformers/all-MiniLM-L6-v2</span>
                </AnimatedSpan>
                <TypingAnimation className="text-muted-foreground">
                    Success! Project initialization completed.
                </TypingAnimation>
                <TypingAnimation>&gt; Commands:</TypingAnimation>
                <TypingAnimation>&gt; &#9; ingest [--reset] → scan and ingest corpus</TypingAnimation>
                <TypingAnimation>&gt; &#9; query &lt;your question&gt; [--top-k N] [--model openai|ollama] → ask a question over corpus</TypingAnimation>
                <TypingAnimation>&gt; &#9; exit → quit session</TypingAnimation>
                <TypingAnimation> </TypingAnimation>
                <TypingAnimation className="text-red-500">&gt; query What happens when a patient develop tolerance to a drug? --top-k 5 --model openai</TypingAnimation>
                <TypingAnimation className="text-blue-500">&gt; When a patient develops tolerance to a drug, no benefit is being accrued from the drug, but withdrawal of the drug may lead to disease exacerbation. This can result in an erroneous conclusion of persisting efficacy. Therefore, slow tapering is advisable to avoid withdrawal phenomena [file:E10 - Document 3.pdf | chunk_index:121].</TypingAnimation>
                <TypingAnimation> </TypingAnimation>
                <TypingAnimation>&gt; _</TypingAnimation>
            </Terminal>
        </div>
            
    )
}