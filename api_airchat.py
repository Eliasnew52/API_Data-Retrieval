import os
import base64
from dotenv import load_dotenv
import requests

# Load environment variables from .env file

load_dotenv(dotenv_path='/Users/josias/Documents/GoogleSheet_API/mynewenviroment/credentials_livechat_api.env')
auth_key = os.getenv('AUTH_KEY')

# Check if the API key is loaded
if not auth_key:
    print("Error: AUTH_KEY environment variable not found. Make sure your .env file is in the project root and contains AUTH_KEY=your_api_key")
    exit(1)

# Encode the AUTH_KEY for Basic Authentication
auth_value = base64.b64encode(auth_key.encode()).decode()
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Basic {auth_value}'
}

url = 'https://api.livechatinc.com/v3.5/agent/action/get_chat'
payload = {
    "chat_id": "SU4MP1UP4P",
    #"thread_id": "SUWHK1I22U"
}

try:
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
    data = response.json()
    print('Chat Details:', data)
except requests.exceptions.RequestException as e:
    print(f'Request error: {e}')
    if response is not None:
        print(f'HTTP status code: {response.status_code}')
        try:
            error_data = response.json()
            print('Error response:', error_data)
        except ValueError:
            print('Error response text:', response.text)
