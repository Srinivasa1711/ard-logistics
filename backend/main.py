
# test_sync.py
import requests
import json
from datetime import datetime, timedelta

# Copy your API constants from the Flask app here
TEAMS_API_BASE_URL = "https://gaamanufacturing.prd.mykronos.com"
TOKEN_ENDPOINT = f"{TEAMS_API_BASE_URL}/api/authentication/access_token"
TEAMS_API_EMPLOYEES_ENDPOINT = f"{TEAMS_API_BASE_URL}/api/v1/commons/persons/apply_read"
TOKEN_CLIENT_ID = 'KPijaUKjvBfBDNuSiX8hKTVN3g9xC3XA'
TOKEN_CLIENT_SECRET = '0uDmCz7TpWAPPit6'
API_USERNAME = 'HR1API'
API_PASSWORD = 'API1234@ARD' 

# Copy your fetch and refresh functions here
def refresh_api_token():
    # ... (paste your function here) ...
    try:
        response = requests.post(
            TOKEN_ENDPOINT,
            data={
                'grant_type': 'password',
                'username': API_USERNAME,
                'password': API_PASSWORD,
                'client_id': TOKEN_CLIENT_ID,
                'client_secret': TOKEN_CLIENT_SECRET,
                'auth_chain': 'OAuthLdapService'
            }
        )
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data['access_token']
        print("Access token obtained successfully.")
        return access_token
    except Exception as e:
        print(f"Error refreshing API token: {e}")
        return None

def fetch_employee_data_from_api(access_token):
    # ... (paste your updated function here) ...
    url = TEAMS_API_EMPLOYEES_ENDPOINT
    # payload = {
    #     "where": {
    #         "hyperfind": {
    #             "qualifier": "All Home"
    #         }
    #     }
    # }
    from datetime import datetime, timedelta

    # Define a full 24-hour range for the current day to get all active employees.
    start_of_today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_today = start_of_today + timedelta(days=1)

    # Format for the API payload
    start_date_str = start_of_today.strftime("%Y-%m-%dT%H:%M:%S")
    end_date_str = end_of_today.strftime("%Y-%m-%dT%H:%M:%S")

    url = TEAMS_API_EMPLOYEES_ENDPOINT
    payload = {
        "where": {
            "dateRange": {
                "startDateTime": start_date_str,
                "endDateTime": end_date_str
            }
        }
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    print(f"Fetching employee data from API using hyperfind 'All Home'...")
    print(f"DEBUG: Fetching from URL: {url}")
    print(f"DEBUG: Using Payload: {json.dumps(payload)}")
    print(f"DEBUG: Using Headers: {headers}")

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching employee data: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print("Server error message:")
            print(e.response.text)
        raise

# Main test block
if __name__ == "__main__":
    access_token = refresh_api_token()
    if access_token:
        print(f"Token: {access_token[:10]}...")
        try:
            employee_data = fetch_employee_data_from_api(access_token)
            print("API fetch successful.")
            print(f"Received {len(employee_data.get('persons', []))} employees.")
            if len(employee_data.get('persons', [])) > 0:
                print("First employee details:")
                print(json.dumps(employee_data['persons'][0], indent=2))
            else:
                print("No employees returned from API. Check the 'hyperfind' qualifier.")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred during employee data fetch: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print("Server error message:")
                print(e.response.text)
    else:
        print("Failed to get access token.")
