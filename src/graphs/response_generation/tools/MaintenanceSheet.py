import logging
from typing import Annotated, Literal
import json

from core.config import settings
from langchain_core.tools import tool
from src.services.GoogleService import get_sheets_service 

logger = logging.getLogger(__name__)

SPREADSHEET_ID = settings.google_sheets.SHEET_ID
SHEET_NAME = "Sheet1" 
DATA_RANGE = f"{SHEET_NAME}!B3:H"
INSERT_RANGE = f"{SHEET_NAME}!B:H" 
HEADERS = ['Data', 'Equipamento', 'Descrição', 'Custo', 'Profissional', 'Responsável', 'Agendada']
# ---------------------------------------------


@tool(
  name_or_callable="MaintenanceSheet",
  description="""Você deve chamar essa função caso o usuário solicite informações
  sobre a planilha de manutenção, como detalhes de manutenção, histórico de
  manutenção, ou qualquer informação relacionada à manutenção dos equipamentos.
  Esta função também é responsável por inserir novos registros de manutenção
  na planilha quando solicitado pelo usuário. Para criação, se a manutenção for
  agendada, não é necessário informar preço nem trabalhador.""",
)
async def MaintenanceSheet(
  action: Annotated[
    Literal[
      "get_last_maintenances",
      "get_maintenances_by_device",
      "get_device_maintenances",
      "insert_maintenance_record",
    ],
    "Este campo identifica a ação específica que você deseja realizar.",
  ],
  date: Annotated[
    str,
    """A data da manutenção no formato 'DD/MM/YYYY'. Use este campo ao inserir
    um novo registro de manutenção.""",
  ] = "",
  device: Annotated[
    str,
    "O nome ou identificador do dispositivo relacionado à manutenção. Use este campo ao inserir ou consultar registros de manutenção específicos de um dispositivo.",
  ] = "",
  details: Annotated[
    str,
    "Detalhes ou descrição da manutenção realizada. Use este campo ao inserir um novo registro de manutenção.",
  ] = "",
  worker: Annotated[
    str,
    "O nome do trabalhador responsável pela manutenção. Use este campo ao inserir um novo registro de manutenção.",
  ] = "",
  responsible: Annotated[
    str,
    "O nome do responsável pela manutenção. Use este campo ao inserir um novo registro de manutenção.",
  ] = "",
  price: Annotated[
    float,
    "O custo associado à manutenção. Use este campo ao inserir um novo registro de manutenção.",
  ] = 0.0,
  scheduled: Annotated[
    bool,
    "Indica se a manutenção foi agendada. Use este campo ao inserir um novo registro de manutenção.",
  ] = False,
) -> str:
  """Implementa as funcionalidades de leitura e escrita na planilha de manutenção."""
  
  sheets_service = get_sheets_service()

  if sheets_service is None:
    logger.error("Google Sheets service is not initialized.")
    return "Erro: o serviço do Google Sheets não está disponível no momento."
  
  sheet = sheets_service.spreadsheets()
  
  logger.debug(f"Selected action: {action}")

  try:
    if action == "insert_maintenance_record":
      if not responsible:
        return "Erro: O responsável é obrigatório para inserir um registro de manutenção."
      
      logger.debug(f"New record: date={date}, device={device}, details={details}, price={price}, worker={worker}, responsible={responsible}, scheduled={scheduled}")

      formatted_price = f"R$ {price:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
      scheduled_text = "Sim" if scheduled else "Não"
      
      new_record = [
        f"{date}",
        device,
        details,
        formatted_price,
        worker,
        responsible,
        scheduled_text
      ]

      result = sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=INSERT_RANGE,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={'values': [new_record]}
      ).execute()

      logger.debug(f"Insert result: {result}")

      return f"Registro de manutenção para '{device}' inserido com sucesso na linha {result.get('updates').get('updatedRange').split('!')[1].split(':')[0].replace(SHEET_NAME, '')}."

    else:
      result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID, 
        range=DATA_RANGE,
      ).execute()
      
      values = result.get('values', [])
      
      if not values:
        logger.info("No maintenance records found.")
        return "Não foram encontrados registros de manutenção."
      
      records = []
      for row in values:
        if len(row) >= len(HEADERS):
          record = dict(zip(HEADERS, row[:len(HEADERS)]))
          records.append(record)

      if action == "get_last_maintenances":
        last_records = records[-5:]
        
        logger.debug(f"Last records: {last_records}")
        
        response = f"Os últimos 5 registros de manutenção são:\n"
        for r in last_records:
          response += f"- {r['Equipamento']} no dia {r['Data']} | {r['Descrição']} | Responsável: {r['Responsável']} | Profissional: {r['Profissional']} | {r['Custo']} | Agendada? {r['Agendada']}\n"
        
        return response

      elif action == "get_maintenances_by_device":
        if not records:
          return "Não há registros para agrupar."

        grouped_maintenances = {}
        
        for record in records:
          device_name = record.get('Equipamento')
          maintenance_date = record.get('Data')
          
          if device_name and maintenance_date:
            if device_name not in grouped_maintenances:
              grouped_maintenances[device_name] = []
            
            grouped_maintenances[device_name].append(maintenance_date)
            
        logger.debug(f"Grouped maintenances: {grouped_maintenances}")
        
        maintenance_list = []
        for device, dates in grouped_maintenances.items():
          maintenance_list.append({
            "nome": device,
            "data_manutencao": dates
          })

        return json.dumps(maintenance_list, ensure_ascii=False, indent=2)
      
      elif action == "get_device_maintenances":
        if not device:
          logger.debug("No device specified, listing unique devices.")
          
          unique_devices = sorted(list(set(r.get('Equipamento') for r in records if r.get('Equipamento'))))
          
          logger.debug(f"Unique devices: {unique_devices}")
          
          if not unique_devices:
              return "Não foi possível identificar equipamentos únicos para consulta."

          response = "O nome do dispositivo não foi fornecido. Dispositivos disponíveis para consulta:\n- "
          response += "\n- ".join(unique_devices)
          
          return response
        
        device_name = device.strip().lower()
        
        filtered_records = [
          r for r in records 
          if device_name in r.get('Equipamento', '').lower()
        ]
        
        logger.debug(f"Filtered records for device '{device}': {filtered_records}")

        if not filtered_records:
          return f"Nenhum registro encontrado para o equipamento '{device}'."
        
        response = f"Histórico de manutenção para o equipamento '{device}':\n"
        for r in filtered_records:
          response += (
            f"- Data: {r.get('Data', 'N/A')} | "
            f"Descrição: {r.get('Descrição', 'N/A')} | "
            f"Custo: {r.get('Custo', 'N/A')} | "
            f"Profissional: {r.get('Profissional', 'N/A')} | "
            f"Agendada: {r.get('Agendada', 'N/A')}\n"
          )
        
        return response
            
      else:
        return "Ação não reconhecida. Use 'get_last_maintenances', 'get_maintenances_by_device', 'get_device_maintenances' ou 'insert_maintenance_record'."

  except Exception as e:
    logger.error(f"Erro ao interagir com o Google Sheets: {e}", exc_info=True)
    return f"Erro interno ao processar a solicitação: {e}"