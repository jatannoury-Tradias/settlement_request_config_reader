import json
import boto3
from config.s3_config import bucket_name, config_file_name
import datetime
from datetime import time
from tools.spaceship_controller import SpaceshipController
from tools.datetime_helpers import *
from tools.settlement_controller import settlement_controller, tfs_settlement_controller
s3 = boto3.client("s3")
spaceship_controller = SpaceshipController()
def lambda_handler(event, context):
    # try:
        raw_response = s3.get_object(Bucket=bucket_name, Key=config_file_name)
        polished_response = raw_response['Body'].read()
        json_response = json.loads(polished_response)
        
        if "queryStringParameters" in event and "read_only" in event['queryStringParameters'] and event['queryStringParameters']['read_only'] == "true":
            return json_response
            
        for key,item in json_response.items():
            if item['is_enabled'] == False:
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
                        sr_data = settlement_controller(item,start_time,end_time)
                        json_response[key] = sr_data
                    else:
                        if item['end_time'] == "12:00 AM":
                            start_time,end_time = get_24_hours_tf(anchor = current_date - datetime.timedelta(days=3))
                            sr_data = settlement_controller(item,start_time,end_time)
                            json_response[key] = sr_data
                        else:
                            start_time, end_time = get_24_hours_tf_from_limit(item['end_time'],anchor = current_date - datetime.timedelta(days=3))
                            if start_time == False or end_time == False:
                                continue
                            sr_data = settlement_controller(item,start_time,end_time)
                            json_response[key] = sr_data
                            
                else:
                    start_time,end_time = get_24_hours_tf_from_limit(item['end_time'])
                    if start_time == False or end_time == False:
                        continue
                    sr_data = settlement_controller(item,start_time,end_time)
                    json_response[key] = sr_data
            elif item['frequency'] == "Weekly":
                if item['day_limit'] == trigger_day:
                    if item['include_weekend'] == True:
                        start_time, end_time = get_7_days_tf_from_limit(item,current_date)
                        sr_data = settlement_controller(item,start_time,end_time)
                        json_response[key] = sr_data
                    else:
                        start_time, end_time = get_7_days_tf_from_limit(item,current_date)
                        left_limit, right_limit = get_7_weekdays_tf_from_limit_no_we(item,current_date)
                        sr_data = tfs_settlement_controller(item,[(start_time,left_limit),(right_limit,end_time)])
                        json_response[key] = sr_data
                else:
                    continue
            elif item['frequency'] == "Monthly":
                    if item['day_limit'] == "EOM":
                        if is_last_day_of_month(current_date.year,current_date.month,current_date.day) == False:
                            continue
                        if item['include_weekend'] == True:
                            start_time = current_date.replace(day=1)
                            settlement_controller(item,start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),current_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
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
                            sr_data = tfs_settlement_controller(item,frames)
                            json_response[key] = sr_data
        new_json_string = json.dumps(json_response)

        # Replace the existing file with the new JSON data
        s3.put_object(
            Bucket=bucket_name,
            Key=config_file_name,
            Body=new_json_string,  # The new JSON data as a string
            ContentType="application/json",  # Specify the content type if needed
        )




                            
                        
                
    # except Exception as e:
    #     return {
    #         'statusCode': 500,
    #         'body': json.dumps('Error: ' + str(e))
    #     }

lambda_handler({},{})