import subprocess
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import getpass

def get_download_url(job_details: str, bearer_token: str):
    api_endpoint = "https://appqore.mynglic.com/fbu/uapi/bulkOperations/downloadLink"

    payload = { 
        "fileLocation": job_details
    }

    json_data = json.dumps(payload)

    command = [
        "curl", "-X", "POST", api_endpoint,
        "-H", f"Authorization: Bearer {bearer_token}",
        "-H", "Content-Type: application/json",
        "-d", json_data
    ]

    try:
        # Execute the curl command and capture the output
        result = subprocess.run(command, capture_output=True, text=True)

        # Return the stdout of the curl command
        return result.stdout

    except FileNotFoundError:
        print("Error: 'curl' command not found. Please ensure curl is installed and in your system's PATH.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def get_job_details(download_id: str, bearer_token: str):
    url = f"https://appqore.mynglic.com/fbu/uapi/bulkOperations/jobs/{download_id}"

    command = [
        "curl", 
        "-X", "GET", 
        "-H", f"Authorization: Bearer {bearer_token}",
        "-H", "Content-Type: application/json",
        url
    ]    
    
    try:
        result = subprocess.run(command, capture_output=True, text=True)

        json_data = json.loads(result.stdout)


        steps = json_data["data"]["steps"]
        files = steps[0]["files"]

        # print(json.dumps(files, indent=4))  

        return files[0]["destination"]["location"]
        
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

def get_logs_with_curl(bearer_token: str):
    api_endpoint = "https://appqore.mynglic.com/fbu/uapi/bulkOperations/export"

    payload = { 
        "dataModelOrModuleId": "5eafdf4ba6690f01f847b95a", 
        "dateFieldStartToFilterOn": "2026-03-18T21:06:59.729Z", 
        "exportFullRecord": "true", 
        "fileFormat": "JSON" ,
        "name":  "RJWorkflowDataExportTest-Data recorded after this date", 
        "numberOfFilesToGenerate": 1, 
        "targetRecordType": "ALL" 
    }

    json_data = json.dumps(payload)

    command = [
        "curl", "-X", "POST", api_endpoint,
        "-H", f"Authorization: Bearer {bearer_token}",
        "-H", "Content-Type: application/json",
        "-d", json_data
    ]

    try:
        # Execute the curl command and capture the output
        result = subprocess.run(command, capture_output=True, text=True)

        # Return the stdout of the curl command
        return result.stdout

    except FileNotFoundError:
        print("Error: 'curl' command not found. Please ensure curl is installed and in your system's PATH.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_bearer_token(auth_url, username, password):
    """
    Obtains a bearer token from an authentication endpoint.

    Args:
        auth_url (str): The URL of the authentication endpoint.
        username (str): The user's username.
        password (str): The user's password.

    Returns:
        str or None: The bearer token if successful, otherwise None.
    """
    payload = {
        'username': username,
        'password': password,
        'grant_type': 'password' # Common for password grant type in OAuth2
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded' # Often required for this grant type
    }

    try:
        response = requests.post(auth_url, data=payload, headers=headers)
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

# Prompt the user for credentials and such
auth_endpoint = "https://appqore.mynglic.com/api/1.0/oauth2/access_token"
your_username = input("Please enter your username: ")
your_password = getpass.getpass("Please enter the password: ")
bearer_token = get_bearer_token(auth_endpoint, your_username, your_password)
output = get_logs_with_curl(bearer_token)

download_id = get_download_id(output)
job_details = get_job_details(download_id, bearer_token)
download_url = get_download_url(job_details, bearer_token)

print(json.dumps(json.loads(download_url), indent=4))

