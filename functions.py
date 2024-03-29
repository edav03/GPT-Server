import json
from dotenv import load_dotenv
from urllib.parse import unquote
import requests
import os
from openai import OpenAI
from prompts import assistant_instructions
from email.message import EmailMessage
import ssl
import smtplib

load_dotenv()
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
email_sender = os.environ["EMAIL_SENDER"]
email_password = os.environ["EMAIL_PASSWORD"]
email_developer = os.environ["EMAIL_DEVELOPER"]
email_clara = os.environ["EMAIL_RECEIVER2"]
email_receiver_list = [os.environ["EMAIL_RECEIVER"], email_clara, email_developer]

# Init OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

# Create or load assistant
def create_assistant(client):
  assistant_file_path = 'assistant.json'

  # If there is an assistant.json file already, then load that assistant
  if os.path.exists(assistant_file_path):
    with open(assistant_file_path, 'r') as file:
      assistant_data = json.load(file)
      assistant_id = assistant_data['assistant_id']
      print(f"Loaded existing assistant ID: {assistant_id}")
  else:
    # If no assistant.json is present, create a new assistant using the below specifications

    # To change the knowledge document, modifiy the file name below to match your document
    # If you want to add multiple files, paste this function into ChatGPT and ask for it to add support for multiple files
    file = client.files.create(file=open("knowledge.pdf", "rb"),
                               purpose='assistants')

    assistant = client.beta.assistants.create(
        # Getting assistant prompt from "prompts.py" file, edit on left panel if you want to change the prompt
        instructions=assistant_instructions,
        model="gpt-4-1106-preview",
        tools=[
            {
                "type": "retrieval"  # This adds the knowledge base as a tool
            },
            {
              "type": "function",  # This adds the setAppointment() as a tool
              "function": {
                  "name": "setAppointment",
                  "description": "Confirma la reserva una cita",
                  "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                          "type": "string",
                          "description": "Nombre del usuario"
                        },
                        "day": {
                          "type": "string",
                          "description": "Dia que tendrá lugar la cita"
                        },
                        "hour": {
                          "type": "string",
                          "description": "Hora que tendrá lugar la cita"
                        },
                        "phone":{
                          "type": "string",
                          "description": "Numero de telefono del usuario"
                        },
                        "summary":{
                          "type": "string",
                          "description": "Resumen de la conversación en español"
                        }
                    },
                    "required": ["name", "day", "hour", "phone", "summary"]
                  }
              }
            },
        ],
        file_ids=[file.id])

    # Create a new assistant.json file to load on future runs
    with open(assistant_file_path, 'w') as file:
      json.dump({'assistant_id': assistant.id}, file)
      print(f"Created a new assistant and saved the ID: {assistant.id}")

    assistant_id = assistant.id

  return assistant_id

def write_data_to_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)

def getFileIds(files):
  # List to store the uploaded file IDs
  file_ids = []

  # Upload each file and store its ID
  for file_name in files:
      with open(file_name, 'rb') as file:
          uploaded_file = client.files.create(file=file, purpose='assistants')
          file_ids.append(uploaded_file.id)
          print(f"File '{file_name}' uploaded with ID: {uploaded_file.id}")

  return file_ids

def setAppointment(name, day, hour, phone, summary):
  try:
    subject = "Cita"
    body = f'Nueva cita a las {hour} horas el dia {day}, a nombre de {name}.\nNumero tlf: {phone}.\nResumen de la conversacion: {summary}'
    decoded_body = unquote(body);

    # If you need to encode for some other reason (e.g., writing to a file, sending over a network)
    encoded_body = decoded_body.encode('utf-8')

    # Decoding (if you have an encoded byte string and want to get a regular string)
    decoded_again = encoded_body.decode('utf-8')

    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver_list
    em['Subject'] = subject
    em.set_content(decoded_again, charset='utf-8')

    context = ssl.create_default_context()


    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
      smtp.login(email_sender, email_password)
      smtp.sendmail(email_sender, email_receiver_list, em.as_string().encode('utf-8'))

    return "Cita reservada"
  except Exception as e:
        print(f"An error occurred: {e}")
        return "Error al reservar la cita"

def emailTheError(errorMessage, assistantId):
  try:
    subject = "Script Error"
    body = f'{errorMessage}\n{assistantId}'

    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = [email_developer, email_clara]
    em['Subject'] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    print(f"Mensaje email: {body}");

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
      smtp.login(email_sender, email_password)
      smtp.sendmail(email_sender, email_receiver_list, em.as_string())

    return "Cita reservada"
  except Exception as e:
        print(f"An error occurred: {e}")
        return "Error al reservar la cita"