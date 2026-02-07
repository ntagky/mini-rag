import re
import uuid
import json
import time
from dataclasses import dataclass, field
from typing import Tuple, Set, List, Any, Dict, Callable, Optional
from pydantic import BaseModel
from app.config.logger import get_logger
from app.utils.helpers import stream_print
from app.model.chat_client import ChatClient, ChatMessage
from app.retrieval.embedder import Embedder
from app.retrieval.indexer import ElasticsearchIndex
from app.retrieval.ranker import TfidfRetriever
from app.config.configer import (
    SYSTEM_PROMPT_PLANNER,
    USER_PROMPT_PLANNER,
    SYSTEM_PROMPT_SINGLE_RESPONSE_DESCRIBER,
    SYSTEM_PROMPT_REWRITER,
)

logger = get_logger("mini-rag." + __name__)


class AgentResult(BaseModel):
    answer: str
    citations: List[Any] = []


@dataclass
class State:
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question: str = ""
    response: Optional[str] = None
    citations: Set[Any] = field(default_factory=set)
    steps: List[str] = field(default_factory=list)
    plan: Dict[str, Any] = field(default_factory=dict)
    retrieval: List[str] = field(default_factory=list)
    latency_ms: Dict[str, float] = field(default_factory=dict)
    tokens: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class Context:
    question: str = ""
    messages: List[Any] = field(default_factory=list)
    chunks: List[Any] = field(default_factory=list)
    response: Optional[str] = None
    citations: Set[Any] = field(default_factory=set)
    plan_steps: List[Dict[str, Any]] = field(default_factory=list)


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

        step_function = Callable[[Context, State, Dict[str, Any]], None]
        self.STEP_REGISTRY: Dict[str, step_function] = {
            "plan": self._step_plan,
            "answer": self._step_answer,
            "rewrite": self._step_rewrite,
            "retrieve": self._step_retrieve,
            "draft": self._step_draft,
        }

    def run(
        self, question: str, messages: List[ChatMessage], top_k: int
    ) -> AgentResult:
        state = State(question=question)
        context = Context(question=question, messages=messages)
        directions = {"user_top_k": top_k} if top_k > 1 else {}
        start_time = time.perf_counter()

        try:
            state.steps.append("plan")
            self._step_plan(context, state, directions)

            for step in context.plan_steps:
                name = step["name"]

                if name not in self.STEP_REGISTRY:
                    raise ValueError(f"Unknown step: {name}")

                state.steps.append(name)
                self.STEP_REGISTRY[name](context, state, step)

            state.latency_ms["total"] = self._calc_ms(start_time)

            if self.is_cli and context.response:
                stream_print(context.response)

            logger.debug(state)
            return AgentResult(
                answer=context.response,
                citations=context.citations,
                log=state,
            )
        except Exception as e:
            logger.error(str(e))
            state.errors.append(str(e))
            state.latency_ms["total"] = self._calc_ms(start_time)
            logger.debug(state)
            return AgentResult(
                answer="I'm sorry, I ran into a technical glitch. Please try asking again in a moment.",
                citations=[],
            )

    def _generate_plan(self, question: str) -> dict:
        """
        Generate a plan for the question using the chat client.

        Args:
            question (str): User question.

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
        print(f"Generated plan response: {plan}")
        return plan

    def _rewrite_question(self, messages: list[ChatMessage], style: str):
        """
        Rewrite a question based on previous messages to improve retrieval or LLM performance.

        Args:
            messages (list[ChatMessage]): Last conversation messages.
            style (str): Rewrite style for maximizing response validity.

        Returns:
            str: Rewritten question string.
        """
        question = (
            f"Current question:\n {messages[0].get('content')[0].get('text')}\n\n"
        )
        question += "Previous user questions:\n"
        for message in messages[1:]:
            question += f"- {message.get('content')[0].get('text')}\n"
        question += f"Please rewrite using the following style: {style}"

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

    def _retrieve_chunks(
        self, question: str, strategy: str, top_k: int, fallback_threshold: float
    ) -> list:
        """
        Retrieve the most relevant document chunks from Elasticsearch and optionally TF-IDF fallback.

        Args:
            question (str): Query string to embed.
            strategy (str): Retrieval strategy.
            top_k (int): top_k information.
            fallback_threshold (float): Fallback threshold value
        Returns:
            list: List of DocumentChunkDistant objects representing retrieved chunks.
        """
        embedding = self.embedder.embed([question])[0]
        chunks = self.retriever.similarity_search(
            embedding, top_k=top_k, threshold=fallback_threshold
        )
        if strategy.endswith("tfidf_fallback") and len(chunks) < top_k:
            fallback_chunks = self.fallback_retriever.retrieve(question, top_k=top_k)
            chunks.extend(fallback_chunks)
        return chunks

    def _draft_response(
        self, messages: list[ChatMessage], question: str, chunks: list, style: str
    ) -> Tuple[str, Set]:
        """
        Generate the final answer using the LLM and retrieved chunks.

        Args:
            messages (list[ChatMessage]): Conversation history.
            question (str): User question.
            chunks (list): Retrieved document chunks.

        Returns:
            Tuple[str, Set]: Generated answer text and a set of citations.
        """
        prompt = self._build_user_prompt(question, chunks, style)
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

    def _step_plan(self, context: Context, state: State, direction: dict):
        """
        Calls _generate_plan and logs latency/errors.
        Stores result in state['plan'] and returns steps for execution.
        """
        s_start = time.perf_counter()
        try:
            plan = self._generate_plan(context.question)

            # Inject user_top_k if provided
            user_top_k = getattr(direction, "user_top_k", None)
            if user_top_k is not None:
                for s in context.plan_steps:
                    if s["name"] == "retrieve":
                        s["user_top_k"] = user_top_k

            state.plan = plan
            if not plan.get("steps"):
                raise ValueError("Planner returned no steps")
            context.plan_steps = plan["steps"]

        except Exception as e:
            state.errors.append(f"plan: {str(e)}")
            context.plan_steps = []
        finally:
            state.latency_ms["plan"] = self._calc_ms(s_start)

    def _step_answer(self, context: Context, state: State, step: dict):
        s_start = time.perf_counter()
        try:
            context.response = step["response"]
            state.response = context.response
        finally:
            state.latency_ms["answer"] = self._calc_ms(s_start)

    def _step_rewrite(self, context: Context, state: State, step: dict):
        s_start = time.perf_counter()
        try:
            context.question = self._rewrite_question(
                messages=context.messages,
                style=step["style"],
            )
        except Exception as e:
            state.errors.append(f"rewrite: {str(e)}")
        finally:
            state.latency_ms["rewrite"] = self._calc_ms(s_start)

    def _step_retrieve(self, context: Context, state: State, step: dict):
        s_start = time.perf_counter()
        try:
            # Override if user provided top_k ---
            if "user_top_k" in step and step["user_top_k"] is not None:
                top_k = step["user_top_k"]
                step["strategy"] = "vector+tfidf_fallback"
                step["fallback_threshold"] = 0.5
            else:
                top_k = min(step.get("top_k", 5), 20)

            context.chunks = self._retrieve_chunks(
                question=context.question,
                strategy=step["strategy"],
                top_k=top_k,
                fallback_threshold=step["fallback_threshold"],
            )

            state.retrieval = [
                f"document-id: {c.metadata.document_id}, "
                f"page: {c.metadata.page}, "
                f"chunk-id: {c.id}, "
                f"source:{c.source}, "
                f"score:{c.score}"
                for c in context.chunks
            ]

            if not context.chunks:
                state.errors.append("Retrieval returned zero chunks")

        except Exception as e:
            state.errors.append(f"retrieve: {str(e)}")
        finally:
            state.latency_ms["retrieve"] = self._calc_ms(s_start)

    def _step_draft(self, context: Context, state: State, step: dict):
        s_start = time.perf_counter()
        try:
            last_messages = context.messages[-6:]

            response, citations = self._draft_response(
                messages=last_messages,
                question=context.question,
                chunks=context.chunks,
                style=step["style"],
            )

            context.response = response
            context.citations = citations
            state.response = response
            state.citations = citations

        except Exception as e:
            state.errors.append(f"draft: {str(e)}")
        finally:
            state.latency_ms["draft"] = self._calc_ms(s_start)

    @staticmethod
    def _build_user_prompt(question: str, chunks: list, style: str) -> str:
        """
        Construct a prompt for the LLM including context, citations, and draft style.

        Args:
            question (str): User question.
            chunks (list): Retrieved document chunks.
            style (str): Draft style.

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

        styles = f"[draft_style: {style}]"
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
