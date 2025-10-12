import logging
import sys

from colorama import Fore, Style, init

init(autoreset=True)


class ColorFormatter(logging.Formatter):
  COLORS = {
    logging.DEBUG: Fore.BLUE,
    logging.INFO: Fore.GREEN,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
  }

  def format(self, record):
    log_color = self.COLORS.get(record.levelno, "")

    message = super().format(record)

    return (
      f"[{Fore.CYAN}{self.formatTime(record, self.datefmt)}{Style.RESET_ALL}] "
      f"[{log_color}{record.levelname:<8}{Style.RESET_ALL}] "  # Usa <8 para alinhar os níveis
      f"[{Fore.YELLOW}{record.module:<20}{Style.RESET_ALL}] "
      f"{message}"
    )


class SuppressDetachFilter(logging.Filter):
  def filter(self, record: logging.LogRecord) -> bool:
    if "Failed to detach context" in record.getMessage():
      return False  # não loga
    return True


def init_logging(
  level: str = "INFO"
):
  """Inicializa a configuração raiz do logging com o handler e formatter customizados."""
  handler = logging.StreamHandler(sys.stdout)

  formatter = ColorFormatter(datefmt="%Y-%m-%d %H:%M:%S UTC%z")
  handler.setFormatter(formatter)

  logging.basicConfig(
    level=level,
    handlers=[handler],
    force=True,
  )


def update_level(level: str = "INFO"):
  root_logger = logging.getLogger()
  root_logger.setLevel(level)
  logging.getLogger(__name__).info(f"Nível de log atualizado para {level}")
