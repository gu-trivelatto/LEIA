import logging
import uuid
import os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Configuração de Logger
logger = logging.getLogger(__name__)

# Garante que o diretório existe
os.makedirs("data/plots", exist_ok=True)



def plot_consumo_total_kwh(data: list[dict], periodo: str, message_id: int) -> str:
  """
  Gera um gráfico de barras comparando o consumo acumulado (kWh) entre as fases.
  Input esperado: Output de get_consumo_total_kwh
  """
  try:
    logger.info(f"Plotting consumo total para {periodo}...")
    
    if not data:
        return "Sem dados para gerar o gráfico."

    df = pd.DataFrame(data)
    # Colunas esperadas: 'fase', 'total_kwh', 'min_demand_kw', 'max_demand_kw'

    fig = px.bar(
      df, 
      x='fase', 
      y='total_kwh',
      text='total_kwh',
      title=f'Consumo Total de Energia por Fase ({periodo.replace("_", " ").title()})',
      color='fase',
      labels={'total_kwh': 'Energia (kWh)', 'fase': 'Fase'}
    )
    
    fig.update_traces(textposition='outside')
    fig.update_layout(yaxis_title="Energia Acumulada (kWh)")

    plot_path = f"data/plots/{str(message_id)}.png"
    fig.write_image(plot_path)
    return plot_path
  except Exception as e:
    logger.error(f"Error in plot_consumo_total_kwh: {e}")
    return "Erro ao gerar gráfico."


def plot_picos_demanda(data: list[dict], periodo: str, message_id: int) -> str:
  """
  Gera um gráfico de dispersão mostrando QUANDO e QUANTO foi o pico de cada fase.
  Input esperado: Output de get_picos_demanda
  """
  try:
    logger.info(f"Plotting picos de demanda para {periodo}...")
    
    if not data:
      return "Sem dados para gerar o gráfico."

    df = pd.DataFrame(data)
    # Colunas esperadas: 'fase', 'pico_kw', 'momento'

    fig = px.scatter(
      df, 
      x='momento', 
      y='pico_kw', 
      color='fase',
      size='pico_kw', # A bolinha fica maior conforme a potência
      title=f'Momentos de Pico de Demanda Máxima ({periodo.replace("_", " ").title()})',
      labels={'pico_kw': 'Potência (kW)', 'momento': 'Horário da Ocorrência'}
    )
    
    # Adiciona linhas verticais para facilitar a leitura do tempo
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')
    fig.update_traces(marker=dict(line=dict(width=2, color='DarkSlateGrey')))

    plot_path = f"data/plots/{str(message_id)}.png"
    fig.write_image(plot_path)
    return plot_path
  except Exception as e:
    logger.error(f"Error in plot_picos_demanda: {e}")
    return "Erro ao gerar gráfico."


def plot_saude_eletrica(data: list[dict], periodo: str, message_id: int) -> str:
  """
  Gera um gráfico de barras do Fator de Potência com uma linha de corte em 0.92 (multa).
  Input esperado: Output de get_saude_eletrica
  """
  try:
    logger.info(f"Plotting saude eletrica para {periodo}...")
    
    if not data:
      return "Sem dados para gerar o gráfico."

    df = pd.DataFrame(data)
    # Colunas esperadas: 'fase', 'voltagem_media', 'fator_potencia_medio'

    fig = px.bar(
      df, 
      x='fase', 
      y='fator_potencia_medio',
      color='fator_potencia_medio',
      # Escala de cor: Vermelho se baixo, Verde se alto
      color_continuous_scale=['red', 'yellow', 'green'], 
      range_color=[0.8, 1.0],
      title=f'Eficiência Energética (Fator de Potência) - {periodo.replace("_", " ").title()}'
    )

    # Adiciona linha de referência de 0.92 (Limite ANEEL/Padrão Indústria)
    fig.add_hline(y=0.92, line_dash="dot", annotation_text="Limite Multa (0.92)", annotation_position="bottom right", line_color="red")
    
    fig.update_layout(yaxis_title="Fator de Potência Médio", yaxis_range=[0.5, 1.1])

    plot_path = f"data/plots/{str(message_id)}.png"
    fig.write_image(plot_path)
    return plot_path
  except Exception as e:
    logger.error(f"Error in plot_saude_eletrica: {e}")
    return "Erro ao gerar gráfico."


def plot_perfil_horario(data: list[dict], periodo: str, message_id: int) -> str:
  """
  Gera um gráfico de linhas multivariado mostrando o consumo ao longo das horas do dia (00-23h).
  Input esperado: Output de get_perfil_horario
  """
  try:
    logger.info(f"Plotting perfil horario para {periodo}...")
    
    if not data:
      return "Sem dados para gerar o gráfico."

    df = pd.DataFrame(data)
    # Colunas: 'hora', 'media_kw_f1', 'media_kw_f2', 'media_kw_f3', 'media_geral_kw'

    # Plotly Express requer dados "longos" (melted) ou lista de colunas para múltiplas linhas
    fig = px.line(
      df, 
      x='hora', 
      y=['media_kw_f1', 'media_kw_f2', 'media_kw_f3', 'media_geral_kw'],
      title=f'Perfil de Carga Horária Médio ({periodo.replace("_", " ").title()})',
      labels={'value': 'Potência Média (kW)', 'hora': 'Hora do Dia', 'variable': 'Sensor'}
    )
    
    # Customizar nomes das legendas
    new_names = {'media_kw_f1': 'Fase 1', 'media_kw_f2': 'Fase 2', 'media_kw_f3': 'Fase 3', 'media_geral_kw': 'Média Geral'}
    fig.for_each_trace(lambda t: t.update(name=new_names[t.name],
                                          legendgroup=new_names[t.name],
                                          hovertemplate=t.hovertemplate.replace(t.name, new_names[t.name])))

    plot_path = f"data/plots/{str(message_id)}.png"
    fig.write_image(plot_path)
    return plot_path
  except Exception as e:
    logger.error(f"Error in plot_perfil_horario: {e}")
    return "Erro ao gerar gráfico."


def plot_desbalanceamento(data: list[dict], periodo: str, message_id: int) -> str:
  """
  Gera um gráfico comparativo das correntes (Amperes) para visualizar desbalanceamento.
  Input esperado: Output de get_desbalanceamento (lista com 1 dict)
  """
  try:
    logger.info(f"Plotting desbalanceamento para {periodo}...")
    
    if not data:
      return "Sem dados para gerar o gráfico."

    row = data[0] # Pega o primeiro (e único) resultado da agregação
    
    # Transforma o dict horizontal em dados verticais para o Plotly
    plot_data = {
      'Fase': ['Fase 1', 'Fase 2', 'Fase 3'],
      'Corrente Média (A)': [row['avg_amp_f1'], row['avg_amp_f2'], row['avg_amp_f3']]
    }
    df = pd.DataFrame(plot_data)

    fig = px.bar(
      df,
      x='Fase',
      y='Corrente Média (A)',
      color='Corrente Média (A)',
      title=f'Desbalanceamento de Corrente ({periodo.replace("_", " ").title()})',
      text='Corrente Média (A)'
    )
    
    # Adiciona anotação sobre a diferença máxima
    max_diff = row['diferenca_max_amperes']
    fig.add_annotation(
      x=1, y=max(plot_data['Corrente Média (A)']) * 1.1,
      text=f"Diferença Máx: {max_diff}A",
      showarrow=False,
      font=dict(size=14, color="red")
    )
    
    fig.update_traces(textposition='outside')
    plot_path = f"data/plots/{str(message_id)}.png"
    fig.write_image(plot_path)
    return plot_path
  except Exception as e:
    logger.error(f"Error in plot_desbalanceamento: {e}")
    return "Erro ao gerar gráfico."


def plot_anomalias_voltagem(data: list[dict], periodo: str, message_id: int) -> str:
  """
  Gera um gráfico timeline mostrando eventos de sub/sobretensão.
  Input esperado: Output de get_anomalias_voltagem
  """
  try:
    logger.info(f"Plotting anomalias voltagem para {periodo}...")
    
    if not data:
      # Se não houver anomalias, gera um gráfico vazio com mensagem de "Tudo OK"
      fig = go.Figure()
      fig.add_annotation(text="Nenhuma anomalia detectada no período!", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=20, color="green"))
      fig.update_layout(title=f"Registro de Anomalias ({periodo.replace('_', ' ').title()})")
      plot_path = f"data/plots/{str(uuid.uuid4())}.png"
      fig.write_image(plot_path)
      return plot_path

    df = pd.DataFrame(data)
    # Colunas: 'timestamp', 'sensor', 'voltage', 'tipo', 'desvio_pct'

    fig = px.scatter(
      df,
      x='timestamp',
      y='voltage',
      color='tipo', # ALTA ou BAIXA
      symbol='sensor', # Formatos diferentes para fases diferentes
      hover_data=['desvio_pct'],
      title=f'Eventos de Anomalia de Tensão ({periodo.replace("_", " ").title()})',
      color_discrete_map={'ALTA': 'red', 'BAIXA': 'orange'}
    )

    # Zonas de segurança
    fig.add_hrect(y0=198, y1=242, line_width=0, fillcolor="green", opacity=0.1, annotation_text="Zona Segura (220V ±10%)")
    
    fig.update_layout(yaxis_title="Voltagem (V)")

    plot_path = f"data/plots/{str(message_id)}.png"
    fig.write_image(plot_path)
    return plot_path
  except Exception as e:
    logger.error(f"Error in plot_anomalias_voltagem: {e}")
    return "Erro ao gerar gráfico."