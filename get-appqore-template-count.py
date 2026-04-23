import subprocess
import requests
import json
import pandas as pd
from datetime import datetime, timedelta, timezone
import getpass
import time
from typing import Final
import sys

PRECOA_GET_TEMPLATE_ENDPOINT_URL: Final = "https://appqore.mynglic.com/fbu/uapi/modules/61e93d16e71e7501a3741571/execute"
PRENEED_GET_TEMPLATE_ENDPOINT_URL: Final = "https://appqore.mynglic.com/fbu/uapi/modules/61e98a3fd2852c01a3242220/execute"
AUTH_ENDPOINT: Final = "https://appqore.mynglic.com/api/1.0/oauth2/access_token"
your_username: str
your_password: str

def get_template_count(api_endpoint: str, template_count_node_name: str):
    payload = {
        "data": {
            "hiddenUserSubmissionId": "60c0eba13bb5eb02e1cf91ed",
            "filterSort": "",
            "filterString": "filter={\"data.hdnTemplateSharedByUserNameID\":{\"$exists\":true}}",
            "stxtRole": "INTERNAL",
            "limit": 300,
            "offset": 0
        }
    }

    json_data = json.dumps(payload)

    command = [
        "curl", "-X", "PUT", api_endpoint,
        "-H", f"Authorization: Bearer {get_bearer_token()}",
        "-H", "Content-Type: application/json",
        "-d", json_data
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True)
        result_json = json.loads(result.stdout)
        result_json["data"]["resolved"][template_count_node_name]        
        return result_json["data"]["resolved"][template_count_node_name]

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

print(datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.000Z"))
print(f"Precoa Shared Template Count: {get_template_count(PRECOA_GET_TEMPLATE_ENDPOINT_URL, 'submissionCountPrecoaTemplate')}")
print(f"Precoa Shared Template Count: {get_template_count(PRENEED_GET_TEMPLATE_ENDPOINT_URL, 'submissionCountPreneedTemplate')}")