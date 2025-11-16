import logging

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

from src.core.config import settings

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheets_service():
    """Cria e retorna o objeto de serviço para a API do Google Sheets usando uma Conta de Serviço."""
    try:
        creds = Credentials.from_service_account_file(
            settings.google_sheets.SERVICE_ACCOUNT_KEY_PATH, scopes=SCOPES)
        
        service = build('sheets', 'v4', credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Error authenticating Google Service Account: {e}")
        return None
