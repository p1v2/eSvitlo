import json
import os

import boto3
import urllib.request

dynamodb = boto3.client('dynamodb')


TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]


def send_telegram_message(chat_id: int, message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

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
    for record in event['Records']:
        id = record['Sns']['Subject']

        dynamo_response = dynamodb.get_item(
            TableName='eSvitlo',
            Key={'id': {'S': id}}
        )

        item = dynamo_response['Item']

        status = item['electricity_status']['S']
        channel_id = int(item['channel_id']['S'])

        address = readable_address(item)

        print(f"Address: {address}")
        print(f"State: {status}")

        if status == "off":
            send_telegram_message(channel_id, f"Немає світла 🕯")
        elif status == "on":
            send_telegram_message(channel_id, f"Є світло 💡")

    return {
        'statusCode': 200,
        'body': "OK"
    }
