import json
from dotenv import load_dotenv
import requests
import os
from openai import OpenAI
from prompts import assistant_instructions

load_dotenv()
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

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
      print("Loaded existing assistant ID.")
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
            }
        ],
        file_ids=[file.id])

    # Create a new assistant.json file to load on future runs
    with open(assistant_file_path, 'w') as file:
      json.dump({'assistant_id': assistant.id}, file)
      print("Created a new assistant and saved the ID.")

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