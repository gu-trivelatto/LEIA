import logging

from datetime import datetime, timedelta
from typing import Literal, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import String, select, func
from src.models.Devices import (
  Devices,
)
from src.models.Measurements import (
  Measurements,
)
from src.core.readings_database import get_db_session

logger = logging.getLogger(__name__)


async def get_consumption_distribution(
  period: Literal["yesterday", "last_week", "last_month"]
) -> dict[str, float | str]:
  """
  Retorna o consumo total de energia por categoria em um determinado período.
  """
  logger.info(f"Fetching consumption distribution for period: {period}")
  db_session: None | AsyncSession = None
  try:
    # Define o intervalo de datas conforme o período
    # TODO usar a data atual quando tivermos dados atualizados
    end = datetime(2025, 9, 15)
    if period == "last_month":
      start = (end - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "last_week":
      start = (end - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
      # Fallback leva todos para ontem
      start = (end - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
      end = start.replace(hour=23, minute=59, second=59)

    db_session = get_db_session()
    stmt = (
      select(Devices.type, func.sum(Measurements.active_power).label("total_active_power"))
      .join(Measurements, Devices.id == Measurements.device_id)
      .where(Measurements.timestamp.between(start, end))
      .group_by(Devices.type)
    )
    rows = (await db_session.execute(stmt)).fetchall()
    
    if not rows:
      logger.info("No consumption data found for the given period.")
      return {"error": "Não há dados disponíveis para o período informado."}
    
    logger.info(f"{len(rows)} consumption records found.")

    # Retorna como dicionário: {tipo: consumo_total}
    return {row.type: row.total_active_power / 60.0 for row in rows}
  except Exception as e:
    logger.error(f"Erro ao buscar distribuição de consumo: {e}")
    return {"error": "Não foi possível buscar a distribuição de consumo."}
  
async def get_daily_consumption(
  period: Literal["last_week", "last_month", "last_year"]
) -> dict[str, list[tuple[str, float]] | str]:
  logger.info(f"Fetching daily consumption for period: {period}")
  try:
    # TODO usar a data atual quando tivermos dados atualizados
    end = datetime(2025, 9, 15)
    if period == "last_month":
      delta = 30
    elif period == "last_year":
      delta = 365
    else:
      # Fallback leva todos para a última semana
      delta = 7
    start = (end - timedelta(days=delta)).replace(hour=0, minute=0, second=0, microsecond=0)
    db_session = get_db_session()
    stmt = (
      select(
        func.cast(func.date_trunc('day', Measurements.timestamp), String).label("consumption_day"),
        func.sum(Measurements.active_power / 60.0).label("total_kwh")
      )
      .where(Measurements.timestamp.between(start, end))
      .group_by("consumption_day")
      .order_by("consumption_day")
    )
    rows = (await db_session.execute(stmt)).fetchall()
    if not rows:
      logger.info("No daily consumption data found for the given period.")
      return {"error": "Não há dados disponíveis para o período informado."}
    logger.info(f"{len(rows)} daily consumption records found.")
    data = [tuple(row) for row in rows]
    return {"data": data}
  except Exception as e:
    logger.error(f"Erro ao buscar consumo diário: {e}")
    return {"error": "Não foi possível buscar o consumo diário."}

async def get_power_readings_by_device(
  period: Literal["yesterday", "last_week"]
) -> dict[str, list[tuple[str, float]] | str]:
  logger.info(f"Fetching power readings by device for period: {period}")
  try:
    # TODO usar a data atual quando tivermos dados atualizados
    end = datetime(2025, 9, 15)
    if period == "last_week":
      start = (end - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
      # Fallback leva todos para ontem
      start = (end - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
      end = start.replace(hour=23, minute=59, second=59)
    db_session = get_db_session()
    stmt = (
      select(Devices.name, Measurements.active_power)
      .join(Measurements, Devices.id == Measurements.device_id)
      .where(Measurements.timestamp.between(start, end))
    )
    rows = (await db_session.execute(stmt)).fetchall()
    if not rows:
      logger.info("No power readings found for the given period.")
      return {"error": "Não há dados disponíveis para o período informado."}
    logger.info(f"{len(rows)} power readings found.")
    data = [tuple(row) for row in rows]
    return {"data": data}
  except Exception as e:
    logger.error(f"Erro ao buscar leituras de potência: {e}")
    return {"error": "Não foi possível buscar as leituras de potência."}

async def get_power_factor_analysis(
  device_id: int,
  period: Literal["last_week", "last_month"]
) -> dict[str, list[tuple[str, float, str]] | str]:
  logger.info(f"Fetching power factor analysis for device_id: {device_id}, period: {period}")
  try:
    # TODO usar a data atual quando tivermos dados atualizados
    end = datetime(2025, 9, 15)
    if period == "last_month":
      delta = 30
    else:
      # Fallback leva todos para a última semana
      delta = 7
    start = (end - timedelta(days=delta)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = end
    db_session = get_db_session()
    stmt = (
      select(Measurements.active_power, Measurements.power_factor, Devices.name)
      .join(Devices, Devices.id == Measurements.device_id)
      .where(
        Measurements.device_id == device_id,
        Measurements.timestamp.between(start, end)
      )
    )
    rows = (await db_session.execute(stmt)).fetchall()
    if not rows:
      logger.info("No power factor analysis data found for the given device and period.")
      return {"error": "Não há dados disponíveis para o período informado."}
    logger.info(f"{len(rows)} power factor analysis records found.")
    data = [tuple(row) for row in rows]
    return {"data": data}
  except Exception as e:
    logger.error(f"Erro ao buscar análise do fator de potência: {e}")
    return {"error": "Não foi possível buscar a análise do fator de potência."}
