import logging

logger = logging.getLogger(__name__)


class PromptHandler:
  def __init__(self) -> None:
    pass

  def get_prompt(self, prompt_name: str) -> str:
    logger.warning(
      f"Trying to fetch prompt: [{prompt_name}] locally."
    )
    try:
      with open(
        f"./src/graphs/prompts/{prompt_name}.md", "r", encoding="utf-8"
      ) as f:
        content = f.read()
        return content
    except Exception as e:
      logger.error(f"Error fetching prompt locally: {e}")
      raise ValueError(
        f"Prompt [{prompt_name}] not found locally."
      )
