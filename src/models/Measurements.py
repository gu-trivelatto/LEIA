import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Float, DateTime

from src.models.Base import Base


class Measurements(Base):
  __tablename__ = "measurements"
  id: Mapped[int] = mapped_column(
    Integer, primary_key=True, autoincrement=True
  )
  device_id: Mapped[str] = mapped_column(String)
  timestamp: Mapped[datetime.datetime] = mapped_column(DateTime)
  voltage: Mapped[float] = mapped_column(Float)
  current: Mapped[float] = mapped_column(Float)
  active_power: Mapped[float] = mapped_column(Float)
  reactive_power: Mapped[float] = mapped_column(Float)
  apparent_power: Mapped[float] = mapped_column(Float)
  power_factor: Mapped[float] = mapped_column(Float)
  energy_consumption: Mapped[float] = mapped_column(Float)
  frequency: Mapped[float] = mapped_column(Float)
  temperature: Mapped[float] = mapped_column(Float)
