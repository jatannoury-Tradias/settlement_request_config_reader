from tools.datetime_helpers import get_24_hours_tf, get_24_hours_tf_from_limit
from tools.spaceship_controller import SpaceshipController
import json
spaceship_controller = SpaceshipController()
def settlement_controller(item,start_time,end_time,client_token,env,user_token,spaceship_id):
    legs_to_be_settelled,trades,start_date,end_date = spaceship_controller.get_paginated_trades(client_id = item['client_id'],start_time=start_time,end_time=end_time,client_token=client_token,env=env,user_token=user_token,spaceship_id=spaceship_id)
    trades = list(set(trades))

    if legs_to_be_settelled == {} or trades == []:
        return item
    curr_client_addresses = spaceship_controller.get_client_addresses(item['client_id'],env=env,token=user_token)
    print("Length of trades:",len(trades))
    body = {
            'trade_ids': trades,
            'request_amounts': [
                {
                    'currency': leg,
                    'from_address': 'BHS' if float(amount) <= 0 else curr_client_addresses.get(leg,f"No Address!"),
                    'to_address': 'BHS' if float(amount) >= 0 else curr_client_addresses.get(leg,f"No Address!"),
                    'amount': amount.replace("-","")
                }
                for leg, amount in legs_to_be_settelled.items()
            ]
        }
    response = spaceship_controller.post_settlement_request(body,client_token,env=env)
    if response.status_code == 202:
        json_response = response.json()
        print(response.content)
        if 'automated_srs' not in item:
            item['automated_srs'] = {json_response['settlement_request_id']:{
                "start_date":start_date,
                "end_date":end_date
            }}
        else:
            item['automated_srs'][json_response['settlement_request_id']] = {
                "start_date":start_date,
                "end_date":end_date
            }
    return item

def tfs_settlement_controller(item,tfs,client_token,env,user_token,spaceship_id):
    legs_to_be_settelled = {}
    trades = []
    for tf in tfs:
        start_time,end_time = tf
        curr_legs_to_be_settelled,curr_trades,start_date,end_date = spaceship_controller.get_paginated_trades(client_id = item['client_id'],start_time=start_time,end_time=end_time,client_token=client_token,env=env,user_token=user_token,spaceship_id=spaceship_id)

        if curr_legs_to_be_settelled == {} or curr_trades == []:
            continue
        else:
            trades = [*curr_trades]
            for leg,amount in curr_legs_to_be_settelled.items():
                if leg in legs_to_be_settelled:
                    legs_to_be_settelled[leg] += amount
                else:
                    legs_to_be_settelled[leg] = amount
    if legs_to_be_settelled == {} or trades == []:
        return item
    curr_client_addresses = spaceship_controller.get_client_addresses(item['client_id'],env=env,token=user_token)
    body = {
            'trade_ids': trades,
            'request_amounts': [
                {
                    'currency': leg,
                    'from_address': 'BHS' if amount < 0 else curr_client_addresses[leg],
                    'to_address': 'BHS' if amount > 0 else curr_client_addresses[leg],
                    'amount': str(abs(float(amount)))
                }
                for leg, amount in legs_to_be_settelled.items()
            ]
        }

    response = spaceship_controller.post_settlement_request(body,env=env,token=client_token)
    if response.status_code == 202:
        json_response = response.json()
        print(response.content)
        if 'automated_srs' not in item:
            item['automated_srs'] = {json_response['settlement_request_id']:{
                "start_date":start_date,
                "end_date":end_date
            }}
        else:
            item['automated_srs'][json_response['settlement_request_id']] = {
                "start_date":start_date,
                "end_date":end_date
            }
    print(response.content)
    return item
