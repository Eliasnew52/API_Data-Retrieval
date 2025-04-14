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


def get_chat(chat_id):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {auth_value}'
    }

    url = 'https://api.livechatinc.com/v3.5/agent/action/get_chat'
    payload = {
        "chat_id": chat_id,
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



def list_agents():
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {auth_value}'
    }

    url = 'https://api.livechatinc.com/v3.5/configuration/action/list_agents'
    payload = {}  # Empty JSON payload
    All_Agents = []

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()

        # Handle both cases: dict with "Agents" or direct list
        if isinstance(data, dict) and "Agents" in data and isinstance(data["Agents"], list):
            Agents = data["Agents"]
        elif isinstance(data, list):
            Agents = data  # The response is directly the list of agents
        else:
            print("Error: Unexpected response format. Expected a list of agents or a dictionary containing 'Agents'.")
            return  # Exit the function if the format is wrong

        print('Agents:')
        for Agent in Agents:
            Agent_Data = {
                'agent_id': Agent.get('account_id', 'N/A'),
                'agent_name': Agent.get('name', 'N/A'),
                'agent_mail': Agent.get('id', 'N/A'),
                'agent_role': Agent.get('role', 'N/A')
            }
            All_Agents.append(Agent_Data)

        print(All_Agents)

    except requests.exceptions.RequestException as e:
        print(f'Request error: {e}')
        if response is not None:
            print(f'HTTP status code: {response.status_code}')
            try:
                error_data = response.json()
                print('Error response:', error_data)
            except ValueError:
                print('Error response text:', response.text)



list_agents()
