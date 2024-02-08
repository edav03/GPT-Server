from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime, timedelta
import schedule
import time
import os

def shouldDeleteFile(file):
    # Assuming created_at is the Unix timestamp you have for the file
    created_at_timestamp = file

    # Convert Unix timestamp to datetime object for the file creation time
    created_at_datetime = datetime.fromtimestamp(created_at_timestamp)

    # Get the current datetime
    current_datetime = datetime.now()

    # Calculate the time difference
    time_difference = current_datetime - created_at_datetime

    # Check if the difference is greater than or equal to 3 hours
    if time_difference >= timedelta(hours=3):
        return True
    else:
        return False

def scanFiles(client):
    # Fetching the list of files
    files_data = client.files.list().data

    # Iterating over the list and assigning each file object to a variable
    for file_object in enumerate(files_data):
        # Here, we're printing the details. You can replace this with any operation you need.
        if file_object.filename == "prices_data.txt" and file_object.id != "file-BaUuu5vl3Mcf0Pu2futPIwXJ":
            deleteFile = shouldDeleteFile(file_object.created_at)
            if deleteFile:
                client.files.delete(file_object.id)
                print(f"File = {file_object.id} - DELETED")
            else:
                print(f"File = {file_object.id} - NOT DELETED")

load_dotenv()
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
client = OpenAI(api_key=OPENAI_API_KEY)

def job():
    scanFiles(client)

schedule.every().day.at("00:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)