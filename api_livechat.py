import os
import base64
from dotenv import load_dotenv
import requests
import json
import psycopg2

# Load environment variables from .env file
load_dotenv(dotenv_path='')
auth_key = os.getenv('AUTH_KEY')

# Load PostgreSQL Credentials from .env file
load_dotenv(dotenv_path='')
db_config = {
    'dbname': 'masayaco_dev',
    'user': os.getenv('username'),
    'password': os.getenv('password'),
    'host': os.getenv('host'),
    'port': os.getenv('port')
}

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
                    #print(f" Customer Name: {customer_name}")
                    customer_data = {
                        'customer_id': customer_id,
                        'customer_name': customer_name,
                        'customer_mail': customer.get('email', 'N/A'),
                        'email_verified': customer.get('email_verified')
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
    next_page_id = page_id  # Use page_id as initial next_page_id
    first_page = True

    try:
        all_chat_ids = []  # Initialize to store only chat IDs
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
                chat_ids_this_page = [chat["id"] for chat in chats_this_page]
                all_chat_ids.extend(chat_ids_this_page)
            if "next_page_id" in data and data["next_page_id"]:
                next_page_id = data["next_page_id"]
                first_page = False
            else:
                break
            first_page = False
        return all_chat_ids

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

def GetDB_Chats():
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        #Query
        cursor.execute("SELECT chat_id FROM erp_livechat_chats")

        # Fetch all the results
        rows = cursor.fetchall()

        # Extract chat IDs from the rows
        All_ChatID = [row[0] for row in rows]  # Assuming chat_id is the first column

        # Print the chat IDs for verification
        
        #print("Chat IDs from database:", All_ChatID)
        #print(len(All_ChatID))


        return All_ChatID
    
    except psycopg2.Error as db_error:
        print(f"Database error: {db_error}")
        return None  # Return None to indicate an error

    finally:
        if conn:
            cursor.close()
            conn.close()
    
def Insert_Agents(All_Agents): # FIXED FOR NEW DB SCHEMA

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
   
        #Insert Agents Query
        author_query = """
            INSERT INTO erp_livechat_authors (author_id, author_name, author_mail, author_type)
            VALUES (%s, %s, %s, 'Agent')
            ON CONFLICT (author_id) DO NOTHING;
        """
        agent_query = """
            INSERT INTO erp_livechat_agents (agent_id, agent_role)
            VALUES (%s, %s)
            ON CONFLICT (agent_id) DO NOTHING;
        """

        for agent in All_Agents:
            cursor.execute(author_query, (agent['agent_id'], agent['agent_name'], agent['agent_mail']))
            cursor.execute(agent_query, (agent['agent_id'], agent['agent_role']))
            print(f"Inserting Agent: {agent['agent_name']} - {agent['agent_role']}")

        conn.commit()
        print(f"Committed {len(All_Agents)} Agents.")

        # Close the cursor and connection
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        raise  # Stop the entire process on any database error

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise  # Stop the entire process on any unexpected error

def Insert_Customers(all_customers):
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        #Insert Author Query
        author_query = """
            INSERT INTO erp_livechat_authors (author_id, author_name, author_mail, author_type)
            VALUES (%s, %s, %s, 'Customer')
            ON CONFLICT (author_id) DO NOTHING;
        """

        #Insert Customers Query
        customer_query = """
            INSERT INTO erp_livechat_customers (customer_id, email_verified)
            VALUES (%s, %s)
            ON CONFLICT (customer_id) DO NOTHING;
        """

        for customer in all_customers:
            cursor.execute(author_query, (customer['customer_id'],customer['customer_name'], customer['customer_mail']))
            cursor.execute(customer_query, (customer['customer_id'], customer['email_verified']))
            print(f"Inserting Customer: {customer['customer_name']} - {customer['customer_mail']}")
        
        conn.commit()
        print(f"Committed {len(all_customers)} Customers.")

        # Close the cursor and connection
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        raise  # Stop the entire process on any database error

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise  # Stop the entire process on any unexpected error

def Insert_Chats(all_chat_ids): 
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        Query = """
            INSERT INTO erp_livechat_chats(chat_id)
            VALUES (%s)
            ON CONFLICT (chat_id) DO NOTHING;
        """

        for chat_id in all_chat_ids: # Iterate through the list of IDs
            cursor.execute(Query, (chat_id,)) # Use the ID directly
            print(f"Inserting Chat ID: {chat_id}")

        conn.commit()
        print(f"Committed {len(all_chat_ids)} Chats.")

        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        raise  # Stop the entire process on any database error

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise  # Stop the entire process on any unexpected error

def list_threads(chat_id):  
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {auth_value}'
    }

    url = 'https://api.livechatinc.com/v3.5/agent/action/list_threads'
    payload = {  # Include chat_id in the payload
        "chat_id": chat_id  # Use the chat_id parameter
    }
    All_Threads = []
    All_Events = []
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        #  The response should have 'threads'
        if isinstance(data, dict) and "threads" in data and isinstance(data["threads"], list):
            Threads = data["threads"]
            All_Threads = []

            #print('Threads:')
            for Thread in Threads:

                # Data for Thread Data
                thread_id = Thread.get('id', 'N/A')
                Thread_Data = {
                    'thread_id': thread_id,
                    'thread_chat_id':chat_id
                }

                # Data for Events from Thread
                events = Thread.get('events', [])
                for event in events:
                    #In Case the Event Author is the System Itself
                    if 'author_id' not in event or event.get('author_id') is None:
                        event['author_id'] = 'System'
                    event_data = {
                    'event_id': event.get('id'),
                    'event_thread_id': thread_id,
                    'created_at': event.get('created_at'),
                    'author_id': event.get('author_id')
                    }

                    All_Events.append(event_data)
                All_Threads.append(Thread_Data)

            #print("All_Threads:", All_Threads)
            #print("All_Events:",All_Events)

        else:
            print("Error: Unexpected response format.  Expected a dict with 'threads' key.")
            print("Full response data:", data)  # Print full response for debugging

    except requests.exceptions.RequestException as e:
        print(f'Request error: {e}')
        if response is not None:
            print(f'HTTP status code: {response.status_code}')
            try:
                error_data = response.json()
                print('Error response:', error_data)
            except ValueError:
                print('Error response text:', response.text)
    return All_Threads, All_Events



def Insert_Threads_Events(All_Threads, All_Events,conn,cursor):
    try:
        
        Thread_Query = """
            INSERT INTO erp_livechat_threads(thread_id, thread_chat_id)
            VALUES (%s, %s)
            ON CONFLICT (thread_id) DO NOTHING;
            """
        Event_Query = """
            INSERT INTO erp_livechat_events(event_id, event_thread_id, author_id, created_at)
            VALUES(%s,%s,%s,%s)
            ON CONFLICT(event_id) DO NOTHING;
            """
        Author_Lookup_Query = """
            SELECT author_id FROM erp_livechat_authors WHERE author_mail = %s;
            """

        #Thread Insertion
        for thread in All_Threads:
            cursor.execute(Thread_Query, (thread['thread_id'], thread['thread_chat_id']))
            #print(f"Inserting Thread ID: {thread['thread_id']}")

        # Event Insertion
        events_to_insert = []
        for event in All_Events:
            author_id = event['author_id']

            if '@' in str(author_id):
                cursor.execute(Author_Lookup_Query, (author_id,))
                Agent = cursor.fetchone()
                if Agent:
                    author_id = Agent[0]
                else:
                    error_message = f"Warning: Agent with email '{author_id}' not found in erp_livechat_authors for event {event['event_id']}"
                    print(error_message)
                    continue
            else:
                continue

            events_to_insert.append((event['event_id'], event['event_thread_id'], author_id, event['created_at']))

        if events_to_insert:
            try:
                cursor.executemany(Event_Query, events_to_insert)
                print(f"Inserted {len(events_to_insert)} events in batch.")
            except psycopg2.Error as e:
                print(f"Error during batch event insert: {e}")
                conn.rollback() 
                raise

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        raise  # Stop the entire process on any database error

    except ValueError as e:
        raise  # Re-raise the ValueError

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise  # Stop the entire process on any unexpected error



if __name__ == "__main__":
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        #All_Agents = list_agents()
        #All_Customers = list_customers()
        #All_Chats = list_chats()
        #list_threads('SV36ETX10B')
        
        #Insert_Agents(All_Agents)
        #Insert_Customers(All_Customers)
        #Insert_Chats(All_Chats)
        #print('FINISH')

        #Thread and Event Insertion

        # [1] Retrieve All Chats from our DB
        Chats = GetDB_Chats()

        for Chat in Chats:
        # [2] list_threads returns all threads and events as lists for every chat
            Chat_Threads,Chat_Events = list_threads(Chat)
            Insert_Threads_Events(Chat_Threads,Chat_Events,conn,cursor)
            print(f'Chat ID: {Chat} Inserted')
        conn.commit()

        cursor.close()
        conn.close()
        print("FINISH")

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print(f"Database error in main: {e}")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"An unexpected error occurred in main: {e}")
        if conn:
            cursor.close()
            conn.close()

