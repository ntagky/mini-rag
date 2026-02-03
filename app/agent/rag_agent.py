import re
import uuid
import json
import time
from pydantic import BaseModel
from typing import Tuple, Set, List, Any, Dict
from ..utils.helpers import stream_print
from ..model.chat_client import ChatClient, ChatMessage
from ..retrieval.embedder import Embedder
from ..retrieval.indexer import ElasticsearchIndex
from ..retrieval.ranker import TfidfRetriever
from ..config.configer import (
    SYSTEM_PROMPT_PLANNER,
    USER_PROMPT_PLANNER,
    SYSTEM_PROMPT_SINGLE_RESPONSE_DESCRIBER,
    SYSTEM_PROMPT_REWRITER,
)


class AgentResult(BaseModel):
    answer: str
    citations: List[Any] = []
    log: Dict

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)


class RAGAgent:
    def __init__(
        self,
        embedder: Embedder,
        retriever: ElasticsearchIndex,
        fallback_retriever: TfidfRetriever,
        chat_client: ChatClient,
        is_cli: bool,
    ):
        """
        Initialize a retrieval-augmented generation (RAG) agent.

        Args:
            embedder (Embedder): Embedding service for converting text to vectors.
            retriever (ElasticsearchIndex): Primary retriever using Elasticsearch.
            fallback_retriever (TfidfRetriever): Fallback retriever using TF-IDF.
            chat_client (ChatClient): LLM client to generate responses.
            is_cli (bool): Whether the agent runs in CLI mode (enables streaming output).
        """
        self.embedder = embedder
        self.retriever = retriever
        self.fallback_retriever = fallback_retriever
        self.chat_client = chat_client
        self.is_cli = is_cli

    def run(self, question: str, messages: List[ChatMessage], top_k) -> AgentResult:
        """
        Execute the RAG pipeline: plan, retrieve chunks, draft response, and return citations.

        Args:
            question (str): User question to answer.
            messages (List[ChatMessage]): Conversation history.
            top_k (int): Maximum number of top chunks to retrieve.

        Returns:
            AgentResult: Contains answer text, citations, and detailed log.
        """
        state: Dict[str, Any] = {
            "trace_id": str(uuid.uuid4()),
            "question": question,
            "steps": [],
            "directions": {},
            "retrieval": [],
            "latency_ms": {},
            "tokens": {},
            "errors": [],
        }

        start_time = time.perf_counter()
        try:
            # Generate planning and directions
            state["steps"].append("plan")
            p_start = time.perf_counter()
            state["directions"] = self._generate_plan(question, top_k)
            state["latency_ms"]["plan"] = self._calc_ms(p_start)

            # Check if model provided quick answer
            if (
                "quick_answer" in state["directions"]
                and state["directions"]["quick_answer"]
            ):
                state["steps"].append("answer")
                response = state["directions"]["quick_answer"]
                state["answer"] = response
                if self.is_cli:
                    stream_print(response)
                return AgentResult(answer=response, citations=[], log=state)
            else:
                # Check if model suggested a new query message for querying efficiency
                if (
                    "query_rewriting" in state["directions"]
                    and state["directions"]["query_rewriting"]
                ):
                    state["steps"].append("rewriting")
                    question = self._rewrite_question(messages[:-6:-2])

                # Embed and retrieve close chunks
                state["steps"].append("retrieve")
                r_start = time.perf_counter()
                chunks = self._retrieve_chunks(question, state["directions"])
                state["retrieval"] = [
                    f"document-id: {c.metadata.document_id}, page: {c.metadata.page}, chunk-id: {c.id}, source:{c.source}, score:{c.score}"
                    for c in chunks
                ]
                state["latency_ms"]["retrieve"] = self._calc_ms(r_start)

                # Provide latest messages and call model to draft the final response attached with citations
                state["steps"].append("draft")
                last_messages = messages[-6:]
                d_start = time.perf_counter()
                response, citations = self._draft_response(
                    last_messages, question, chunks, state["directions"]
                )
                state["latency_ms"]["draft"] = self._calc_ms(d_start)
                state["answer"] = response
                state["citations"] = citations
                state["latency_ms"]["total"] = self._calc_ms(start_time)
                return AgentResult(answer=response, citations=citations, log=state)
        except Exception as e:
            state["errors"].append(str(e))
            state["latency_ms"]["total"] = self._calc_ms(start_time)
            return AgentResult(
                answer="I'm sorry, I ran into a technical glitch. Please try asking again in a moment.",
                citations=[],
                log=state,
            )

    def _generate_plan(self, question: str, top_k: int) -> dict:
        """
        Generate a plan for the question using the chat client.

        Args:
            question (str): User question.
            top_k (int): Number of top chunks to retrieve.

        Returns:
            dict: Planning options, including top_k, retrieval strategy, and fallback thresholds.
        """
        plan_json = self.chat_client.chat(
            [
                {
                    "role": "system",
                    "content": [{"text": SYSTEM_PROMPT_PLANNER}],
                },
                {"role": "user", "content": [{"text": USER_PROMPT_PLANNER + question}]},
            ]
        )
        plan = self._parse_plan_options(plan_json)
        if "top_k" in plan and top_k > 0:
            plan["top_k"] = top_k

        return plan

    def _rewrite_question(self, messages: list[ChatMessage]):
        """
        Rewrite a question based on previous messages to improve retrieval or LLM performance.

        Args:
            messages (list[ChatMessage]): Last conversation messages.

        Returns:
            str: Rewritten question string.
        """
        question = (
            f"Current question:\n {messages[0].get('content')[0].get('text')}\n\n"
        )
        question += "Previous user questions:\n"
        for message in messages[1:]:
            question += f"- {message.get('content')[0].get('text')}\n"

        response = self.chat_client.chat(
            [
                {
                    "role": "system",
                    "content": [{"text": SYSTEM_PROMPT_REWRITER}],
                },
                {"role": "user", "content": [{"text": question}]},
            ]
        )
        return response

    def _retrieve_chunks(self, question: str, plan: dict) -> list:
        """
        Retrieve the most relevant document chunks from Elasticsearch and optionally TF-IDF fallback.

        Args:
            question (str): Query string to embed.
            plan (dict): Retrieval strategy and top_k information.

        Returns:
            list: List of DocumentChunkDistant objects representing retrieved chunks.
        """
        embedding = self.embedder.embed([question])[0]
        chunks = self.retriever.similarity_search(
            embedding, top_k=plan["top_k"], threshold=plan["fallback_threshold"]
        )
        if (
            plan["retrieval_strategy"].endswith("tfidf_fallback")
            and len(chunks) < plan["top_k"]
        ):
            fallback_chunks = self.fallback_retriever.retrieve(
                question, top_k=plan["top_k"]
            )
            chunks.extend(fallback_chunks)
        return chunks

    def _draft_response(
        self, messages: list[ChatMessage], question: str, chunks: list, plan: dict
    ) -> Tuple[str, Set]:
        """
        Generate the final answer using the LLM and retrieved chunks.

        Args:
            messages (list[ChatMessage]): Conversation history.
            question (str): User question.
            chunks (list): Retrieved document chunks.
            plan (dict): Drafting instructions and style.

        Returns:
            Tuple[str, Set]: Generated answer text and a set of citations.
        """
        prompt = self._build_user_prompt(question, chunks, plan)
        messages.extend(
            [
                {
                    "role": "system",
                    "content": [{"text": SYSTEM_PROMPT_SINGLE_RESPONSE_DESCRIBER}],
                },
                {"role": "user", "content": [{"text": prompt}]},
            ]
        )
        response = self.chat_client.chat(messages, stream=self.is_cli)
        citations = self._extract_citations(response)
        return response, citations

    @staticmethod
    def _build_user_prompt(question: str, chunks: list, plan: dict) -> str:
        """
        Construct a prompt for the LLM including context, citations, and draft style.

        Args:
            question (str): User question.
            chunks (list): Retrieved document chunks.
            plan (dict): Draft style and instructions.

        Returns:
            str: Prompt text to feed to the LLM.
        """
        context_blocks = []
        for chunk in chunks:
            metadata = chunk.metadata
            context_blocks.append(
                f"cite=[{metadata.document_id}+{metadata.page}] | "
                f"score:{chunk.score} ({chunk.source})]\n"
                f"{chunk.text}"
            )
        context = "\n\n---\n\n".join(context_blocks)

        styles = f"[draft_style: {plan.get('draft_style')}]"
        prompt = f"Styles:\n{styles}\n\nContext:\n{context}\n\nQuestion:\n{question}"
        return prompt

    @staticmethod
    def _parse_plan_options(response_text: str) -> dict:
        """
        Parse a JSON string returned by the LLM into a plan dictionary.

        Args:
            response_text (str): Raw LLM output.

        Returns:
            dict: Parsed plan options including retrieval strategy, top_k, etc.

        Raises:
            ValueError: If JSON parsing fails.
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
            raise ValueError(
                f"Failed to parse plan options JSON: {e}\nResponse: {response_text}"
            )

    @staticmethod
    def _extract_citations(response) -> set:
        """
        Extract cited documents from the LLM response text.

        Args:
            response (str): LLM-generated text containing citations.

        Returns:
            set: Set of citation identifiers.
        """
        matches = re.findall(r"cite=\[(.*?)]", response)
        if len(matches) == 0:
            matches = re.findall(r"\[(.*?)]", response)

        # Split each match by comma (in case there are multiple files per cite) and strip whitespace
        cited_files = set()
        for m in matches:
            cites = [f.strip() for f in m.split("|")]
            cited_files.update(cites)

        return cited_files

    @staticmethod
    def _calc_ms(start_time) -> int:
        """
        Calculate elapsed time in milliseconds from a start time.

        Args:
            start_time (float): Starting time (from time.perf_counter()).

        Returns:
            int: Elapsed time in milliseconds.
        """
        # Calculate difference in ms
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return int(round(elapsed_ms, 0))
