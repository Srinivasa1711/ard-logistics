
import requests
import pandas as pd
from datetime import datetime
# Access Token & Endpoint

today = datetime.today().strftime('%Y-%m-%d')
access_token = "UsIZcjIJm4-JIRsPQyYXC1shHH8"
url = "https://gaamanufacturing.prd.mykronos.com/api/v1/commons/data/multi_read"

# Payload with desired date range and filter



payload = {
"select": [
{"key": "TK_ON_PREMISE"},
{ "key": "EMP_COMMON_FULL_NAME_AND_PERSON_NUMBER"},
{ "key": "EMP_COMMON_PRIMARY_JOB_CODE"},
{ "key": "EMP_COMMON_PRIMARY_JOB_DESCRIPTION"},
{ "key": "EMP_COMMON_PRIMARY_JOB"}
],
"from": {
"view": "EMP",
"employeeSet": {
"hyperfind": {
"qualifier": "Vance"
},
"dateRange": {
"symbolicPeriod": {
"qualifier": "Today"
}
}

}
}
}

headers = {
    "authorization": f"Bearer {access_token}",
    "accept": "application/json",
    "content-type": "application/json"
}

# API Call
response = requests.post(url, json=payload, headers=headers)
print(response.text)
