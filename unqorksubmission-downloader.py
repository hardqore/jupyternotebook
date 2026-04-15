import subprocess
import requests
import json
import pandas as pd
from datetime import datetime, timedelta, timezone, date
import getpass
import time
from typing import Final
import sys

PRECOA_WORKFLOW_ID: Final = "5eafdf4ba6690f01f847b95a"
PRENEED_WORKFLOW_ID: Final = "5eb0182c3b877e01f970ffa3"
ALLOWED_WORKFLOWS: Final = [PRECOA_WORKFLOW_ID, PRENEED_WORKFLOW_ID]
AUTH_ENDPOINT: Final = "https://appqore.mynglic.com/api/1.0/oauth2/access_token"
your_username: str
your_password: str
how_many_days_back: int

def get_files_list(job_id: str):
    try:
        while True:
            status = get_job_status(jobid)
            print(f"Current status: {status}")
        
            # 2. Check the condition to exit
            if status == 'completed':
                print("Status is complete! retreving the filepaths to download ...")
                return get_job_details(jobid)
                break
            
            # 3. Wait for 5 minutes (300 seconds) before trying again
            print("Waiting 5 minutes...")
            time.sleep(300)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def download_files_from_urls(files: list[str]):
    for file in files:
        api_endpoint = f"https://appqore.mynglic.com/api{file}"
    
        filename = file.split("/")[-1]  # Get the last part of the URL after the last '/'
        filename = f"{filename}.json"

        # Construct the curl command
        command = [
            "curl",
            "-s",  # Suppress progress meter
            "-o", filename,  # Save the downloaded file with the specified filename
            api_endpoint  # The URL to download
        ]
    
        # Add bearer token header if provided
        bearer_token = get_bearer_token()
        if bearer_token:
            command.extend(["-H", f"Authorization: Bearer {bearer_token}"])
    
        try:
            subprocess.run(command, check=True)  # check=True raises an exception for non-zero exit codes
    
            print(f"Downloaded '{api_endpoint}' and saved as '{filename}'")
    
        except FileNotFoundError:
            print("Error: 'curl' command not found. Please ensure curl is installed and in your system's PATH.")
        except subprocess.CalledProcessError as e:
            print(f"Error downloading '{url}': {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


def get_filepath_list(job_details: list[str]):
    api_endpoint = "https://appqore.mynglic.com/fbu/uapi/bulkOperations/downloadLink"

    files = []
    
    for job_detail in job_details:
    
        command = [
            "curl", "-X", "POST", api_endpoint,
            "-H", f"Authorization: Bearer {get_bearer_token()}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"fileLocation": job_detail["destination"]["location"]})
        ]

        try:
            result = subprocess.run(command, capture_output=True, text=True)   
            json_data = json.loads(result.stdout)
            files.append(json_data["downloadLink"])
    
        except FileNotFoundError:
            print("Error: 'curl' command not found. Please ensure curl is installed and in your system's PATH.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    return files

def get_job_status(download_id: str):
    url = f"https://appqore.mynglic.com/fbu/uapi/bulkOperations/jobs/{download_id}"

    command = [
        "curl", 
        "-X", "GET", 
        "-H", f"Authorization: Bearer {get_bearer_token()}",
        "-H", "Content-Type: application/json",
        url
    ]    
    
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        json_data = json.loads(result.stdout)

        return json_data["data"]["status"]
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_job_details(download_id: str):
    url = f"https://appqore.mynglic.com/fbu/uapi/bulkOperations/jobs/{download_id}"

    command = [
        "curl", 
        "-X", "GET", 
        "-H", f"Authorization: Bearer {get_bearer_token()}",
        "-H", "Content-Type: application/json",
        url
    ]    
    
    try:
        result = subprocess.run(command, capture_output=True, text=True)

        json_data = json.loads(result.stdout)
        steps = json_data["data"]["steps"]
        files = steps[0]["files"]

        return files
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_download_id(json_payload: str):
    if output:
        try:
            json_data = json.loads(json_payload)
            if 'id' in json_data:
                return json_data['id']
        except json.JSONDecodeError:
            print(f"Error decoding JSON for hour {hour}. Output: {output}")
            return None

def get_logs_with_curl(workflow_id: str):
    api_endpoint = "https://appqore.mynglic.com/fbu/uapi/bulkOperations/export"

    past_date = datetime.now(timezone.utc) - timedelta(days=how_many_days_back)
    
    payload = { 
        "dataModelOrModuleId": workflow_id, 
        "dateFieldStartToFilterOn": past_date.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000Z"), 
        "exportFullRecord": "true", 
        "fileFormat": "JSON" ,
        "name":  "RJWorkflowDataExportTest-Data recorded after this date", 
        "numberOfFilesToGenerate": 1, 
        "targetRecordType": "ALL" 
    }

    json_data = json.dumps(payload)

    command = [
        "curl", "-X", "POST", api_endpoint,
        "-H", f"Authorization: Bearer {get_bearer_token()}",
        "-H", "Content-Type: application/json",
        "-d", json_data
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True)
        return result.stdout

    except FileNotFoundError:
        print("Error: 'curl' command not found. Please ensure curl is installed and in your system's PATH.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_bearer_token():
    payload = {
        'username': your_username,
        'password': your_password,
        'grant_type': 'password' 
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded' 
    }

    try:
        response = requests.post(AUTH_ENDPOINT, data=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        token_data = response.json()
        bearer_token = token_data.get('access_token')

        if bearer_token:
            return bearer_token
        else:
            print(f"Error: 'access_token' not found in response: {token_data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error during token request: {e}")
        return None


your_username = input("Please enter your username: ")
your_password = getpass.getpass("Please enter the password: ")

workflow_id = input(f"Please enter the workflow_id {ALLOWED_WORKFLOWS}: ")

how_many_days_back = int(input("How many days back do you want to download files for? "))

# Check if the input belongs to the allowed list
if workflow_id not in ALLOWED_WORKFLOWS:
    print("Error: Invalid workflow_id. Terminating program.")
    sys.exit()  # Ends the program's execution
    
output = get_logs_with_curl(workflow_id)
jobid = json.loads(output)["id"]

print(f"Job Id: {jobid}")

file_details_list = get_files_list(jobid)

files_to_download = get_filepath_list(file_details_list)

download_files_from_urls(files_to_download)