import json
import boto3
from config.s3_config import bucket_name, config_file_name
import datetime
from datetime import time
from tools.spaceship_controller import SpaceshipController
from tools.datetime_helpers import *
from tools.settlement_controller import settlement_controller, tfs_settlement_controller
from tools.automation_config_resolver import configs_resolver
s3 = boto3.client("s3")
spaceship_controller = SpaceshipController()
def lambda_handler(event, context):
    # try:
        
        if "queryStringParameters" in event and "read_only" in event['queryStringParameters'] and event['queryStringParameters']['read_only'] == "true" :
            if "queryStringParameters" in event and 'environment' in event['queryStringParameters'] and len(event['queryStringParameters']['environment']) > 0:
                raw_response = s3.get_object(Bucket=bucket_name, Key=f"{config_file_name}/{event['queryStringParameters']['environment'].upper()}/settlement_client_config.json")
                polished_response = raw_response['Body'].read()
                json_response = json.loads(polished_response)
            else:
                return {
                    "statusCode":400,
                    "message":"Environment should be specified"
                }
            return json_response
            
        for env in ['UAT',"PREPROD","PROD"]:
            try:
                raw_response = s3.get_object(Bucket=bucket_name, Key=f"{config_file_name}/{env.upper()}/settlement_client_config.json")
                polished_response = raw_response['Body'].read()
                json_response = json.loads(polished_response)
                configs_resolver(json_response,s3,env)
            except Exception as e:
                print(e)
lambda_handler({},{})