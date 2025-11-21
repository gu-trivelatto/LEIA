import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DataAccessRepository:
  def __init__(self, db_path="laboratorio_mock.db"):
    self.db_path = db_path

  def _get_conn(self):
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    return conn

  def _get_time_filter(self, periodo):
    """
    Traduz strings amigáveis em cláusulas SQL WHERE.
    """
    filtros = {
      "ultimos_30_dias": "timestamp >= datetime('now', '-30 days')",
      "ultimos_7_dias":  "timestamp >= datetime('now', '-7 days')",
      "ultimos_3_dias":  "timestamp >= datetime('now', '-3 days')",
      "ontem":           "date(timestamp) = date('now', '-1 day')",
      "hoje":            "date(timestamp) = date('now')",
      "semana_passada":  "strftime('%W', timestamp) = strftime('%W', 'now', '-7 days') AND strftime('%Y', timestamp) = strftime('%Y', 'now')",
      "mes_passado":     "strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now', 'start of month', '-1 month')",
      "tudo":            "1=1" # Traz tudo sem filtro
    }
    
    if periodo not in filtros:
      error_msg = f"Período '{periodo}' inválido. Opções: {list(filtros.keys())}"
      logger.error(error_msg)
      return error_msg
        
    return filtros[periodo]

  # =================================================================
  # Consumo Acumulado (Energia Ativa)
  # =================================================================
  def get_consumo_total_kwh(self, periodo="ultimos_30_dias"):
    """
    Retorna o consumo total em kWh por fase.
    Cálculo: Soma(Power kW) * (5min / 60min)
    """
    logger.info(f"Calculating consumo total kWh for period: {periodo}")
    where_clause = self._get_time_filter(periodo)
    query = f"""
      SELECT 
        sensor as fase,
        ROUND(SUM(power) / 12.0, 2) as total_kwh,
        ROUND(MIN(power), 2) as min_demand_kw,
        ROUND(MAX(power), 2) as max_demand_kw
      FROM medicoes
      WHERE {where_clause}
      GROUP BY sensor
    """
    
    with self._get_conn() as conn:
      cursor = conn.execute(query)
      return [dict(row) for row in cursor.fetchall()]

  # =================================================================
  # Picos de Demanda (Momentos Críticos)
  # =================================================================
  def get_picos_demanda(self, periodo="ultimos_7_dias"):
    """
    Identifica o momento exato da maior potência registrada em cada fase.
    """
    logger.info(f"Calculating picos de demanda for period: {periodo}")
    where_clause = self._get_time_filter(periodo)
    query = f"""
      SELECT 
        m1.sensor as fase,
        m1.power as pico_kw,
        m1.timestamp as momento
      FROM medicoes m1
      WHERE m1.power = (
        SELECT MAX(m2.power) 
        FROM medicoes m2 
        WHERE m2.sensor = m1.sensor 
        AND {where_clause}
      )
      AND {where_clause}
      GROUP BY m1.sensor -- Garante um por fase se houver empate
      ORDER BY m1.sensor
    """
    
    with self._get_conn() as conn:
      cursor = conn.execute(query)
      return [dict(row) for row in cursor.fetchall()]

  # =================================================================
  # Saúde Elétrica (Fator de Potência)
  # =================================================================
  def get_saude_eletrica(self, periodo="ultimos_30_dias"):
    """
    Calcula Fator de Potência Médio e Voltagem Média.
    FP = P / Sqrt(P² + Q²)
    """
    logger.info(f"Calculating saúde elétrica for period: {periodo}")
    where_clause = self._get_time_filter(periodo)
    query = f"""
      SELECT 
        sensor as fase,
        ROUND(AVG(voltage), 1) as voltagem_media,
        ROUND(AVG(
          CASE WHEN power = 0 THEN 0 
          ELSE power / SQRT((power*power) + (reactivePower*reactivePower)) 
          END
        ), 3) as fator_potencia_medio
      FROM medicoes
      WHERE {where_clause}
      GROUP BY sensor
    """
    
    with self._get_conn() as conn:
      cursor = conn.execute(query)
      return [dict(row) for row in cursor.fetchall()]

  # =================================================================
  # Perfil Horário (Mapa de Calor)
  # =================================================================
  def get_perfil_horario(self, periodo="ultimos_30_dias"):
    """
    Agrega o consumo médio por hora do dia (00:00 a 23:00).
    Útil para identificar desperdício noturno ou picos de almoço.
    """
    logger.info(f"Calculating perfil horário for period: {periodo}")
    where_clause = self._get_time_filter(periodo)
    query = f"""
      SELECT 
        strftime('%H', timestamp) || ':00' as hora,
        ROUND(AVG(CASE WHEN sensor = 'fase1' THEN power END), 2) as media_kw_f1,
        ROUND(AVG(CASE WHEN sensor = 'fase2' THEN power END), 2) as media_kw_f2,
        ROUND(AVG(CASE WHEN sensor = 'fase3' THEN power END), 2) as media_kw_f3,
        ROUND(AVG(power), 2) as media_geral_kw
      FROM medicoes
      WHERE {where_clause}
      GROUP BY 1
      ORDER BY 1
    """
    
    with self._get_conn() as conn:
      cursor = conn.execute(query)
      return [dict(row) for row in cursor.fetchall()]

  # =================================================================
  # Desbalanceamento de Fases
  # =================================================================
  def get_desbalanceamento(self, periodo="ontem"):
    """
    Verifica se as fases estão carregadas de forma desigual (Ampere).
    """
    logger.info(f"Calculating desbalanceamento for period: {periodo}")
    where_clause = self._get_time_filter(periodo)
    query = f"""
      SELECT 
        ROUND(AVG(CASE WHEN sensor = 'fase1' THEN current END), 2) as avg_amp_f1,
        ROUND(AVG(CASE WHEN sensor = 'fase2' THEN current END), 2) as avg_amp_f2,
        ROUND(AVG(CASE WHEN sensor = 'fase3' THEN current END), 2) as avg_amp_f3,
        ROUND(
          (MAX(AVG(CASE WHEN sensor = 'fase1' THEN current END), 
            AVG(CASE WHEN sensor = 'fase2' THEN current END), 
            AVG(CASE WHEN sensor = 'fase3' THEN current END)) 
          - 
          MIN(AVG(CASE WHEN sensor = 'fase1' THEN current END), 
            AVG(CASE WHEN sensor = 'fase2' THEN current END), 
            AVG(CASE WHEN sensor = 'fase3' THEN current END)))
        , 2) as diferenca_max_amperes
      FROM medicoes
      WHERE {where_clause}
    """
    
    with self._get_conn() as conn:
      cursor = conn.execute(query)
      return [dict(row) for row in cursor.fetchall()]

  # =================================================================
  # Detecção de Anomalias (Voltagem)
  # =================================================================
  def get_anomalias_voltagem(self, periodo="ultimos_7_dias", limite_inf=198, limite_sup=242):
    """
    Retorna lista de eventos onde a voltagem saiu da zona segura.
    Também calcula a % de desvio.
    """
    logger.info(f"Calculating anomalias de voltagem for period: {periodo}")
    where_clause = self._get_time_filter(periodo)
    query = f"""
      SELECT 
        timestamp,
        sensor,
        voltage,
        CASE 
          WHEN voltage > {limite_sup} THEN 'ALTA' 
          WHEN voltage < {limite_inf} THEN 'BAIXA' 
        END as tipo,
        ROUND(((voltage - 220) / 220.0) * 100, 1) as desvio_pct
      FROM medicoes
      WHERE (voltage > {limite_sup} OR voltage < {limite_inf})
      AND voltage > 5 -- Ignora desligamentos totais
      AND {where_clause}
      ORDER BY timestamp DESC
      LIMIT 50
    """
    
    with self._get_conn() as conn:
      cursor = conn.execute(query)
      return [dict(row) for row in cursor.fetchall()]
