import logging
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, SecretStr

from src.core.logger import init_logging, update_level

logger = logging.getLogger(__name__)


class LLMSettings(BaseModel):
  API_KEY: SecretStr
  MODEL: str = "gpt-4.1"
  TEMPERATURE: float = 0.7
  TIMEOUT: int = 30
  PROMPT_NAME: str


class OmniModelSettings(LLMSettings):
  MAX_COMPLETION_TOKENS: int = 1024
  TOP_P: float = 1.0


class TavilySettings(BaseModel):
  API_KEY: SecretStr
  MAX_RESULTS: int = 3
  
  
class LlamaCloudSettings(BaseModel):
  API_KEY: SecretStr


class QdrantSettings(BaseModel):
  API_KEY: SecretStr
  URL: str
  
  
class HuggingFaceSettings(BaseModel):
  EMBEDDING_MODEL: str


class MemorySettings(BaseModel):
  STRATEGY: Literal["postgres", "in_memory"] = "in_memory"
  DISABLE_MIGRATIONS: bool = True
  URL: SecretStr
  

class ReadingsDatabaseSettings(BaseModel):
  URL: SecretStr


class LoggerSettings(BaseModel):
  LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


class SecuritySettings(BaseModel):
  TYPE: Literal["NONE", "APIKEY"] = "APIKEY"
  SECRET: SecretStr


class BotSettings(BaseModel):
  NAME: str
  MAX_HISTORY: int = 10
  TELEGRAM_TOKEN: SecretStr


class Settings(BaseSettings):
  bot: BotSettings
  main_llm: LLMSettings
  formatter_llm: LLMSettings
  audio_model: LLMSettings
  omni_model: OmniModelSettings
  tavily: TavilySettings
  llama_cloud: LlamaCloudSettings
  qdrant: QdrantSettings
  huggingface: HuggingFaceSettings
  memory: MemorySettings
  logger: LoggerSettings
  readings_database: ReadingsDatabaseSettings
  security: SecuritySettings

  model_config = SettingsConfigDict(
    env_file=".env",
    extra="ignore",
    env_file_encoding="utf-8",
    env_nested_delimiter="__",
    case_sensitive=False,
  )


settings = Settings.model_validate({})

init_logging(settings.logger.LEVEL)
logger.info("Loading configuration from env...")
update_level(settings.logger.LEVEL)
logger.debug(f"Settings model: {settings.model_dump()}")

