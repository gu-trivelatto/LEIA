import logging
from langchain_groq import ChatGroq
from pydantic import SecretStr

logger = logging.getLogger(__name__)


def create_llm(
  model_name: str,
  api_key: SecretStr,
  temperature: float,
  timeout: float,
):
  logger.info(
    f"Creating LLM with  model: {model_name}, temperature: {temperature}, timeout: {timeout}, api_key set: {'Yes' if api_key else 'No'}"
  )
  return ChatGroq(
    model=model_name,
    api_key=api_key,
    max_retries=3,
    timeout=timeout,
    temperature=temperature,
  )
