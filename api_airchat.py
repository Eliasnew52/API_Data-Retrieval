import os
import base64
from dotenv import load_dotenv
import requests
import json

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
    return All_Agents
    

def list_customers(page_id=None, limit=100):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {auth_value}'
    }
    url = 'https://api.livechatinc.com/v3.5/agent/action/list_customers'

    all_customers = []
    next_page_id = page_id  # Use page_id as initial next_page_id
    first_page = True

    try:
        while True:
            payload = {}
            if next_page_id:
                payload['page_id'] = next_page_id
            elif first_page:
                if 0 < limit <= 100:
                    payload['limit'] = limit
                else:
                    raise ValueError("Limit must be between 1 and 100")

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and "customers" in data and isinstance(data["customers"], list):
                customers = data["customers"]
                print(f"Fetching page with page_id: {next_page_id}, limit: {limit}")
                for customer in customers:
                    customer_id = customer.get('id', 'N/A')
                    customer_name = customer.get('name', 'N/A')
                    #print(f"  Customer ID: {customer_id}")
                    print(f" Customer Name: {customer_name}")
                    customer_data = {
                        'customer_id': customer_id,
                        'customer_name': customer_name,
                        'customer_email': customer.get('email', 'N/A'),
                    }
                    all_customers.append(customer_data)

                next_page = data.get('next_page_id')
                if not next_page:
                    break

                next_page_id = next_page
                first_page = False # set it to false after the first page

            else:
                print("Error: Unexpected response format. Expected a dictionary containing 'customers'.")
                break

    except requests.exceptions.RequestException as e:
        print(f'Request error: {e}')
        if response is not None:
            print(f'HTTP status code: {response.status_code}')
            try:
                error_data = response.json()
                print('Error response:', error_data)
            except ValueError:
                print('Error response text:', response.text)
        return None

    print(f"\nTotal customers fetched: {len(all_customers)}")
    return all_customers


def list_chats(page_id=None, limit=100):
    url = "https://api.livechatinc.com/v3.5/agent/action/list_chats"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_value}",
    }
    all_chats = []  # Initialize to store all chats
    next_page_id = page_id  # Use page_id as initial next_page_id
    first_page = True

    try:
        while True:
            payload = {}
            if next_page_id:
                payload["page_id"] = next_page_id
            elif first_page:
                if 0 < limit <= 100:
                    payload["limit"] = limit
                else:
                    raise ValueError("Limit must be between 1 and 100")
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            if "chats_summary" in data:
                chats_this_page = data["chats_summary"]
                all_chats.extend(chats_this_page)
                print("Chats on this page:")  # Print header for each page
                for chat in chats_this_page:
                    print(chat["id"])  # Print chat IDs on current page
            if "next_page_id" in data and data["next_page_id"]:
                next_page_id = data["next_page_id"]
                first_page = False
            else:
                break
            first_page = False

        return all_chats

    except requests.exceptions.RequestException as e:
        print(f"Fetch error: {e}")
        if response is not None:
            try:
                error_text = response.text
                print(f"Error details: {error_text}")
            except:
                pass
        return None

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        if response is not None:
            print(f"Raw response text: {response.text}")
        return None

    except ValueError as e:
        print(f"Invalid input: {e}")
        return None


if __name__ == "__main__":
    try:
        #all_chats = list_chats(limit=100)  # Get chats with a limit
        #if all_chats:
        #    print("\nTotal Chats Retrieved:", len(all_chats))
        #else:
        #   print("Failed to retrieve chats.")

        All_Agents = list_agents()
        print(All_Agents)
        print(f'Total Agents: {len(All_Agents)}')
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

