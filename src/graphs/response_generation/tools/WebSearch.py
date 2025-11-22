import logging

from langchain_core.tools import tool
from typing import Annotated
from langchain_community.tools.tavily_search import TavilySearchResults
from src.core.config import settings

logger = logging.getLogger(__name__)


@tool(
  name_or_callable="WebSearch",
  description="""Você deve chamar essa função no caso do usuário solicitar informações
  atuais da internet, como notícias, eventos recentes, ou qualquer informação
  que possa ter mudado recentemente.
  Sempre informe ao usuário as fontes que você usou para a sua resposta. As fontes
  relevantes devem apenas ser listadas no final da resposta, em uma seção chamada 'Fontes'.
  Índices de chamada não devem ser adicionados ao texto, visto que não são bem
  renderizados no chat."""
)
async def WebSearch(
  query: Annotated[
    str, 
    "Uma query curta e objetiva, descrevendo o que o usuário quer saber. Exemplo: 'Quais são as notícias mais recentes sobre IA?'"
  ],
) -> str:
  web_search_tool = TavilySearchResults(tavily_api_key=settings.tavily.API_KEY.get_secret_value())
  response = web_search_tool.invoke({"query": query, "max_results": settings.tavily.MAX_RESULTS})
  
  return response
