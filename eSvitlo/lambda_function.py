import json
import os
from datetime import datetime
import urllib.request

import boto3

dynamodb = boto3.client("dynamodb")
sns = boto3.client("sns")


TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]


def send_telegram_message(chat_id: int, message: str):
    url = "https://api.telegram.org/bot{}/sendMessage"

    request = urllib.request.Request(url)
    request.add_header('Content-Type', 'application/json; charset=utf-8')
    jsonData = json.dumps({
            "chat_id": chat_id,
            "text": message,
        })
    jsonBytes = jsonData.encode()
    request.add_header('Content-Length', str(len(jsonBytes)))
    urllib.request.urlopen(request, jsonBytes)


def readable_address(item):
    address = item["address"]["M"]
    return ', '.join((address["city"]["S"], address["street"]["S"], address["building"]["S"]))


def lambda_handler(event, context):
    items = dynamodb.scan(
        TableName='eSvitlo',
    )['Items']

    for item in items:
        id = item['id']['S']
        ts = datetime.fromisoformat(item['pong']['S'])
        status = item['electricity_status']['S']
        channel_id = int(item['channel_id']['S'])

        address = readable_address(item)

        now = datetime.now()

        print(f"Address: {address}")
        print(f"State: {status}")
        print(f"TS: {ts}")

        status_change = False

        if ((now - ts).total_seconds() > 60 * 5) and status == "on":
            send_telegram_message(channel_id, "Немає світла 🕯")
            status = "off"
            status_change = True

        if ((now - ts).total_seconds() <= 60 * 5) and status == "off":
            send_telegram_message(channel_id, "Є світло 💡")
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
                MessageStructure="json"
            )

    return {
        'statusCode': 200,
        'body': json.dumps('Ok')
    }
