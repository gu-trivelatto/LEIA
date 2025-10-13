import logging

from langchain_core.tools import tool
from typing import Annotated, Literal, cast

from src.repositories.DataAccessRepository import (
  get_consumption_distribution,
  get_daily_consumption,
  get_power_readings_by_device,
  get_power_factor_analysis
)
from src.services.Plotter import (
  plot_consumption_distribution,
  plot_daily_consumption,
  plot_power_outliers,
  plot_power_factor_analysis
)

logger = logging.getLogger(__name__)


@tool(
  name_or_callable="DataAccess",
  description="""Você deve chamar essa função para acessar dados históricos de
  consumo de energia, como consumo diário, distribuição de consumo por tipo de
  aparelho, leituras de potência por aparelho, análise do fator de potência e
  detecção de outliers. Os períodos suportados para cada uma das ações são:
  - get_consumption_distribution: 'yesterday', 'last_week', 'last_month'
  - get_daily_consumption: 'last_week', 'last_month', 'last_year'
  - get_power_readings_by_device: 'yesterday', 'last_week'
  - get_power_factor_analysis: 'last_week', 'last_month'
  A lista de dispositivos é a seguinte, onde M é monitor, C é computador,
  R é roteador, P é projetor e A é ar-condicionado:
  - C1: 1; C2: 3; C3: 5; C4: 7; C5: 9; C6: 11; C7: 13; C8: 15; C9: 17; C10: 19; C11: 21; C12: 23
  - M1: 2; M2: 4; M3: 6; M4: 8; M5: 10; M6: 12; M7: 14; M8: 16; M9: 18; M10: 20; M11: 22; M12: 24
  - R1: 25
  - P1: 26
  - A1: 27; A2: 28 """,
)
async def DataAccess(
  action: Annotated[
    Literal[
      "get_consumption_distribution",
      "get_daily_consumption",
      "get_power_readings_by_device",
      "get_power_factor_analysis",
    ],
    "Este campo identifica a ação específica que você deseja realizar.",
  ],
  period: Annotated[
    Literal["yesterday", "last_week", "last_month", "last_year"],
    """O período de tempo para o qual você deseja recuperar os dados. Use
    'yesterday' para dados do dia anterior, 'last_week' para a última semana,
    'last_month' para o último mês e 'last_year' para o último ano.""",
  ],
  should_plot: Annotated[
    bool,
    """Indica se o usuário também solicitou a exibição de um gráfico exibindo
    os dados retornados. Use True se o usuário deixou claro que gostaria de ver
    os dados plotados em gráficos, caso contrário, use False.""",
  ],
  device_id: Annotated[
    int | None,
    """O ID do dispositivo para o qual você deseja realizar a análise do fator de
    potência. Este campo é obrigatório apenas se a ação for 'get_power_factor_analysis'.""",
  ] = None,
):
  ## Distribuição de consumo por tipo de aparelho
  logger.info(f"DataAccess tool called with action: {action}, period: {period}, should_plot: {should_plot}, device_id: {device_id}")
  if action == "get_consumption_distribution":
    if period not in ["yesterday", "last_week", "last_month"]:
      raise ValueError("Período inválido para get_consumption_distribution.")
    
    period = cast(Literal["yesterday", "last_week", "last_month"], period)
    response = await get_consumption_distribution(period)
    
    if response.get("error"):
      logger.error(f"Error occurred while fetching consumption distribution: {response['error']}")
      return response["error"]
    
    str_response = ", ".join([f"{tipo}: {valor:.1f} kWh" for tipo, valor in response.items()])
    
    if len(str_response) > 500:
      logger.warning("Resposta muito longa, truncando.")
      str_response = str_response[:500] + "..."
      
    if should_plot:
      response = cast(dict[str, float], response)
      plot_path = plot_consumption_distribution(response)
      return f"Gráfico salvo no caminho: {plot_path}\nDados: {str_response}"
    else:
      return str_response
    
  ## Consumo diário total de energia
  elif action == "get_daily_consumption":
    if period not in ["last_week", "last_month", "last_year"]:
      raise ValueError("Período inválido para get_daily_consumption.")
    
    period = cast(Literal["last_week", "last_month", "last_year"], period)
    response = await get_daily_consumption(period)
    
    if response.get("error"):
      logger.error(f"Error occurred while fetching daily consumption: {response['error']}")
      return response["error"]
    
    str_response = ", ".join([f"{dia}: {consumo:.1f} kWh" for dia, consumo in response.get("data", [])])
    
    if len(str_response) > 500:
      logger.warning("Resposta muito longa, truncando.")
      str_response = str_response[:500] + "..."
    
    if should_plot:
      response = cast(list[tuple[str, float]], response["data"])
      plot_path = plot_daily_consumption(response, period)
      return f"Gráfico salvo no caminho: {plot_path}\nDados: {str_response}"
    else:
      return str_response
    
  ## Leituras de potência por aparelho com detecção de outliers
  elif action == "get_power_readings_by_device":
    if period not in ["yesterday", "last_week"]:
      raise ValueError("Período inválido para get_power_readings_by_device.")
    
    period = cast(Literal["yesterday", "last_week"], period)
    response = await get_power_readings_by_device(period)
    
    if response.get("error"):
      logger.error(f"Error occurred while fetching power readings by device: {response['error']}")
      return response["error"]
    
    if not should_plot:
      return "Gráficos são necessários para esta ação."
    else:
      response = cast(list[tuple[str, float]], response["data"])
      plot_path = plot_power_outliers(response, period)
      return f"Gráfico salvo no caminho: {plot_path}"

  ## Análise do fator de potência para um aparelho específico
  elif action == "get_power_factor_analysis":
    if period not in ["last_week", "last_month"]:
      raise ValueError("Período inválido para get_power_factor_analysis.")
    if device_id is None:
      raise ValueError("device_id é obrigatório para get_power_factor_analysis.")
    
    period = cast(Literal["last_week", "last_month"], period)
    response = await get_power_factor_analysis(device_id, period)
    
    if response.get("error"):
      logger.error(f"Error occurred while fetching power factor analysis: {response['error']}")
      return response["error"]
    
    if not should_plot:
      return "Gráficos são necessários para esta ação."
    else: 
      response = cast(list[tuple[str, float, str]], response["data"])
      plot_path = plot_power_factor_analysis(response)
      return f"Gráfico salvo no caminho: {plot_path}"
