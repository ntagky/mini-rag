import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"

export default function ModelsPage() {
  return (
    <div className="space-y-6 p-2">
      <div className="flex justify-start mt-4">
        <h2 className="text-xl font-semibold tracking-tight">
          Generation Models
        </h2>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>LLaVA 7B (via Ollama)</CardTitle>
            <CardDescription>Local multimodal model</CardDescription>
          </CardHeader>
          <Separator/>
          <CardContent className="text-sm text-muted-foreground space-y-2">
            <p>
              LLaVA 7B is an open-source vision-language model capable of understanding
              both images and text.
            </p>
            <p>
              Running through Ollama allows fully local inference, improving privacy
              and reducing dependency on external APIs.
            </p>
            <p>
              Ideal for experimentation, offline workflows, and cost-efficient deployments.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>GPT-4o Mini (OpenAI)</CardTitle>
            <CardDescription>Fast, efficient cloud model</CardDescription>
          </CardHeader>
          <Separator/>
          <CardContent className="text-sm text-muted-foreground space-y-2">
            <p>
              GPT-4o Mini delivers strong reasoning and language capabilities with
              significantly lower latency.
            </p>
            <p>
              Hosted by OpenAI, it provides reliable performance without requiring
              local compute resources.
            </p>
            <p>
              Well suited for production environments where speed and consistency matter.
            </p>
          </CardContent>
        </Card>

      </div>

      <div className="mt-8">
        <h2 className="text-xl font-semibold tracking-tight">
          Embedding Models
        </h2>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>text-embedding-3-small</CardTitle>
            <CardDescription>OpenAI embedding model</CardDescription>
          </CardHeader>
          <Separator/>
          <CardContent className="text-sm text-muted-foreground space-y-2">
            <p>
              Generates high-quality vector representations using <strong>512 dimensions</strong>,
              enabling fast and accurate semantic search.
            </p>
            <p>
              Optimized for performance and cost efficiency while maintaining strong
              retrieval accuracy.
            </p>
            <p>
              Ideal for scalable RAG pipelines and production-grade applications.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>all-MiniLM-L6-v2</CardTitle>
            <CardDescription>Sentence Transformers</CardDescription>
          </CardHeader>
          <Separator/>
          <CardContent className="text-sm text-muted-foreground space-y-2">
            <p>
              A lightweight transformer model producing embeddings with <strong>384 dimensions</strong>.
            </p>
            <p>
              Designed for speed while preserving strong semantic similarity performance.
            </p>
            <p className="">
              Popular for local deployments and real-time retrieval systems.
            </p>
          </CardContent>
        </Card>
      </div>

    </div>
  )
}
