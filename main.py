import json
import os
import time
from flask import Flask, request, jsonify
import openai
from openai import OpenAI
import functions

# Check OpenAI version compatibility
from packaging import version

required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
if current_version < required_version:
  raise ValueError(
      f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1"
  )
else:
  print("OpenAI version is compatible.")

# Create Flask app
app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Create or load assistant
assistant_id = functions.create_assistant(client)  # this function comes from "functions.py"

@app.route('/', methods=['GET'])
def checkServer():
  return jsonify({"status": 'Server running'})


# Start conversation thread
@app.route('/start', methods=['POST'])
def start_conversation():
  data = request.json
  general_info = data.get('general_info')

  print("Starting a new conversation...")
  thread = client.beta.threads.create()
  print(f"New thread created with ID: {thread.id}")

  functions.write_data_to_file('prices_data.txt', general_info)
  fileIds = functions.getFileIds(['prices_data.txt'])

  # Add user context
  client.beta.threads.messages.create(thread_id=thread.id,
                                      role="user",
                                      content='Mi tienda mas cercana es QuickGold Granada (Puentezuelas)',
                                      file_ids=fileIds)

  print("Thread contextualized by user")
  return jsonify({"thread_id": thread.id})


# Generate response
@app.route('/chat', methods=['POST'])
def chat():
  data = request.json
  thread_id = data.get('thread_id')
  user_input = data.get('message', '')

  if not thread_id:
    print("Error: Missing thread_id")
    return jsonify({"error": "Missing thread_id"}), 400

  print(f"Received message: {user_input} for thread ID: {thread_id}")

  print("Add the user's message to the thread...")
  client.beta.threads.messages.create(thread_id=thread_id,
                                      role="user",
                                      content=user_input)

  print("Running the assistant...")
  run = client.beta.threads.runs.create(thread_id=thread_id,
                                        assistant_id=assistant_id)

  # Check if the Run requires action (function call)
  while True:
    run_status = client.beta.threads.runs.retrieve(thread_id=thread_id,
                                                   run_id=run.id)
    
    print(f"Run status: {run_status.status}")
    if run_status.status == 'completed':
      break
    elif run_status.status == 'requires_action':
      # Handle the function call
      for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
        if tool_call.function.name == "setAppointment":
          # Process appointment creation
          arguments = json.loads(tool_call.function.arguments)
          output = functions.setAppointment(arguments["name"], arguments["day"], arguments["hour"])
          client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id,
                                                       run_id=run.id,
                                                       tool_outputs=[{
                                                        "tool_call_id": tool_call.id,
                                                        "output": output
                                                       }])

      time.sleep(0.5)  # Wait for a second before checking again
                                        
  # Retrieve and return the latest message from the assistant
  message = client.beta.threads.messages.list(thread_id=thread_id)
  response = message.data[0].content[0].text.value

  print(f"Assistant response: {response}")
  return jsonify({"response": response})


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080)