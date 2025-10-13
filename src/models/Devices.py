from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String

from src.models.Base import Base


class Devices(Base):
  __tablename__ = "devices"
  id: Mapped[int] = mapped_column(
    Integer, primary_key=True, autoincrement=True
  )
  type: Mapped[str] = mapped_column(String)
  name: Mapped[str] = mapped_column(String)
