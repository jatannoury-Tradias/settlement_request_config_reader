from datetime import time
import datetime
import json

import requests

from config.spaceship_configs import CREDENTIALS
from tools.datetime_helpers import *
from tools.get_clients_tokens import get_client_tokens
from tools.settlement_controller import settlement_controller, tfs_settlement_controller
from config.s3_config import bucket_name, config_file_name
token=None

def get_user_token(env):
    print("Auth request!!!!!!!!!!!!")
    payload = {
        "email": CREDENTIALS[env.lower()]['email'],
        "secret": CREDENTIALS[env.lower()]['password']
    }
    response = requests.post(f"https://{env.casefold()}.tradias.link/api/authenticate", json=payload)
    if response.status_code != 200:
        raise Exception("Wrong credentials. Add the correct credentials to the .env file")
    json_response = response.json()
    if json_response.get('auth_token', None) == None:
        raise KeyError("Something went wrong during authentication, auth_token key not found in response")
    return json_response['auth_token']


def get_client_legacy_id( client_spaceship_id,env):
    return requests.get(f"https://{env.lower()}.tradias.link/api/counter_parties/{client_spaceship_id}", headers={
        "Authorization": f"Bearer {get_user_token(env) if token == None else token}"
    }).json().get("client_legacy_id", None)

def configs_resolver(json_response,s3,env):
    token = get_user_token(env)
    client_tokens = get_client_tokens(env)
    for key,item in json_response.items():
        if item['is_enabled'] == False:
            continue
        if item['client_name'].lower() == "duck_test" or item['client_name'].lower() == "alain desvigne 1" or item['client_name'].lower() == "alain desvigne 2":
            print()
        curr_client_spaceship_id = item['client_id']
        curr_client_token = client_tokens.get(get_client_legacy_id(client_spaceship_id=curr_client_spaceship_id,env=env), None)
        if curr_client_token == None:
            print(f"Client: {item['client_name']} with id:{item['client_id']} is not in the scraped tokens mapping")
            continue
        print(key,item)
        current_date = datetime.date.today()
        days_to_subtract = (current_date.weekday() - 0) % 7  # Calculate days to subtract for the previous Monday
        # current_date = (current_date - datetime.timedelta(days=21))
        trigger_day = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][current_date.weekday()]
        print("Trigger Day",trigger_day)
        if item['frequency'] == "Daily":
            if current_date.weekday() == 0:
                if item['include_weekend'] == True:
                    start_time,end_time = get_72_hours_tf_from_limit(item['end_time'])
                    sr_data = settlement_controller(item,start_time,end_time,curr_client_token,env,user_token=token,spaceship_id=curr_client_spaceship_id)
                    json_response[key] = sr_data
                else:
                    if item['end_time'] == "12:00 AM":
                        start_time,end_time = get_24_hours_tf(anchor = current_date - datetime.timedelta(days=3))
                        sr_data = settlement_controller(item,start_time,end_time,curr_client_token,env,user_token=token,spaceship_id=curr_client_spaceship_id)
                        json_response[key] = sr_data
                    else:
                        start_time, end_time = get_24_hours_tf_from_limit(item['end_time'],anchor = current_date - datetime.timedelta(days=3))
                        if start_time == False or end_time == False:
                            continue
                        sr_data = settlement_controller(item,start_time,end_time,curr_client_token,env,user_token=token,spaceship_id=curr_client_spaceship_id)
                        json_response[key] = sr_data
                        
            else:
                start_time,end_time = get_24_hours_tf_from_limit(item['end_time'])
                if start_time == False or end_time == False:
                    continue
                sr_data = settlement_controller(item,start_time,end_time,client_token=curr_client_token,env=env,user_token=token,spaceship_id=curr_client_spaceship_id)
                json_response[key] = sr_data
        elif item['frequency'] == "Weekly":
            if item['day_limit'] == trigger_day:
                if item['include_weekend'] == True:
                    start_time, end_time = get_7_days_tf_from_limit(item,current_date)
                    sr_data = settlement_controller(item,start_time,end_time,curr_client_token,env,user_token=token,spaceship_id=curr_client_spaceship_id)
                    json_response[key] = sr_data
                else:
                    start_time, end_time = get_7_days_tf_from_limit(item,current_date)
                    left_limit, right_limit = get_7_weekdays_tf_from_limit_no_we(item,current_date)
                    sr_data = tfs_settlement_controller(item,[(start_time,left_limit),(right_limit,end_time)],curr_client_token,env,user_token=token,spaceship_id=curr_client_spaceship_id)
                    json_response[key] = sr_data
            else:
                continue
        elif item['frequency'] == "Monthly":
                if item['day_limit'] == "EOM":
                    if is_last_day_of_month(current_date.year,current_date.month,current_date.day) == False:
                        continue
                    if item['include_weekend'] == True:
                        start_time = current_date.replace(day=1)
                        settlement_controller(item,start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),current_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),curr_client_token,env,user_token=token,spaceship_id=curr_client_spaceship_id)
                    elif item['include_weekend'] == False:
                        start_time = current_date.replace(day=1)
                        boundaries = []
                        weekdays = get_month_weekdays(start_time,current_date)
                        frames = [[limit[0], limit[-1]]for limit in weekdays]
                        for frame in frames:
                            lower_bound = frame[0]
                            upper_bound = frame[1]
                            frame[0] = datetime.datetime(lower_bound.year,lower_bound.month,lower_bound.day,0,0,0).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                            frame[1] = datetime.datetime(upper_bound.year,upper_bound.month,upper_bound.day,23,59,59,999999).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                        sr_data = tfs_settlement_controller(item,frames,env=env,client_token=curr_client_token,user_token=token,spaceship_id=curr_client_spaceship_id)
                        json_response[key] = sr_data
        new_json_string = json.dumps(json_response)
        s3.put_object(
            Bucket=bucket_name,
            Key=config_file_name,
            Body=new_json_string,  # The new JSON data as a string
            ContentType="application/json",  # Specify the content type if needed
        )
