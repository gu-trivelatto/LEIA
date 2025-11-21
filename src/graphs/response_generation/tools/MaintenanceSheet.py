import logging
from typing import Annotated, Literal, List, Dict, Any

from src.core.config import settings 
from langchain_core.tools import tool
from src.services.GoogleService import get_sheets_service

logger = logging.getLogger(__name__)

SPREADSHEET_ID = settings.google_sheets.SHEET_ID
SHEET_NAME = "Sheet1"
HEADERS = ['Data', 'Equipamento', 'Descrição', 'Custo', 'Profissional', 'Responsável', 'Agendada']
DATA_RANGE = f"{SHEET_NAME}!B3:H"
INSERT_RANGE = f"{SHEET_NAME}!B:H"

# --- FUNÇÕES AUXILIARES ---

def _fetch_all_records(service) -> List[Dict[str, str]]:
  """Busca e estrutura todos os dados da planilha."""
  try:
    result = service.spreadsheets().values().get(
      spreadsheetId=SPREADSHEET_ID, range=DATA_RANGE
    ).execute()
    rows = result.get('values', [])
    
    structured_data = []
    for row in rows:
      # Preenche colunas faltantes para evitar erros de index
      padded_row = row + [""] * (len(HEADERS) - len(row))
      record = {header: val for header, val in zip(HEADERS, padded_row)}
      structured_data.append(record)
        
    return structured_data
  except Exception as e:
    logger.error(f"Erro ao buscar registros: {e}")
    return []

def _format_as_markdown_table(records: List[Dict[str, Any]]) -> str:
  """Converte lista de dicts em tabela Markdown."""
  if not records:
    return "Nenhum registro encontrado."
  
  markdown = "| " + " | ".join(HEADERS) + " |\n"
  markdown += "| " + " | ".join(["---"] * len(HEADERS)) + " |\n"
  
  for rec in records:
    row_values = [str(rec.get(h, "")) for h in HEADERS]
    markdown += "| " + " | ".join(row_values) + " |\n"
      
  return markdown

def _filter_by_device(records: List[Dict], device_query: str) -> List[Dict]:
  """Filtra registros pelo nome do equipamento (case insensitive)."""
  query = device_query.lower().strip()
  return [r for r in records if query in r.get('Equipamento', '').lower()]

# --- TOOL PRINCIPAL ---

@tool(
  name_or_callable="MaintenanceSheet",
  description="""
  Gerenciador da Planilha de Manutenção.
  
  Ações disponíveis:
  - 'get_last_maintenances': Histórico geral (use 'limit' para definir a qtd).
  - 'get_device_maintenances': Histórico completo de um equipamento.
  - 'get_scheduled_maintenances': Lista apenas manutenções futuras/agendadas.
  - 'insert_maintenance_record': Insere novo registro.
  
  Notas:
  - Para buscar agendamentos de um item específico, use 'get_scheduled_maintenances' + 'device'.
  """
)
async def MaintenanceSheet(
  action: Annotated[
    Literal[
      "get_last_maintenances",
      "get_device_maintenances",
      "get_scheduled_maintenances",
      "insert_maintenance_record",
    ],
    "A ação a ser realizada na planilha.",
  ],
  date: Annotated[str, "Data (DD/MM/YYYY). Obrigatório p/ inserir."] = "",
  device: Annotated[str, "Equipamento. Obrigatório p/ busca específica ou insert."] = "",
  details: Annotated[str, "Descrição do serviço."] = "",
  worker: Annotated[str, "Nome do técnico."] = "",
  responsible: Annotated[str, "Nome do responsável interno."] = "",
  price: Annotated[float, "Custo (apenas números)."] = 0.0,
  scheduled: Annotated[bool, "True para agendamento futuro, False se já realizado."] = False,
  limit: Annotated[int, "Qtd de registros (apenas para get_last_maintenances)."] = 5,
) -> str:
    
  logger.info(f"MaintenanceSheet called: action={action}, device={device}")
  
  sheets_service = get_sheets_service()
  if not sheets_service:
    return "Erro Técnico: Serviço Google Sheets indisponível."

  try:
    # --- ESCRITA ---
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

      return f"✅ Sucesso: Manutenção para '{device}' registrada (Data: {date})."

    # --- LEITURA ---
    all_records = _fetch_all_records(sheets_service)
    if not all_records: return "A planilha está vazia."

    if action == "get_last_maintenances":
      safe_limit = max(1, limit)
      last_records = all_records[-safe_limit:]
      return f"Últimos {len(last_records)} registros:\n\n{_format_as_markdown_table(last_records)}"

    elif action == "get_device_maintenances":
      if not device:
        unique = sorted(list(set(r['Equipamento'] for r in all_records if r['Equipamento'])))
        return f"⚠️ Especifique o equipamento. Opções:\n" + "\n".join([f"- {d}" for d in unique])
      
      filtered = _filter_by_device(all_records, device)
      if not filtered: return f"Nenhum registro para '{device}'."
      return f"Histórico completo de **{device}**:\n\n{_format_as_markdown_table(filtered)}"

    elif action == "get_scheduled_maintenances":
      scheduled_list = [
        r for r in all_records 
        if r.get('Agendada', '').strip().lower() == 'sim'
      ]

      if not scheduled_list:
        return "Não há nenhuma manutenção agendada no momento."

      if device:
        scheduled_list = _filter_by_device(scheduled_list, device)
        if not scheduled_list:
          return f"Não há manutenções agendadas especificamente para '{device}'."
        msg_prefix = f"Manutenções agendadas para **{device}**:"
      else:
        msg_prefix = "Todas as manutenções agendadas:"

      return f"{msg_prefix}\n\n{_format_as_markdown_table(scheduled_list)}"

    else:
      return f"Ação '{action}' desconhecida."

  except Exception as e:
    logger.error(f"Erro na MaintenanceSheet: {e}", exc_info=True)
    return f"Ocorreu um erro: {str(e)}"