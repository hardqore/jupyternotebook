import subprocess
import requests
import json
import pandas as pd
from datetime import datetime, timedelta

# ngl@MDL002461:/mnt/c/GitHub/jupyternotebook/unqork-audit-logs$ mkdir 2025-november-december
# ngl@MDL002461:/mnt/c/GitHub/jupyternotebook/unqork-audit-logs$ mv *.gz  ./2025-november-december/
# ngl@MDL002461:/mnt/c/GitHub/jupyternotebook/unqork-audit-logs$ cd 2025-november-december/
# ngl@MDL002461:/mnt/c/GitHub/jupyternotebook/unqork-audit-logs/2025-november-december$ gunzip *.gz
# ngl@MDL002461:/mnt/c/GitHub/jupyternotebook/unqork-audit-logs$ ./process_file.sh

my_array = []

def get_audit_logs_with_curl(start_date: str, end_date: str, bearer_token: str):
    api_endpoint = "https://appqore.mynglic.com/api/1.0/logs/audit-logs"

    command = [
        "curl",
        "-s",  # Suppress progress meter
        "-H", f"Authorization: Bearer {bearer_token}",  # Add bearer token header
        f"{api_endpoint}?startDatetime={start_date}&endDatetime={end_date}"  # Construct the API URL with query parameters
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

def download_files_from_urls(urls: list[str], bearer_token: str = None):
    for url in urls:
        # Extract the filename from the URL (part after "/files/")
        filename = url.split("/")[-1]  # Get the last part of the URL after the last '/'
        
        # Add the .gz extension to the filename
        save_filename = f"{filename}.gz"

        # Construct the curl command
        command = [
            "curl",
            "-s",  # Suppress progress meter
            "-o", save_filename,  # Save the downloaded file with the specified filename
            url  # The URL to download
        ]

        # Add bearer token header if provided
        if bearer_token:
            command.extend(["-H", f"Authorization: Bearer {bearer_token}"])

        try:
            # Execute the curl command
            subprocess.run(command, check=True)  # check=True raises an exception for non-zero exit codes

            print(f"Downloaded '{url}' and saved as '{save_filename}'")

        except FileNotFoundError:
            print("Error: 'curl' command not found. Please ensure curl is installed and in your system's PATH.")
        except subprocess.CalledProcessError as e:
            print(f"Error downloading '{url}': {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


def get_logfile_urls(start_datetime_str, bearer_token):
    start_datetime_obj = datetime.fromisoformat(start_datetime_str.replace("Z", "+00:00")) 
    logfile_urls = []

    # Iterate through 24 hours
    for hour in range(24):
        # Calculate the end datetime (1 hour after the start datetime)
        end_datetime_obj = start_datetime_obj + timedelta(hours=1)

        # Format the datetimes back to the required string format
        start_date_str = start_datetime_obj.isoformat(timespec='milliseconds').replace("+00:00", "Z")
        end_date_str = end_datetime_obj.isoformat(timespec='milliseconds').replace("+00:00", "Z")

        # Call the function for the current hour
        # NOTE: You'll need to replace 'get_audit_logs_with_curl' with your actual function call
        # that fetches audit logs using curl.
        output = get_audit_logs_with_curl(start_date_str, end_date_str, bearer_token) 

        # Process the output (e.g., print it, save it to a file, etc.)
        if output:
            try:
                json_data = json.loads(output)
                if 'logLocations' in json_data:
                    logfile_urls.extend(json_data['logLocations']) # Use extend to add elements from a list
            except json.JSONDecodeError:
                print(f"Error decoding JSON for hour {hour}. Output: {output}")

        # Update the start datetime for the next iteration
        start_datetime_obj = end_datetime_obj

    return logfile_urls

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
your_password = input("Please enter the password: ")
user_input_string = input("Please enter for how many days past you want the data for: ")

# Array of start dates
start_dates = pd.date_range(end=datetime.utcnow().date(), periods=int(user_input_string), freq='D').strftime("%Y-%m-%dT%H:%M:%S.000Z").tolist() 


# Loop through the array of start dates
for start_date in start_dates:
    # Call the function with the current start date and bearer token
    bearer_token = get_bearer_token(auth_endpoint, your_username, your_password)
    urls_for_date = get_logfile_urls(start_date, bearer_token)

    # Cumulatively store the results
    my_array.extend(urls_for_date) # Use extend for efficient list merging

download_files_from_urls(my_array, bearer_token)
