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


def Get_LatestChats():
    url = "https://api.livechatinc.com/v3.5/agent/action/list_chats"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_value}",
    }
    latest_chat_ids = []
    limit = 100  # Maximum allowed limit

    # First request for the latest 100 chats
    payload_first = {"sort_order": "desc", "limit": limit}
    try:
        response_first = requests.post(url, headers=headers, json=payload_first)
        response_first.raise_for_status()
        data_first = response_first.json()
        if "chats_summary" in data_first:
            latest_chat_ids.extend([chat["id"] for chat in data_first["chats_summary"]])
            next_page_id = data_first.get("next_page_id")

            # Second request for the next 50 chats using pagination
            if len(latest_chat_ids) == limit and next_page_id:
                payload_second = {"page_id": next_page_id}  # Only include page_id
                response_second = requests.post(url, headers=headers, json=payload_second)
                response_second.raise_for_status()
                data_second = response_second.json()
                if "chats_summary" in data_second:
                    latest_chat_ids.extend([chat["id"] for chat in data_second["chats_summary"]])

    except requests.exceptions.RequestException as e:
        print(f"Fetch error: {e}")
        if 'response_first' in locals() and response_first is not None:
            try:
                print(f"Error details (first request): {response_first.text}")
            except:
                pass
        if 'response_second' in locals() and response_second is not None:
            try:
                print(f"Error details (second request): {response_second.text}")
            except:
                pass
        return None

    return latest_chat_ids[:150] # Ensure we return at most 150 chat IDs

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

# Example usage:
if __name__ == "__main__":
    try:
        
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        #Retrive the Last 150 Chats
        All_Chats = Get_LatestChats()
        print(len(All_Chats))
        Insert_Chats(All_Chats)
       

        for Chat in All_Chats:

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
