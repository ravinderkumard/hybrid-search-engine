import logging
import os
from pathlib import Path
from typing import Literal, Optional, Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from app.utils.config_loader import load_config

logger = logging.getLogger(__name__)


def _load_environment() -> None:
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")


class ConfigLoader:
    def __init__(self):
        _load_environment()
        self.config = load_config()
        logger.info("Model configuration loaded")
    
    def __getitem__(self, key):
        return self.config[key]

class ModelLoader(BaseModel):
    model_provider: Literal["groq", "openai"] = "openai"
    config: Optional[ConfigLoader] = Field(default=None, exclude=True)

    def model_post_init(self, __context: Any) -> None:
        self.config = ConfigLoader()
    
    class Config:
        arbitrary_types_allowed = True
    
    def load_llm(self):
        """
        Load and return the LLM model.
        """
        _load_environment()
        logger.info("Loading language model provider=%s", self.model_provider)
        if self.model_provider == "openai":
            openai_api_key = os.getenv("OPENAI_API_KEY")
            model_name = os.getenv("OPENAI_MODEL_NAME") or self.config["llm"]["openai"]["model_name"]
            if not openai_api_key:
                logger.warning("OPENAI_API_KEY is not configured")
            logger.info("Initializing OpenAI model model_name=%s", model_name)
            llm = ChatOpenAI(model_name=model_name, api_key=openai_api_key)
        
        return llm
    
