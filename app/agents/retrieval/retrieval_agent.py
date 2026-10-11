from pathlib import Path
import logging

from .retrieval_parser import RetrievalParser
from .retrieval_schema import RetrievalRequest
from .retrieval_schema import RetrievalDecision

logger = logging.getLogger(__name__)


class RetrievalAgent:
    """
    Retrieval Strategy Agent.

    Responsibilities:
        - Load prompt
        - Render prompt
        - Invoke LLM
        - Parse response
        - Return RetrievalDecision
    """

    def __init__(self, llm):

        self.llm = llm

        prompt_path = (
            Path(__file__)
            .parent
            .joinpath("retrieval_strategy.prompt")
        )

        self.prompt_template = prompt_path.read_text(
            encoding="utf-8"
        )

    def decide(
        self,
        request: RetrievalRequest
    ) -> RetrievalDecision:

        logger.info("RetrievalAgent started")

        prompt = self._render_prompt(request.query)

        logger.info("Prompt rendered")

        raw_response = self._invoke_llm(prompt)

        logger.info("LLM response received")

        decision = RetrievalParser.parse(raw_response)

        logger.info(
            "Strategy=%s Confidence=%.2f",
            decision.strategy,
            decision.confidence,
        )

        return decision

    def _render_prompt(
        self,
        query: str
    ) -> str:

        return self.prompt_template.replace(
            "{query}",
            query
        )

    def _invoke_llm(
        self,
        prompt: str
    ) -> str:

        response = self.llm.invoke(prompt)

        # LangChain compatibility
        if hasattr(response, "content"):
            return response.content

        # Plain string compatibility
        return str(response)