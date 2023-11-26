import datetime
from decimal import Decimal
from typing import Tuple, Dict, List

import requests

from tools.logger import FileLogger

logger = FileLogger(__name__)


class SpaceshipController:
    def __init__(self):
        self._url = f"https://api.uat.tradias.link"
        self.tradias_user_token = None

    def get_client_token(self, client_id, client_token=None):
        if client_token != None:
            return client_token
        headers = {
            "Authorization": f"Bearer {self.tradias_user_token}"
        }
        self.client_token = requests.post(f"https://uat.tradias.link/api/clients/{client_id}/generate_token",
                                          headers=headers).json()
        return self.client_token

    def remove_one_day(self, dt_format, date_str):
        removed_day_object = datetime.datetime.strptime(date_str, dt_format) - datetime.timedelta(days=1)
        return removed_day_object.strftime(dt_format)

    def get_paginated_trades(self, client_id, start_time, end_time, client_token, env, user_token, spaceship_id) -> \
    Tuple[Dict, List, str, str]:
        # try:
        start_time = self.remove_one_day(dt_format='%Y-%m-%dT%H:%M:%S.%fZ', date_str=start_time)
        end_time = self.remove_one_day(dt_format='%Y-%m-%dT%H:%M:%S.%fZ', date_str=end_time)
        logger.log_info(f"FROM:{start_time}, TO:{end_time}")
        trades = self.get_client_trades(spaceship_id, start_time, end_time, return_raw=True,
                                        queries="limit=1000", user_token=user_token, env=env)
        if len(trades['items']) == 0:
            return {}, [], "", ""
        request_nb = 1
        paginated_trades = [*trades['items']]

        if trades.get("pagination", None) == None:
            trades_dates = [trade['executed_at'] for trade in paginated_trades]
            start_date, end_date = min(trades_dates), max(trades_dates)
            return self.clean_response({"trades": paginated_trades, "start_date": start_date, "end_date": end_date})
        while trades['pagination']['limit'] + trades['pagination']['skip'] < trades['pagination']['total_count']:
            trades = self.get_client_trades(spaceship_id, start_time, end_time, return_raw=True,
                                            queries=f"skip={1000 * request_nb}&limit=1000", env=env,
                                            user_token=client_token)
            paginated_trades = [*paginated_trades, *trades['items']]
            request_nb += 1

        trades_dates = [trade['executed_at'] for trade in paginated_trades]
        start_date, end_date = min(trades_dates), max(trades_dates)
        return self.clean_response({"trades": paginated_trades, "start_date": start_date, "end_date": end_date})

    def get_client_trades(self, client_id, from_datetime_str, to_datetime_str, return_raw=False, queries="",
                          user_token=None, env=None):
        params = {
            "start_date": str(datetime.datetime.strptime(from_datetime_str, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()),
            "end_date": str(datetime.datetime.strptime(to_datetime_str, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()),
            'any_leg': True,
            'leg_1': client_id
        }
        headers = {
            "Authorization": f"Bearer {user_token}"
        }
        response = requests.get(f"https://{env.lower()}.tradias.link/api/trades_history?{queries}", params=params,
                                headers=headers).json()
        if return_raw == True:
            return response

        return self.clean_response(response)

    def get_client_addresses(self, client_id, env, token):
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(f"https://{env}.tradias.link/api/addresses/?limit=1000000000", headers=headers).json()

        client_addresses = {
            currency: element['address'] for element in list(
                filter(
                    lambda element: element['owner_id'] == client_id,
                    response['items']
                )
            ) for currency in element['currencies']
        }
        return client_addresses

    def post_settlement_request(self, data, token, env):
        headers = {'Authorization': f'Bearer {token}'}
        return requests.post(f'https://api.{env}.tradias.link/api/settlement-requests', json=data, headers=headers)

    def clean_response(self, response) -> Tuple[Dict, List, str, str]:
        legs_to_be_settelled = {}
        trades = []
        for trade in response['trades']:
            leg_1, leg_2 = trade['leg_1_currency'], \
                           trade['leg_2_currency']
            leg_1_status, leg_2_status = trade['leg_1_status'], trade['leg_1_status']
            side = trade['side']
            amt_leg_1 = str(Decimal(trade['leg_1_amount'])) if side == "SELL" else str(
                -1 * Decimal(trade['leg_1_amount']))
            amt_leg_2 = str(
                -1 * Decimal(trade['leg_2_amount'])) if side == "SELL" else str(
                Decimal(trade['leg_2_amount']))
            if leg_1_status == "Unknown" and leg_2_status == "Unknown":
                legs_to_be_settelled[leg_1] = amt_leg_1 if leg_1 not in legs_to_be_settelled else format(
                    Decimal(legs_to_be_settelled[leg_1]) + Decimal(amt_leg_1), '.100f').rstrip("0").rstrip(".")
                legs_to_be_settelled[leg_2] = amt_leg_2 if leg_2 not in legs_to_be_settelled else format(
                    Decimal(legs_to_be_settelled[leg_2]) + Decimal(amt_leg_2), '.100f').rstrip("0").rstrip(".")
                trades.append(trade['id'])
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

                trades.append(trade['id'])
        return legs_to_be_settelled, trades, response['start_date'], response['end_date']
