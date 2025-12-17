import os
import logging
from datetime import datetime, timedelta
from typing import Optional
from src.core.config import settings

import httpx

logger = logging.getLogger(__name__)


class DataAccessRepository:
  def __init__(self, api_url: Optional[str] = None):
    """
    Inicializa o repositório de acesso a dados via API REST.

    Args:
      api_url: URL base da API de medições. Se None, usa MEASUREMENTS_API_URL do ambiente.
    """
    self.api_url = api_url or settings.readings_database.MEASUREMENT_API_URL
    self.channel = settings.readings_database.MQTT_CHANNEL or "lab"
    self.api_url = self.api_url.rstrip("/")

  def _parse_period_to_time_range(self, periodo: str) -> tuple[str, str]:
    """
    Converte strings amigáveis de período em timestamps ISO.

    Args:
      periodo: String de período (ex: "ultimos_30_dias", "hoje", "ontem")

    Returns:
      Tupla (from_time, to_time) em formato ISO
    """
    now = datetime.now()

    period_map = {
      "ultimos_30_dias": timedelta(days=30),
      "ultimos_7_dias": timedelta(days=7),
      "ultimos_3_dias": timedelta(days=3),
      "ontem": None,  # Caso especial
      "hoje": None,  # Caso especial
      "semana_passada": None,  # Caso especial
      "mes_passado": None,  # Caso especial
      "tudo": timedelta(days=3650),  # ~10 anos
    }

    if periodo not in period_map:
      error_msg = f"Período '{periodo}' inválido. Opções: {list(period_map.keys())}"
      logger.error(error_msg)
      raise ValueError(error_msg)

    if periodo == "hoje":
      from_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
      to_dt = now
    elif periodo == "ontem":
      yesterday = now - timedelta(days=1)
      from_dt = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
      to_dt = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif periodo == "semana_passada":
      # Semana passada: mesma semana, semana anterior
      days_since_monday = now.weekday()
      last_monday = now - timedelta(days=days_since_monday + 7)
      last_sunday = last_monday + timedelta(days=6)
      from_dt = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
      to_dt = last_sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif periodo == "mes_passado":
      # Mês passado
      first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
      last_day_of_last_month = first_of_this_month - timedelta(days=1)
      first_of_last_month = last_day_of_last_month.replace(day=1)
      from_dt = first_of_last_month
      to_dt = last_day_of_last_month.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
      # Casos de delta simples
      delta = period_map[periodo]
      from_dt = now - delta
      to_dt = now
      
    logger.debug(f"Parsed period '{periodo}' to range: {from_dt.isoformat()} to {to_dt.isoformat()}")

    return from_dt.isoformat(timespec="seconds"), to_dt.isoformat(timespec="seconds")

  def _make_request(self, endpoint: str, params: Optional[dict] = None) -> dict:
    """
    Faz uma requisição HTTP GET para a API.

    Args:
      endpoint: Caminho do endpoint (ex: "/analytics/lab/consumption")
      params: Parâmetros de query string

    Returns:
      Resposta JSON da API

    Raises:
      Exception: Se a requisição falhar
    """
    url = f"{self.api_url}{endpoint}"
    try:
      response = httpx.get(url, params=params or {}, timeout=30.0)
      response.raise_for_status()
      logger.debug(f"Request to {url} successful with status code {response.status_code}")
      return response.json()
    except httpx.HTTPError as e:
      logger.error(f"Erro ao fazer requisição para {url}: {e}")
      raise

  # =================================================================
  # Consumo Acumulado (Energia Ativa)
  # =================================================================
  def get_consumo_total_kwh(self, periodo: str = "ultimos_30_dias"):
    """
    Retorna o consumo total em kWh por fase.

    Usa integração trapezoidal sobre o tempo para calcular energia.
    Não assume intervalo regular de medições.

    Args:
      periodo: Período de tempo (ex: "ultimos_30_dias", "hoje", "ontem")

    Returns:
      Lista de dicionários com fase, total_kwh, min_demand_kw, max_demand_kw
    """
    logger.info(f"Calculating consumo total kWh for period: {periodo}")
    from_time, to_time = self._parse_period_to_time_range(periodo)
    endpoint = f"/analytics/{self.channel}/consumption"
    response = self._make_request(endpoint, params={"from_time": from_time, "to_time": to_time})

    # Renomear campos de inglês para português
    results = []
    for item in response.get("results", []):
      results.append({
        "fase": item["sensor"],
        "total_kwh": item["total_kwh"],
        "min_demand_kw": item["min_demand_kw"],
        "max_demand_kw": item["max_demand_kw"],
      })
    return results

  # =================================================================
  # Picos de Demanda (Momentos Críticos)
  # =================================================================
  def get_picos_demanda(self, periodo: str = "ultimos_7_dias"):
    """
    Identifica o momento exato da maior potência registrada em cada fase.

    Args:
      periodo: Período de tempo (ex: "ultimos_7_dias", "ontem")

    Returns:
      Lista de dicionários com fase, pico_kw, momento
    """
    logger.info(f"Calculating picos de demanda for period: {periodo}")
    from_time, to_time = self._parse_period_to_time_range(periodo)
    endpoint = f"/analytics/{self.channel}/demand_peaks"
    response = self._make_request(endpoint, params={"from_time": from_time, "to_time": to_time})

    # Renomear campos de inglês para português
    results = []
    for item in response.get("results", []):
      results.append({
        "fase": item["sensor"],
        "pico_kw": item["peak_kw"],
        "momento": item["timestamp"],
      })
    return results

  # =================================================================
  # Saúde Elétrica (Fator de Potência)
  # =================================================================
  def get_saude_eletrica(self, periodo: str = "ultimos_30_dias"):
    """
    Calcula Fator de Potência Médio e Voltagem Média.

    FP = P / Sqrt(P² + Q²)

    Args:
      periodo: Período de tempo (ex: "ultimos_30_dias")

    Returns:
      Lista de dicionários com fase, voltagem_media, fator_potencia_medio
    """
    logger.info(f"Calculating saúde elétrica for period: {periodo}")
    from_time, to_time = self._parse_period_to_time_range(periodo)
    endpoint = f"/analytics/{self.channel}/electrical_health"
    response = self._make_request(endpoint, params={"from_time": from_time, "to_time": to_time})

    # Renomear campos de inglês para português
    results = []
    for item in response.get("results", []):
      results.append({
        "fase": item["sensor"],
        "voltagem_media": item["avg_voltage"],
        "fator_potencia_medio": item["avg_power_factor"],
      })
    return results

  # =================================================================
  # Perfil Horário (Mapa de Calor)
  # =================================================================
  def get_perfil_horario(self, periodo: str = "ultimos_30_dias"):
    """
    Agrega o consumo médio por hora do dia (00:00 a 23:00).

    Útil para identificar desperdício noturno ou picos de almoço.

    Args:
      periodo: Período de tempo (ex: "ultimos_30_dias")

    Returns:
      Lista de dicionários com hora, media_kw_f1, media_kw_f2, media_kw_f3, media_geral_kw
    """
    logger.info(f"Calculating perfil horário for period: {periodo}")
    from_time, to_time = self._parse_period_to_time_range(periodo)
    endpoint = f"/analytics/{self.channel}/hourly_profile"
    response = self._make_request(endpoint, params={"from_time": from_time, "to_time": to_time})

    # Agregar dados por hora e fase (sensor-específico para fase1, fase2, fase3)
    hourly_data = {}
    for item in response.get("results", []):
      hour = f"{item['hour']}:00"
      sensor = item["sensor"]
      avg_power = item["avg_power_kw"]

      if hour not in hourly_data:
        hourly_data[hour] = {
          "hora": hour,
          "media_kw_f1": None,
          "media_kw_f2": None,
          "media_kw_f3": None,
          "powers": []
        }

      # Mapear sensores específicos
      if sensor == "fase1":
        hourly_data[hour]["media_kw_f1"] = avg_power
      elif sensor == "fase2":
        hourly_data[hour]["media_kw_f2"] = avg_power
      elif sensor == "fase3":
        hourly_data[hour]["media_kw_f3"] = avg_power

      if avg_power is not None:
        hourly_data[hour]["powers"].append(avg_power)

    # Calcular média geral e formatar resultado
    results = []
    for hour in sorted(hourly_data.keys()):
      data = hourly_data[hour]
      powers = data["powers"]
      media_geral = round(sum(powers) / len(powers), 2) if powers else None

      results.append({
        "hora": data["hora"],
        "media_kw_f1": data["media_kw_f1"],
        "media_kw_f2": data["media_kw_f2"],
        "media_kw_f3": data["media_kw_f3"],
        "media_geral_kw": media_geral,
      })

    return results

  # =================================================================
  # Desbalanceamento de Fases
  # =================================================================
  def get_desbalanceamento(self, periodo: str = "ontem"):
    """
    Verifica se as fases estão carregadas de forma desigual (Ampere).

    Args:
      periodo: Período de tempo (ex: "ontem", "hoje")

    Returns:
      Lista de dicionários com avg_amp_f1, avg_amp_f2, avg_amp_f3, diferenca_max_amperes
    """
    logger.info(f"Calculating desbalanceamento for period: {periodo}")
    from_time, to_time = self._parse_period_to_time_range(periodo)
    endpoint = f"/analytics/{self.channel}/current_by_sensor"
    response = self._make_request(endpoint, params={"from_time": from_time, "to_time": to_time})

    # Organizar dados por fase específica
    currents: dict[str, Optional[float]] = {
      "avg_amp_f1": None,
      "avg_amp_f2": None,
      "avg_amp_f3": None,
    }

    for item in response.get("results", []):
      sensor = item["sensor"]
      avg_current = item["avg_current"]

      if sensor == "fase1":
        currents["avg_amp_f1"] = avg_current
      elif sensor == "fase2":
        currents["avg_amp_f2"] = avg_current
      elif sensor == "fase3":
        currents["avg_amp_f3"] = avg_current

    # Calcular diferença máxima
    valid_currents = [v for v in currents.values() if v is not None]
    if valid_currents:
      max_amp = max(valid_currents)
      min_amp = min(valid_currents)
      diferenca = round(max_amp - min_amp, 2)
    else:
      diferenca = 0.0

    # Substituir None por 0.0 para compatibilidade
    for key in currents:
      if currents[key] is None:
        currents[key] = 0.0

    currents["diferenca_max_amperes"] = diferenca

    return [currents]

  # =================================================================
  # Detecção de Anomalias (Voltagem)
  # =================================================================
  def get_anomalias_voltagem(
    self,
    periodo: str = "ultimos_7_dias",
    limite_inf: float = 115,
    limite_sup: float = 132
  ):
    """
    Retorna lista de eventos onde a voltagem saiu da zona segura.

    Também calcula a % de desvio em relação aos 220V nominais.

    Args:
      periodo: Período de tempo (ex: "ultimos_7_dias")
      limite_inf: Limite inferior de voltagem (padrão: 198V)
      limite_sup: Limite superior de voltagem (padrão: 242V)

    Returns:
      Lista de dicionários com timestamp, sensor, voltage, tipo, desvio_pct
    """
    logger.info(f"Calculating anomalias de voltagem for period: {periodo}")
    from_time, to_time = self._parse_period_to_time_range(periodo)
    endpoint = f"/analytics/{self.channel}/voltage_anomalies"
    params = {
      "from_time": from_time,
      "to_time": to_time,
      "lower_limit": limite_inf,
      "upper_limit": limite_sup,
      "nominal_voltage": 127,
    }
    response = self._make_request(endpoint, params=params)

    # Renomear campos de inglês para português
    results = []
    for item in response.get("results", []):
      # Traduzir tipo de anomalia
      tipo = "ALTA" if item["anomaly_type"] == "HIGH" else "BAIXA"

      results.append({
        "timestamp": item["timestamp"],
        "sensor": item["sensor"],
        "voltage": item["voltage"],
        "tipo": tipo,
        "desvio_pct": item["deviation_pct"],
      })

    return results
