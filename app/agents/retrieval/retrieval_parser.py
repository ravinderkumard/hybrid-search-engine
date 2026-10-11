import json
import logging

from pydantic import ValidationError

from .retrieval_schema import RetrievalDecision

logger = logging.getLogger(__name__)

class RetrievalParser:
    """
    Responsible only for converting raw LLM output
    into a validated RetrievalDecision.
    """
    @staticmethod
    def parse(response: str) -> RetrievalDecision:
        """
        Parse LLM JSON response into RetrievalDecision.

        Args:
            response: Raw LLM response string

        Returns:
            RetrievalDecision

        Raises:
            ValueError
            ValidationError
        """
        try:
            data = json.loads(response)

        except json.JSONDecodeError as ex:
            logger.error("Invalid JSON returned by LLM")
            raise ValueError("LLM returned invalid JSON") from ex

        try:
            decision = RetrievalDecision.model_validate(data)

        except ValidationError as ex:
            logger.error("LLM JSON failed schema validation")
            raise

        return decision