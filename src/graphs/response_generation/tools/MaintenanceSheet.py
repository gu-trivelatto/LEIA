import logging
from typing import Annotated, Literal, List, Dict, Any

from src.core.config import settings
from langchain_core.tools import tool
from src.services.GoogleService import get_sheets_service

logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES ---
SPREADSHEET_ID = settings.google_sheets.SHEET_ID
SHEET_NAME = "Sheet1"
HEADERS = ['Data', 'Equipamento', 'Descrição', 'Custo', 'Profissional', 'Responsável', 'Agendada']
DATA_START_ROW = 3
DATA_RANGE = f"{SHEET_NAME}!B{DATA_START_ROW}:H"
INSERT_RANGE = f"{SHEET_NAME}!B:H"

# --- FUNÇÕES AUXILIARES ---

def _fetch_all_records(service) -> List[Dict[str, str]]:
  """Busca todos os registros."""
  try:
    result = service.spreadsheets().values().get(
      spreadsheetId=SPREADSHEET_ID, range=DATA_RANGE
    ).execute()
    rows = result.get('values', [])

    structured_data = []
    for row in rows:
      padded_row = row + [""] * (len(HEADERS) - len(row))
      record = {header: val for header, val in zip(HEADERS, padded_row)}
      structured_data.append(record)
    return structured_data
  except Exception as e:
    logger.error(f"Erro ao buscar registros: {e}")
    return []

def _format_as_markdown_table(records: List[Dict[str, Any]]) -> str:
  """Converte lista em tabela Markdown."""
  if not records: return "Nenhum registro encontrado."

  markdown = "| " + " | ".join(HEADERS) + " |\n"
  markdown += "| " + " | ".join(["---"] * len(HEADERS)) + " |\n"

  for rec in records:
    row_values = [str(rec.get(h, "")) for h in HEADERS]
    markdown += "| " + " | ".join(row_values) + " |\n"
  return markdown

def _filter_by_device(records: List[Dict], device_query: str) -> List[Dict]:
  """Filtra por equipamento."""
  query = device_query.lower().strip()
  return [r for r in records if query in r.get('Equipamento', '').lower()]

# --- TOOL PRINCIPAL ---

@tool(
  name_or_callable="MaintenanceSheet",
  description="""
  Gerenciador da Planilha de Manutenção.
  
  Ações disponíveis:
  - 'get_last_maintenances': Histórico geral.
  - 'get_device_maintenances': Histórico por equipamento.
  - 'get_scheduled_maintenances': Lista manutenções futuras.
  - 'insert_maintenance_record': Cria novo registro.
  - 'update_maintenance_status': Atualiza uma manutenção agendada para realizada (define custo e tira o status de agendada).
  
  Para ATUALIZAR ('update_maintenance_status'):
  - É obrigatório fornecer 'device' e 'date' para localizar o registro.
  - Forneça 'price' para o valor final pago.
  """
)
async def MaintenanceSheet(
  action: Annotated[
    Literal[
      "get_last_maintenances",
      "get_device_maintenances",
      "get_scheduled_maintenances",
      "insert_maintenance_record",
      "update_maintenance_status",
    ],
    "A ação a ser realizada na planilha.",
  ],
  date: Annotated[str, "Data (DD/MM/YYYY). Obrigatório para inserts e updates."],
  device: Annotated[str, "Equipamento. Obrigatório para inserts, updates e buscas específicas."] = "",
  details: Annotated[str, "Descrição do serviço (usado no insert)."] = "",
  worker: Annotated[str, "Nome do técnico (usado no insert)."] = "",
  responsible: Annotated[str, "Nome do responsável (usado no insert)."] = "",
  price: Annotated[float, "Custo final do serviço. Usado no insert e no update."] = 0.0,
  scheduled: Annotated[bool, "True para agendar. No update, isso é ignorado pois o status mudará para 'Não'."] = False,
  limit: Annotated[int, "Qtd de registros (apenas para get_last_maintenances)."] = 5,
) -> str:
  
  logger.info(f"MaintenanceSheet called: action={action}, device={device}, date={date}")
  
  sheets_service = get_sheets_service()
  if not sheets_service:
    return "Erro Técnico: Serviço Google Sheets indisponível."

  try:
    # --- LÓGICA DE INSERÇÃO ---
    if action == "insert_maintenance_record":
      if not device or not responsible or not date:
        return "Erro: 'device', 'responsible' e 'date' são obrigatórios."

      formatted_price = f"R$ {price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
      scheduled_str = "Sim" if scheduled else "Não"
      
      new_row = [date, device, details, formatted_price, worker, responsible, scheduled_str]

      sheets_service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=INSERT_RANGE,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={'values': [new_row]}
      ).execute()

      return f"✅ Sucesso: Manutenção para '{device}' registrada."

    # --- LÓGICA DE ATUALIZAÇÃO (UPDATE) ---
    elif action == "update_maintenance_status":
      if not device or not date:
        return "Erro: Para atualizar, informe o 'device' e a 'date' do agendamento."

      all_records = _fetch_all_records(sheets_service)
      
      target_index = -1
      found_record = None

      # Procura registro: Dispositivo + Data + (Preferência por Agendada='Sim')
      for i, rec in enumerate(all_records):
        rec_device = rec.get('Equipamento', '').lower()
        rec_date = rec.get('Data', '')
        rec_scheduled = rec.get('Agendada', '').lower()
        
        if (device.lower() in rec_device) and (date == rec_date):
          target_index = i
          found_record = rec
          if rec_scheduled == 'sim': 
            break 

      if target_index == -1 or found_record is None:
        return f"❌ Não encontrei nenhum registro para '{device}' na data {date}."

      # Calcula a linha
      sheet_row = DATA_START_ROW + target_index
      
      formatted_price = f"R$ {price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
      
      # Atualiza Custo (Col E)
      sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!E{sheet_row}",
        valueInputOption="USER_ENTERED",
        body={'values': [[formatted_price]]}
      ).execute()
      
      # Atualiza Agendada para 'Não' (Col H)
      sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!H{sheet_row}",
        valueInputOption="USER_ENTERED",
        body={'values': [["Não"]]}
      ).execute()

      return f"✅ Atualizado: Manutenção de '{device}' ({date}) foi concluída. Valor atualizado para {formatted_price}."

    # --- LÓGICA DE LEITURA ---
    all_records = _fetch_all_records(sheets_service)
    if not all_records: return "A planilha está vazia."

    if action == "get_last_maintenances":
      safe_limit = max(1, limit)
      return f"Últimos {len(all_records[-safe_limit:])} registros:\n\n{_format_as_markdown_table(all_records[-safe_limit:])}"

    elif action == "get_device_maintenances":
      if not device: return "⚠️ Especifique o equipamento."
      filtered = _filter_by_device(all_records, device)
      if not filtered: return f"Nenhum registro para '{device}'."
      return f"Histórico de **{device}**:\n\n{_format_as_markdown_table(filtered)}"

    elif action == "get_scheduled_maintenances":
      scheduled_list = [r for r in all_records if r.get('Agendada', '').strip().lower() == 'sim']
      if not scheduled_list: return "Nenhum agendamento encontrado."
      
      if device:
        scheduled_list = _filter_by_device(scheduled_list, device)
        if not scheduled_list: return f"Nenhum agendamento para '{device}'."
      
      return f"Manutenções agendadas:\n\n{_format_as_markdown_table(scheduled_list)}"

    else:
      return f"Ação '{action}' desconhecida."

  except Exception as e:
    logger.error(f"Erro na MaintenanceSheet: {e}", exc_info=True)
    return f"Ocorreu um erro: {str(e)}"