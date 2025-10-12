import hmac
import logging
from src.core.config import settings
from fastapi import Header, HTTPException, status

logger = logging.getLogger(__name__)


def _verify_api_key(api_key_header: str | None):
  """Estratégia de validação de API Key."""
  if api_key_header is None:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Header X-Api-Key is missing for API Key validation",
    )

  # Use hmac.compare_digest para uma comparação segura contra timing attacks
  if not hmac.compare_digest(
    api_key_header, settings.security.SECRET.get_secret_value()
  ):
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN, detail="Error: Invalid API Key"
    )
  logger.debug("API Key validated successfully.")


async def validate_security(
  x_api_key: str | None = Header(
    default=None, description="Static API Key for authentication"
  ),
):
  """
  Dispatcher de segurança que escolhe a estratégia de validação
  baseado na configuração (settings.security.TYPE).
  """
  auth_type = settings.security.TYPE

  if auth_type == "NONE":
    logger.warning(
      "Security is disabled by configuration. Skipping validation."
    )
    return

  elif auth_type == "APIKEY":
    _verify_api_key(x_api_key)

  else:
    logger.error(f"Invalid security type configured: {settings.security.TYPE}")
    # Este é um erro de configuração do servidor, não do cliente
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Security system is misconfigured",
    )
