import logging
from langchain_core.tools import tool
from typing import Annotated, Literal, cast

from langgraph.prebuilt import InjectedState

# Importando suas classes e funções criadas anteriormente
from src.graphs.response_generation.schemas.MainState import MainState
from src.repositories.DataAccessRepository import DataAccessRepository
from src.services.Plotter import (
  plot_consumo_total_kwh,
  plot_picos_demanda,
  plot_saude_eletrica,
  plot_perfil_horario,
  plot_desbalanceamento,
  plot_anomalias_voltagem
)

logger = logging.getLogger(__name__)

# Instância global do monitor (ou poderia ser injetada)
monitor = DataAccessRepository()

@tool(
  name_or_callable="DataAccess",
  description="""
  ACESSO A DADOS ELÉTRICOS DO LABORATÓRIO.
  Use esta ferramenta para extrair insights sobre o consumo de energia trifásico,
  qualidade da energia e anomalias. O sistema monitora 3 fases (fase1, fase2, fase3).
  
  Ações disponíveis:
  - 'consumo_total': Consumo acumulado (kWh) por fase.
  - 'picos_demanda': Momentos de maior estresse (kW) e horários de pico.
  - 'saude_eletrica': Fator de Potência e eficiência energética.
  - 'perfil_horario': Média de consumo por hora do dia (00h-23h).
  - 'desbalanceamento': Diferença de corrente (Amperes) entre as fases.
  - 'anomalias_voltagem': Lista eventos de sub/sobretensão perigosos.

  Os períodos aceitos são: 
  'ultimos_30_dias', 'ultimos_7_dias', 'ultimos_3_dias', 
  'ontem', 'semana_passada', 'mes_passado', 'hoje', 'tudo'.
  """,
)
def DataAccess(
  action: Annotated[
    Literal[
      "consumo_total",
      "picos_demanda",
      "saude_eletrica",
      "perfil_horario",
      "desbalanceamento",
      "anomalias_voltagem"
    ],
    "A análise específica a ser realizada nos dados elétricos.",
  ],
  period: Annotated[
    Literal[
      "ultimos_30_dias", "ultimos_7_dias", "ultimos_3_dias",
      "ontem", "semana_passada", "mes_passado", "hoje", "tudo"
    ],
    "A janela temporal para análise.",
  ],
  state: Annotated[MainState, InjectedState],
  should_plot: Annotated[
    bool,
    "Se True, gera e salva um gráfico. Defina como True sempre que o usuário pedir 'ver', 'plotar', 'gráfico', 'visualizar' ou similares.",
  ] = False,
) -> str:
    
  logger.info(f"DataAccess tool called: action={action}, period={period}, plot={should_plot}")
  img_name = f"{state.get("chat_id")}_{state.get("message_id")}"

  try:
    # --- Consumo Total ---
    if action == "consumo_total":
      data = monitor.get_consumo_total_kwh(period)
      # Formata texto para o LLM
      summary = "\n".join([f"- {d['fase']}: {d['total_kwh']} kWh (Max Demand: {d['max_demand_kw']} kW)" for d in data])
      
      result_msg = f"Resumo do Consumo ({period}):\n{summary}"
      
      if should_plot:
        path = plot_consumo_total_kwh(data, period, img_name)
        result_msg += f"\n\n[GRÁFICO GERADO]: {path}"
      return result_msg

    # --- Picos de Demanda ---
    elif action == "picos_demanda":
      data = monitor.get_picos_demanda(period)
      summary = "\n".join([f"- {d['fase']}: Pico de {d['pico_kw']} kW em {d['momento']}" for d in data])
      
      result_msg = f"Picos de Demanda Registrados ({period}):\n{summary}"
      
      if should_plot:
        path = plot_picos_demanda(data, period, img_name)
        result_msg += f"\n\n[GRÁFICO GERADO]: {path}"
      return result_msg

    # --- Saúde Elétrica (Fator de Potência) ---
    elif action == "saude_eletrica":
      data = monitor.get_saude_eletrica(period)
      summary = "\n".join([
        f"- {d['fase']}: FP Médio {d['fator_potencia_medio']} (Voltagem Média: {d['voltagem_media']}V)" 
        for d in data
      ])
      
      result_msg = f"Análise de Eficiência/Fator de Potência ({period}):\n{summary}\nNota: FP ideal deve ser > 0.92."
      
      if should_plot:
        path = plot_saude_eletrica(data, period, img_name)
        result_msg += f"\n\n[GRÁFICO GERADO]: {path}"
      return result_msg

    # --- Perfil Horário ---
    elif action == "perfil_horario":
      data = monitor.get_perfil_horario(period)
      # Como são muitos dados (24 horas), retornamos apenas um resumo dos picos para o texto do LLM
      # mas o gráfico mostrará tudo.
      maior_hora = max(data, key=lambda x: x['media_geral_kw'])
      menor_hora = min(data, key=lambda x: x['media_geral_kw'])
      
      summary = (f"Resumo do Perfil Diário:\n"
                  f"- Horário de Maior Consumo: {maior_hora['hora']} com média geral de {maior_hora['media_geral_kw']} kW\n"
                  f"- Horário de Menor Consumo: {menor_hora['hora']} com média geral de {menor_hora['media_geral_kw']} kW")
      
      result_msg = f"Perfil de Carga Horária ({period}):\n{summary}"
      
      if should_plot:
        path = plot_perfil_horario(data, period, img_name)
        result_msg += f"\n\n[GRÁFICO GERADO]: {path}"
      return result_msg

    # --- Desbalanceamento ---
    elif action == "desbalanceamento":
      data = monitor.get_desbalanceamento(period)
      d = data[0] # Unico registro
      
      summary = (f"- Correntes Médias: F1={d['avg_amp_f1']}A, F2={d['avg_amp_f2']}A, F3={d['avg_amp_f3']}A\n"
                  f"- Diferença Máxima entre fases: {d['diferenca_max_amperes']} Amperes")
      
      result_msg = f"Análise de Desbalanceamento ({period}):\n{summary}"
      
      if should_plot:
        path = plot_desbalanceamento(data, period, img_name)
        result_msg += f"\n\n[GRÁFICO GERADO]: {path}"
      return result_msg

    # --- Anomalias ---
    elif action == "anomalias_voltagem":
      data = monitor.get_anomalias_voltagem(period)
      
      if not data:
        result_msg = f"Nenhuma anomalia de voltagem detectada em {period}. O sistema está estável."
      else:
        qtd = len(data)
        top_3 = data[:3]
        details = "\n".join([f"- [{x['timestamp']}] {x['sensor']}: {x['voltage']}V ({x['tipo']} {x['desvio_pct']}%)" for x in top_3])
        result_msg = f"ALERTA: Foram detectadas {qtd} anomalias de tensão em {period}.\nÚltimas 3 ocorrências:\n{details}"

      if should_plot:
        path = plot_anomalias_voltagem(data, period, img_name)
        result_msg += f"\n\n[GRÁFICO GERADO]: {path}"
      return result_msg

    else:
      return "Ação desconhecida."

  except Exception as e:
    error_msg = f"Erro ao executar DataAccess: {str(e)}"
    logger.error(error_msg)
    return error_msg