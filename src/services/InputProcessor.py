import logging
import base64
import io
from telegram import Message, Bot
from src.graphs.llm.model import create_groq_client
from src.core.config import settings
from src.graphs.response_generation.schemas.MainState import InputState
from src.core.prompt import PromptHandler

logger = logging.getLogger(__name__)
bot = Bot(token=settings.bot.TELEGRAM_TOKEN.get_secret_value())


async def download_file(file_id: str) -> bytearray:
  try:
    file = await bot.get_file(file_id)
    data = await file.download_as_bytearray()
    return data
  except Exception as e:
    logger.error(f"Error downloading file {file_id}: {e}")
    return bytearray()

def transcribe_audio(audio: bytearray) -> str:
  try:
    logger.info(f"Transcribing audio of size: {len(audio)} bytes")
    
    client = create_groq_client(settings.audio_model.API_KEY)
    audio_file = io.BytesIO(audio)
    audio_file.name = "audio.ogg"
    
    transcription = client.audio.transcriptions.create(
      file=audio_file,
      model=settings.audio_model.MODEL,
      prompt=PromptHandler().get_prompt(
        settings.audio_model.PROMPT_NAME
      ),
      response_format="verbose_json",
      language="pt",
      temperature=settings.audio_model.TEMPERATURE,
    )
    if not transcription or not transcription.text:
      raise ValueError("Transcription response is empty or malformed.")
    return "Transcrição de Áudio: " + transcription.text
  except Exception as e:
    logger.error(f"Error transcribing audio: {e}")
    return "Transcrição de Áudio: Não foi possível transcrever o áudio recebido. Ele pode ser vazio, estar corrompido ou mesmo protegido por senha."


def interpret_image(image: bytearray) -> str:
  try:
    logger.info(f"Interpreting image of size: {len(image)} bytes")
    logger.info(f"Encoding image to base64")
    
    base64_image = base64.b64encode(image).decode('utf-8')
    
    logger.info(f"Image encoded to base64, length: {len(base64_image)} characters")
    
    client = create_groq_client(settings.audio_model.API_KEY)
    completion = client.chat.completions.create(
      model=settings.omni_model.MODEL,
      messages=[
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": PromptHandler().get_prompt(
                settings.omni_model.PROMPT_NAME
              ),
            },
            {
              "type": "image_url",
              "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}",
              },
            },
          ]
        }
      ],
      temperature=settings.omni_model.TEMPERATURE,
      max_completion_tokens=settings.omni_model.MAX_COMPLETION_TOKENS,
      top_p=settings.omni_model.TOP_P,
      stream=False,
      stop=None,
    )

    if not completion or not completion.choices or not completion.choices[0].message or not completion.choices[0].message.content:
      raise ValueError("Completion response is empty or malformed.")
    return "Descrição de Imagem: " + completion.choices[0].message.content
  except Exception as e:
    logger.error(f"Error interpreting image: {e}")
    return "Descrição de Imagem: Não foi possível interpretar a imagem recebida. Ela pode ser vazia, estar corrompida ou mesmo protegida por senha."


async def process_input(message: Message) -> InputState:
  chat_id = message.chat.id
  message_id = message.message_id
  phone_number = message.contact.phone_number if message.contact else ""
  if message.text:
    chat_input = message.text
  elif message.audio:
    audio = await download_file(message.audio.file_id)
    chat_input = transcribe_audio(audio)
  elif message.voice:
    voice = await download_file(message.voice.file_id)
    chat_input = transcribe_audio(voice)
  elif message.photo:
    photo = await download_file(message.photo[-1].file_id)
    chat_input = interpret_image(photo)
  else:
    chat_input = "O usuário enviou um tipo de mensagem não suportado. Informe que apenas mensagens de texto, áudio e fotos são aceitas."
    
  if message.caption:
    chat_input = f"{chat_input}\nLegenda: {message.caption}"
  
  user_name = "Desconhecido"
  if message.from_user and message.from_user.first_name:
    user_name = message.from_user.first_name
    if message.from_user.last_name:
      user_name += f" {message.from_user.last_name}" 
    
  return InputState(
    chat_input=chat_input,
    chat_id=chat_id,
    message_id=message_id,
    phone_number=phone_number,
    user_name=user_name,
  )
