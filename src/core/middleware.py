from fastapi import Request
from starlette.middleware.base import (
  BaseHTTPMiddleware,
  RequestResponseEndpoint,
)
from starlette.responses import Response

from .readings_database import AsyncSessionMaker, db_session_context


class DBSessionMiddleware(BaseHTTPMiddleware):
  async def dispatch(
    self, request: Request, call_next: RequestResponseEndpoint
  ) -> Response:
    # Cria uma nova sessão para esta requisição específica
    async with AsyncSessionMaker() as session:
      # Define o valor da context var para esta sessão
      token = db_session_context.set(session)

      try:
        # Processa a requisição
        response = await call_next(request)
      finally:
        # Garante que a sessão seja fechada e o contexto resetado
        await session.close()
        db_session_context.reset(token)

    return response
