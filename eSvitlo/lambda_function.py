import json
import os
from datetime import datetime

import boto3

from air_strike import get_air_strike_oblasts

dynamodb = boto3.client("dynamodb")
sns = boto3.client("sns")


def readable_address(item):
    address = item["address"]["M"]
    return ', '.join((address["city"]["S"], address["street"]["S"], address["building"]["S"]))


def lambda_handler(event, context):
    items = dynamodb.scan(
        TableName='eSvitlo',
    )['Items']

    air_strikes = get_air_strike_oblasts()
    print(f"Air strikes: {', '.join(air_strikes)}")

    for item in items:
        id = item['id']['S']
        ts = datetime.fromisoformat(item['pong']['S'])
        status = item['electricity_status']['S']
        disabled = item['disabled']['BOOL']
        oblast = item['address']['M'].get('oblast', {}).get('S')

        if oblast in air_strikes:
            print("Skip check for electricity status due to air strike")
            continue
        if not oblast:
            print("Skip check for electricity status due to missing oblast")
            continue

        address = readable_address(item)

        now = datetime.now()

        print(f"Address: {address}")
        print(f"State: {status}")
        print(f"TS: {ts}")

        if disabled:
            print("Disabled")
            continue

        status_change = False

        if ((now - ts).total_seconds() > 60 * 7) and status == "on":
            status = "off"
            status_change = True

        if ((now - ts).total_seconds() <= 60 * 7) and status == "off":
            status = "on"
            status_change = True

        if status_change:
            dynamodb.update_item(
                TableName='eSvitlo',
                Key={'id': {"S": id}},
                UpdateExpression="set electricity_status=:electricity_status",
                ExpressionAttributeValues={":electricity_status": {"S": status}}
            )
            sns.publish(
                TopicArn=os.environ["SNS_TOPIC_ARN"],
                Message=json.dumps({"id": id, "status": status, "default": f"{address} - {status}"}),
                MessageStructure="json",
                Subject=id,
            )

    return {
        'statusCode': 200,
        'body': json.dumps('Ok')
    }
