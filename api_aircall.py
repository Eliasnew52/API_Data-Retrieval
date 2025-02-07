import requests
import os
from dotenv import load_dotenv
import base64

#env file path
load_dotenv()

url = "https://api.aircall.io/v1/calls"

api_token = os.getenv('api_token')
api_id = os.getenv('api_id')

auth = (api_id,api_token)

response = requests.get(url, auth=auth)

if response.status_code == 401:
  print("Error")
else:
  print(response.json())
