#
# 
import requests
import pandas as pd
from datetime import datetime
# Access Token & Endpoint

today = datetime.today().strftime('%Y-%m-%d')
access_token = "KdiZsgCgZPZ3adsnvjPZ1GqtDEo"
url = "https://gaamanufacturing.prd.mykronos.com/api/v1/commons/data/multi_read"

# Payload with desired date range and filter



payload = {
"select": [
# {"key": "TK_ON_PREMISE"},
{ "key": "EMP_COMMON_FULL_NAME_AND_PERSON_NUMBER"},

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



#import requests
# import pandas as pd
# from datetime import datetime

# # Format today's date as snapshot
# snapshot_date = datetime.today().strftime("%Y-%m-%dT00:00:00")

# # UKG access token (replace with your real token logic for automation)
# access_token = "s4IQE-niX84r5C5Nh838z2cYU8U"

# # API endpoint for reading persons
# url = "https://gaamanufacturing.prd.mykronos.com/api/v1/commons/persons/apply_read"

# # Payload to fetch active employees only
# payload = { "where": {
#         "dateRange": {
#             "endDateTime": (snapshot_date),
#             "startDateTime": (snapshot_date)
#         },
#         "missingExternalIdType": "aoid"
#     } }

# headers = {
#     "Authorization": f"Bearer {access_token}",
#     "Accept": "application/json",
#     "Content-Type": "application/json"
# }




#>>>>>>>>>>
#actual API call
# import requests
# import pandas as pd
# from datetime import datetime, timedelta


# # end_date = datetime.today()
# # start_date = end_date - timedelta(days=100)
# # start = start_date.strftime('2025-07-08')
# # end = end_date.strftime('2025-07-14')

# today = datetime.today().strftime('%Y-%m-%d')


# access_token ="IyFRsW2_Jw9r07mOTE3ubyGLhZ4"
# url = "https://gaamanufacturing.prd.mykronos.com/api/v1/commons/persons/apply_read"


 
# payload = { "where": {
#         "dateRange": {
#             "endDateTime": "today",
#             "startDateTime": "today"
#         },
#         "missingExternalIdType": "aoid"
#     } }

# headers = {
#     "Authorization": f"Bearer {access_token}",
#     "Accept": "application/json",
#     "Content-Type": "application/json"
# }
 
# response = requests.post(url, json=payload, headers=headers)

# print(response.text)
# # API call
# try:
#     response = requests.post(url, json=payload, headers=headers)
#     response.raise_for_status()
#     data = response.json()

#     # Extract results (check list or dict)
#     results = data.get("results", []) if isinstance(data, dict) else data

#     if not results:
#         print("⚠️ No employee data returned.")
#     else:
#         # Normalize and extract relevant fields
#         df = pd.json_normalize(results)

#         df_final = df[["person.personNumber", "person.name.firstName", "person.name.lastName", "employment.status"]].copy()
#         df_final.columns = ["Employee ID", "First Name", "Last Name", "Status"]

#         # Optional: Convert status to "Active"/"Terminated" for readability
#         df_final["Status"] = df_final["Status"].apply(lambda x: "Active" if x == "Active" else "Terminated")

#         print(df_final)

#         # Save to Excel
#         df_final.to_excel("employee_status_export.xlsx", index=False)
#         print(f"✅ Exported {len(df_final)} records to employee_status_export.xlsx")

# except requests.exceptions.HTTPError as http_err:
#     print("❌ HTTP Error Occurred:", http_err)
#     try:
#         error_data = response.json()
#         print("📄 Error Details:")
#         print(f"🔹 Message: {error_data.get('message')}")
#         print(f"🔹 Code: {error_data.get('errorCode')}")
#     except:
#         print("📄 Raw Response Text:", response.text)
# except Exception as e:
#     print("❌ Unexpected Error:", str(e))

