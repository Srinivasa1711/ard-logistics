import requests
import pandas as pd
from datetime import datetime, timedelta




# Replace with your actual values
client_id = 'KPijaUKjvBfBDNuSiX8hKTVN3g9xC3XA'
client_secret = '0uDmCz7TpWAPPit6'
token_url = 'https://gaamanufacturing.prd.mykronos.com/api/authentication/access_token'

# # Define the token request payload
# payload = {
#     'username': 'HRAPI3',
#     'password': 'API1234@ARD',
#     'grant_type': 'password',
#     'client_id': client_id,
#     'client_secret': client_secret,
#     'auth_chain': 'OAuthLdapService'
# }

# # Send the POST requecst to get the token
# response = requests.post(token_url, data=payload)

# if response.status_code == 200:
#     token_data = response.json()
#     access_token = token_data['access_token']
#     refresh_token = token_data['refresh_token']
#     print("Access Token:", access_token)
#     print("Refresh_Token:", refresh_token)
#     print("Expires In:", refresh_token)
    
# else:
#     print("Failed to retrieve token:", response.status_code)
#     print(response.text)

payload = {
    'username': 'HR1API',
    'password': 'API1234@ARD',
    'grant_type': 'password',
    'client_id': client_id,
    'client_secret': client_secret,
    'auth_chain': 'OAuthLdapService'
}


response = requests.post(token_url, data=payload)

if response.status_code == 200:
    token_data = response.json()
    
    access_token = token_data['access_token']
    refresh_token = token_data['refresh_token']
    expires_in = token_data.get('expires_in', 3600)  

    # Calculate token expiry time
    expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)

    print("Access Token:", access_token)
    print("Refresh Token:", refresh_token)
    print("Expires In (seconds):", expires_in)
    print("Token Expiry Time (UTC):", expiry_time.isoformat())

else:
    print("❌ Failed to retrieve token:", response.status_code)
    print(response.text)
