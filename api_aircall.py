import requests
import os 
from dotenv import load_dotenv
import base64
from datetime import datetime , timezone
from psycopg2 import *
import json


load_dotenv(dotenv_path='/Users/luis/Documents/shoopify_api/shopifyenviroment/credentials_aircall.env')
url_id = "https://api.aircall.io/v1/calls/2236890239"
url = "https://api.aircall.io/v1/calls"

api_token = os.getenv('api_token')
api_id = os.getenv('api_id')

auth = (api_id,api_token)


load_dotenv(dotenv_path='/Users/luis/Documents/ia_project/myenviromet/credential_postgresql.env')
db_config = {
    'dbname': os.getenv('database'),
    'user': os.getenv('username'),
    'password': os.getenv('password'),
    'host': os.getenv('host'),
    'port': os.getenv('port')
}



def FetchAll(url, auth):
    # Response
    All_Calls = []
    current = url

    while current:
        try:
            response = requests.get(current, auth=auth)
            response.raise_for_status()  # Check for HTTP errors
            Json = response.json()

            # Cada Response me Devuelve ->
            JsonCalls = Json['calls']  # Una Lista de las Llamadas de una Pagina
            MetaData = Json['meta']  # Metadata para Acceder a las demas Paginas y conocer el numero de la actual
            for Call in JsonCalls:
                user_info = Call.get('user') or {}  # User puede ser un Objeto None 
                call_data = {  # Datos de la Llamada
                    'call_id': Call.get('id'),
                    'call_status': Call.get('status'),
                    'call_direction': Call.get('direction'),
                    'call_missed_reason': Call.get('missed_call_reason'),
                    'call_duration': Call.get('duration'),
                    'call_started_at': datetime.fromtimestamp(int(Call['started_at']), timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if Call.get('started_at') else None,
                    'call_answered_at': datetime.fromtimestamp(int(Call['answered_at']), timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if Call.get('answered_at') else None,
                    'call_ended_at': datetime.fromtimestamp(int(Call['ended_at']), timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if Call.get('ended_at') else None,  
                    'call_raw_digits': Call.get('raw_digits'),
                    'call_tags': json.dumps(Call.get('tags')),
                    'call_teams': json.dumps(Call.get('teams')),  
                    # User info
                    'user_id': user_info.get('id'),
                    'user_name': user_info.get('name'),
                    'user_email': user_info.get('email'),
                    'user_created_at': user_info.get('created_at'),
                    'user_state': user_info.get('state'),
                    'user_availability': user_info.get('availability_status'),
                }
                # Agregamos cada Registro a la Lista
                All_Calls.append(call_data)
                # print(call_data)

            # Imprime el numero de la pagina actual
            print(MetaData['current_page'])

            # Revisa que hayan más páginas
            current = MetaData.get('next_page_link')

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            # Maneja errores relacionados con las solicitudes HTTP, como problemas de conexión o tiempos de espera
            break
        except KeyError as e:
            print(f"Key error: {e}")
            # Maneja errores cuando las claves esperadas no están presentes en la respuesta JSON.
            break
        except ValueError as e:
            print(f"Value error: {e}")
            # Maneja errores relacionados con conversiones de tipo incorrectas o valores inesperados como None a INT.
            break
    
    print("Fetching Finished")
    return All_Calls


#Only Works for a Single ID
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


# WORKING 100%


def InsertCalls(all_calls, db_config):
    try:
        # Conectar a la base de datos
        conn = connect(**db_config)
        cursor = conn.cursor()

        # Preparar la sentencia SQL de inserción
        insert_query = """
        INSERT INTO api_aircall (call_id, call_status, call_direction, call_missed_reason, call_duration, call_started_at, call_answered_at, call_ended_at, call_raw_digits, call_tags, call_teams, user_id, user_name, user_email, user_created_at, user_state, user_availability)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (call_id) DO NOTHING
        """

        # Insertar cada llamada en la base de datos
        for call in all_calls:
            cursor.execute(insert_query, (
                call['call_id'], call['call_status'], call['call_direction'], call.get('call_missed_reason'),
                call['call_duration'], call['call_started_at'], call.get('call_answered_at'), call['call_ended_at'],
                call.get('call_raw_digits'), call.get('call_tags'), call.get('call_teams'), call.get('user_id'),
                call.get('user_name'), call.get('user_email'), call.get('user_created_at'),
                call.get('user_state'), call.get('user_availability')
            ))
            print(f"Data inserted: {call['call_id']}")

        # Confirmar la transacción
        conn.commit()

    except Error as e:
        print(f"Error inserting data: {e}")
        conn.rollback()

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        print("Database connection closed.")

# Configuración de la base de datos


# Llamar a la función FetchAll para obtener los datos y luego insertar en la base de datos
All_Calls = FetchAll(url, auth)

#Inserta los Registros en la DB
InsertCalls(All_Calls, db_config)
