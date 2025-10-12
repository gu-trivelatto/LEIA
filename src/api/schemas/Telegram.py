from pydantic import RootModel


class TelegramRawUpdate(RootModel[dict]):
  pass
    