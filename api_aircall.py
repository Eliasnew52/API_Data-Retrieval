import requests
import os 
from dotenv import load_dotenv
import base64
from datetime import datetime


load_dotenv(dotenv_path='/Users/luis/Documents/shoopify_api/shopifyenviroment/credentials_aircall.env')
url_id = "https://api.aircall.io/v1/calls/2236890239"
url = "https://api.aircall.io/v1/calls"

api_token = os.getenv('api_token')
api_id = os.getenv('api_id')

auth = (api_id,api_token)

def FetchAll(url, auth):
    #Response
    All_Calls = []
    current =  url

    while current:
        response = requests.get(current, auth=auth)
        Json = response.json()

        JsonCalls = Json['calls']
        MetaData = Json['meta']
        for Call in JsonCalls:
            call_data = {
                'call_id': Call.get('id'),
                'direction': Call.get('direction'),
                'duration': Call.get('duration'),
                
            }
            print(call_data)

        print(MetaData['current_page'])
         #Test Breaker
        if MetaData['current_page'] == 5:
            break
        else:    
            current = MetaData['next_page_link']

       
    
    print("Finish")
        





def Fetch_Test(url,auth):
    # Al Ejecutar la Peticion, le pasamos los Tokens de Auth y el Endpoint
    # NOTA - Auth es una Lista que obtiene tanto el ID como el Token de la API desde el .env
    response = requests.get(url,auth=auth)

    if response.status_code == 401:
        print("Error")
    else:
        json_response = response.json()

        call_dict = json_response['call']
        user_dict = json_response['call']['user']
        number_dict = json_response['call']['number']


        #Objeto Call

        stored_call = {
            'call_id' : call_dict['id'], #Call Primary Key
            'call_status': call_dict['status'],
            'call_direction': call_dict['direction'],
            'call_missed_call_reason': call_dict['missed_call_reason'],
            'call_duration': call_dict['duration'],
            'call_raw_digits': call_dict['raw_digits'],
            'call_voice_mail': call_dict['voicemail'],
            'call_user_id': user_dict['id'], # User Foreign Key - Se Relaciona con stored_user 'id_user'
            'call_started_at': datetime.utcfromtimestamp(call_dict['started_at']).strftime('%Y-%m-%d %H:%M:%S'),
            'call_answered_at': datetime.utcfromtimestamp(call_dict['answered_at']).strftime('%Y-%m-%d %H:%M:%S'),
            'call_ended_at': datetime.utcfromtimestamp(call_dict['ended_at']).strftime('%Y-%m-%d %H:%M:%S'), 

            #Format goes as Follows: {2024-09-03  22:22:22}
            
            

        }

        #Objeto User - Call
        stored_user_dict = {
            'user_id': user_dict['id'], #User Primary Key - Se Relaciona con stored_call 'id_user
            'user_direct_link': user_dict['direct_link'],
            'user_name': user_dict['name'],
            'user_email': user_dict['email'],
            'user_available': user_dict['available'],
            'user_availability_status': user_dict['availability_status'],
            'user_created_at': user_dict['created_at'],
            'user_time_zone': user_dict['time_zone'],
            'user_language': user_dict['language'],
            'user_state': user_dict['state'],
            'user_wrap_up_time': user_dict['wrap_up_time']
        }

        #Object Number - Call
        stored_number_dict={
            'number_id': number_dict['id'],
            'number_name': number_dict['name'],
            'number_digits' : number_dict['digits'],
            'number_created_at': number_dict['created_at'],
            'number_country': number_dict['country'],
            'number_timezone': number_dict['time_zone'],
            'number_availability_status': number_dict['availability_status'],


        }



        #print(stored_user_dict)
        #print(stored_call)
        #print (number_dict)
        print(json_response)

def FetchAll_Test(url, auth):
    response = requests.get(url,auth=auth)

    if response.status_code == 401:
        print("Error")
    else:
        json_response = response.json()
        print(json_response)


#all = Fetch_Calls(url,auth)
#for i in range(10):
#    print(all[i])

#FetchAll_Test(url,auth)
# Example usage
FetchAll(url,auth)


