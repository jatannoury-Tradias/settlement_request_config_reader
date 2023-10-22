from decimal import Decimal
from typing import Tuple, Dict, List

import requests


class SpaceshipController:
    def __init__(self):
        self._url = f"https://api.uat.tradias.link"
        self.tradias_user_token = requests.post(url=f"https://uat.tradias.link/api/authenticate", json={
            "email": "admin@tradias.de",
            "secret": "admin@tradias.de"
        }).json()['auth_token']

    def get_client_token(self, client_id):
        headers = {
            "Authorization": f"Bearer {self.tradias_user_token}"
        }
        self.client_token = requests.post(f"https://uat.tradias.link/api/clients/{client_id}/generate_token",
                                          headers=headers).json()
        return self.client_token

    def get_paginated_trades(self, client_id, start_time, end_time) -> Tuple[Dict, List, str, str]:
        # try:
        print(f"FROM:{start_time}, TO:{end_time}")
        trades = self.get_client_trades(client_id, start_time, end_time, return_raw=True,
                                        queries="limit=1000")
        if len(trades['trades']) == 0:
            return {}, [], "", ""
        request_nb = 1
        paginated_trades = [*trades['trades']]

        if trades.get("pagination", None) == None:
            trades_dates = [trade['executions'][0]['executed_at'] for trade in paginated_trades]
            start_date, end_date = min(trades_dates), max(trades_dates)
            return self.clean_response({"trades": paginated_trades, "start_date": start_date, "end_date": end_date})
        while trades['pagination']['limit'] + trades['pagination']['skip'] < trades['pagination']['total_count']:
            trades = self.get_client_trades(start_time, end_time, return_raw=True,
                                            queries=f"skip={1000 * request_nb}&limit=1000")
            paginated_trades = [*paginated_trades, *trades['trades']]
            request_nb += 1

        trades_dates = [trade['executions'][0]['executed_at'] for trade in paginated_trades]
        start_date, end_date = min(trades_dates), max(trades_dates)
        return self.clean_response({"trades": paginated_trades, "start_date": start_date, "end_date": end_date})

    def get_client_trades(self, client_id, from_datetime_str, to_datetime_str, return_raw=False, queries=""):
        params = {
            "from_datetime": from_datetime_str,
            "to_datetime": to_datetime_str
        }
        headers = {
            "Authorization": f"Bearer {self.get_client_token(client_id=client_id)['token']}"
        }
        response = requests.get(f"https://api.uat.tradias.link/api/trades?{queries}", params=params,
                                headers=headers).json()
        if return_raw == True:
            return response

        return self.clean_response(response)

    def get_client_addresses(self, client_id):
        headers = {
            "Authorization": f"Bearer {self.tradias_user_token}"
        }
        response = requests.get(f"https://uat.tradias.link/api/addresses/?limit=1000000000", headers=headers).json()

        client_addresses = {
            currency: element['address'] for element in list(
                filter(
                    lambda element: element['owner_id'] == client_id,
                    response['items']
                )
            ) for currency in element['currencies']
        }
        return client_addresses

    def post_settlement_request(self, data):
        headers = {'Authorization': f'Bearer {self.client_token["token"]}'}
        return requests.post('https://api.uat.tradias.link/api/settlement-requests', json=data, headers=headers)

    def clean_response(self, response) -> Tuple[Dict, List, str, str]:
        legs_to_be_settelled = {}
        trades = []
        for trade in response['trades']:
            leg_1, leg_2 = trade['order'][0].get('instrument').split("-")[0], \
                           trade['order'][0].get('instrument').split("-")[1]
            leg_1_status, leg_2_status = trade['executions'][0].get('leg_1_status'), trade['executions'][0].get(
                'leg_2_status')
            side = trade['order'][0].get('side')
            amt_leg_1 = str(Decimal(trade['executions'][0].get('leg_1_executed_amount'))) if side == "SELL" else str(
                -1 * Decimal(trade['executions'][0].get('leg_1_executed_amount')))
            amt_leg_2 = str(
                -1 * Decimal(trade['executions'][0].get('leg_2_executed_amount'))) if side == "SELL" else str(
                Decimal(trade['executions'][0].get('leg_2_executed_amount')))
            if leg_1_status == "UNSPECIFIED" and leg_2_status == "UNSPECIFIED":
                legs_to_be_settelled[leg_1] = amt_leg_1 if leg_1 not in legs_to_be_settelled else format(
                    Decimal(legs_to_be_settelled[leg_1]) + Decimal(amt_leg_1), '.100f').rstrip("0").rstrip(".")
                legs_to_be_settelled[leg_2] = amt_leg_2 if leg_2 not in legs_to_be_settelled else format(
                    Decimal(legs_to_be_settelled[leg_2]) + Decimal(amt_leg_2), '.100f').rstrip("0").rstrip(".")
                trades.append(trade['trade_id'])
                # elif leg_1_status == "UNSPECIFIED" and leg_2_status != "UNSPECIFIED":
                #     if leg_1 not in legs_to_be_settelled:
                #         legs_to_be_settelled[leg_1] = -amt_leg_1 if side.lower() == "buy" else amt_leg_1
                #     else:
                #         legs_to_be_settelled[leg_1] += -amt_leg_1 if side.lower() == "buy" else amt_leg_1
                #
                #     trades.append(trade['trade_id'])
                # elif leg_1_status != "UNSPECIFIED" and leg_2_status == "UNSPECIFIED":
                #     if leg_2 not in legs_to_be_settelled:
                #         legs_to_be_settelled[leg_2] = amt_leg_2 if side.lower() == "buy" else -amt_leg_2
                #     else:
                #         legs_to_be_settelled[leg_2] += amt_leg_2 if side.lower() == "buy" else -amt_leg_2

                trades.append(trade['trade_id'])
        return legs_to_be_settelled, trades, response['start_date'], response['end_date']
