import json
import boto3
import requests

from config.s3_config import bucket_name, config_file_name
import datetime
from datetime import time

from tools.logger import FileLogger
from tools.spaceship_controller import SpaceshipController
from tools.datetime_helpers import *
from tools.settlement_controller import settlement_controller, tfs_settlement_controller
from tools.automation_config_resolver import configs_resolver

s3 = boto3.client("s3")
spaceship_controller = SpaceshipController()
logger = FileLogger(__name__)


def lambda_handler(event, context):
    logs = []
    if "queryStringParameters" in event and "read_only" in event['queryStringParameters'] and \
            event['queryStringParameters']['read_only'] == "true":
        if "queryStringParameters" in event and 'environment' in event['queryStringParameters'] and len(
                event['queryStringParameters']['environment']) > 0:
            raw_response = s3.get_object(Bucket=bucket_name,
                                         Key=f"{config_file_name}/{event['queryStringParameters']['environment'].upper()}/settlement_client_config.json")
            polished_response = raw_response['Body'].read()
            json_response = json.loads(polished_response)
        else:
            return {
                "statusCode": 400,
                "message": "Environment should be specified"
            }
        return json_response

    for env in ['UAT', "PREPROD", "PROD"]:
        try:
            logger.log_info(f"ENV:{env}")
            raw_response = s3.get_object(Bucket=bucket_name,
                                         Key=f"{config_file_name}/{env.upper()}/settlement_client_config.json")
            polished_response = raw_response['Body'].read()
            json_response = json.loads(polished_response)
            configs_resolver(json_response, s3, env)
        except Exception as e:
            logger.log_critical(str(e))
    requests.post("https://pg6iizvmy3g7znprkhvkb3onje0fycoy.lambda-url.eu-central-1.on.aws/",
                  json={"data": json.dumps(logger.get_all_logs())})


