import json
from ..model.chat_client import ChatClient
from ..retrieval.embedder import Embedder
from ..retrieval.indexer import ElasticsearchIndex
from ..retrieval.ranker import TfidfRetriever
from ..config.configer import SYSTEM_PROMPT_PLANNER, USER_PROMPT_PLANNER, SYSTEM_PROMPT_SINGLE_RESPONSE_DESCRIBER


class RAGAgent:
    def __init__(
            self, embedder: Embedder, retriever: ElasticsearchIndex, fallback_retriever: TfidfRetriever, chat_client: ChatClient
    ):
        self.embedder = embedder
        self.retriever = retriever
        self.fallback_retriever = fallback_retriever
        self.chat_client = chat_client

    def generate_plan(self, question: str) -> dict:
        """
        Returns a dict describing the plan.
        """
        plan_json = self.chat_client.chat([
            {
                "role": "system",
                "content": [{"text": SYSTEM_PROMPT_PLANNER}],
            },
            {
                "role": "user",
                "content": [{"text": USER_PROMPT_PLANNER + question}]
            }
        ])
        print(plan_json)
        plan = self._parse_plan_options(plan_json)
        return plan

    def retrieve_chunks(self, question: str, plan: dict) -> list:
        """
        Returns a list of chunks according to the plan.
        Includes fallback logic if needed.
        """
        embedding = self.embedder.embed([question])[0]
        chunks = self.retriever.similarity_search(embedding, top_k=plan["top_k"], threshold=plan["fallback_threshold"])
        if plan["retrieval_strategy"].endswith("tfidf_fallback") and len(chunks) < plan["top_k"]:
            fallback_chunks = self.fallback_retriever.retrieve(question, top_k=plan["top_k"])
            chunks.extend(fallback_chunks)
        return chunks

    def draft_response(self, question: str, chunks: list, plan: dict) -> str:
        """
        Returns the generated answer text from LLM.
        """
        prompt = self._build_user_prompt(question, chunks, plan)
        response = self.chat_client.chat([
            {
                "role": "system",
                "content": [{"text": SYSTEM_PROMPT_SINGLE_RESPONSE_DESCRIBER}],
            },
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ])
        return response

    # ----------------
    # Step 4: Cite
    # ----------------
    def attach_citations(self, response_text: str, chunks: list, plan: dict) -> str:
        """
        Returns the final text with citations according to plan["citation_style"].
        """
        if plan["citation_style"] == "inline":
            cited = ""
            for i, chunk in enumerate(chunks):
                cited += f"{response_text}\n[{chunk.metadata.document_id}, chunk {chunk.metadata.chunk_index}]"
            return cited
        # other citation styles...
        return response_text

    @staticmethod
    def _build_user_prompt(question: str, chunks: list, plan: dict) -> str:
        context_blocks = []
        for chunk in chunks:
            metadata = chunk.metadata
            context_blocks.append(
                f"[file:{metadata.document_id} | chunk_index:{metadata.chunk_index} | "
                f"score:{chunk.score} ({chunk.source})]\n"
                f"{chunk.text}"
            )
        context = "\n\n---\n\n".join(context_blocks)

        plan = f"Provide an answer based on this plan: {plan}"

        prompt = f"Context:\n{context}\n\nQuestion:\n{question}"
        print(prompt)
        return prompt

    @staticmethod
    def _parse_plan_options(response_text: str) -> dict:
        """
        Parses the LLM response containing JSON plan options into a Python dict.
        """
        try:
            # Remove leading/trailing whitespace
            response_text = response_text.strip()

            # In case the LLM added ```json ... ``` block, remove it
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            # Parse JSON
            plan_options = json.loads(response_text)
            return plan_options

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse plan options JSON: {e}\nResponse: {response_text}")
