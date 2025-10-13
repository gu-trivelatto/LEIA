import logging
import uuid

import plotly.express as px
import pandas as pd

logger = logging.getLogger(__name__)

    
def plot_consumption_distribution(
  data: dict[str, float],
) -> str:
  try:
    logger.info("Plotting consumption distribution...")
    labels = [f"{tipo.capitalize()}" for tipo in data.keys()]
    values = [round(valor, 1) for valor in data.values()]
    df = pd.DataFrame({'Tipo': labels, 'Consumo (kWh)': values})
    fig = px.pie(
      df, values='Consumo (kWh)', names='Tipo',
      title='Distribuição de Consumo por Tipo de Aparelho'
    )
    plot_path = f"src/plots/{str(uuid.uuid4())}.png"
    logger.info(f"Saving plot to {plot_path}...")
    fig.write_image(plot_path)
    return plot_path
  except Exception as e:
    logger.error(f"Error occurred while plotting consumption distribution: {e}")
    return "Erro ao gerar gráfico."

def plot_daily_consumption(
  data: list[tuple[str, float]],
  period: str
) -> str:
  try:
    logger.info("Plotting daily consumption...")
    df = pd.DataFrame(data, columns=['Dia', 'Consumo (kWh)'])
    fig = px.line(
      df, x='Dia', y='Consumo (kWh)', 
      title=f'Consumo Diário Total de Energia ({period.replace("_", " ").title()})',
      markers=True
    )
    fig.update_layout(xaxis_title="Data", yaxis_title="Consumo Total (kWh)")
    plot_path = f"src/plots/{str(uuid.uuid4())}.png"
    logger.info(f"Saving plot to {plot_path}...")
    fig.write_image(plot_path)
    return plot_path
  except Exception as e:
    logger.error(f"Error occurred while plotting daily consumption: {e}")
    return "Erro ao gerar gráfico."

def plot_power_outliers(
  data: list[tuple[str, float]],
  period: str
) -> str:
  try:
    logger.info("Plotting power outliers...")
    df = pd.DataFrame(data, columns=['Aparelho', 'Potência Ativa (kW)'])
    fig = px.box(
      df, x='Aparelho', y='Potência Ativa (kW)',
      title=f'Distribuição de Potência e Anomalias por Aparelho ({period.replace("_", " ").title()})',
      points="all" # 'all' mostra todos os pontos, destacando outliers
    )
    fig.update_xaxes(tickangle=45)  # Rotaciona os nomes dos aparelhos para melhor leitura
    plot_path = f"src/plots/{str(uuid.uuid4())}.png"
    logger.info(f"Saving plot to {plot_path}...")
    fig.write_image(plot_path)
    return plot_path
  except Exception as e:
    logger.error(f"Error occurred while plotting power outliers: {e}")
    return "Erro ao gerar gráfico."

def plot_power_factor_analysis(
  data: list[tuple[str, float, str]]
) -> str:
  try:
    logger.info("Plotting power factor analysis...")
    df = pd.DataFrame(data, columns=['Potência Ativa (kW)', 'Fator de Potência'])
    fig = px.scatter(
      df, x='Potência Ativa (kW)', y='Fator de Potência',
      title=f'Análise de Eficiência: Fator de Potência vs. Consumo para {data[0][2]}',
      trendline="ols",  # Adiciona uma linha de tendência para ver a correlação
      trendline_color_override="red"
    )
    fig.update_yaxes(range=[0.5, 1.0]) # Fixa a escala do Fator de Potência
    plot_path = f"src/plots/{str(uuid.uuid4())}.png"
    logger.info(f"Saving plot to {plot_path}...")
    fig.write_image(plot_path)
    return plot_path
  except Exception as e:
    logger.error(f"Error occurred while plotting power factor analysis: {e}")
    return "Erro ao gerar gráfico."
