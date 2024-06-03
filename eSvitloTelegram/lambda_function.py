import json
import os
from datetime import date
from urllib.error import HTTPError

import boto3
import urllib.request

dynamodb = boto3.client('dynamodb')


TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]


def send_telegram_message(chat_id: str, message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    request = urllib.request.Request(url)
    request.add_header('Content-Type', 'application/json; charset=utf-8')
    jsonData = json.dumps({
        "chat_id": chat_id,
        "text": message,
    })
    jsonBytes = jsonData.encode()
    request.add_header('Content-Length', str(len(jsonBytes)))
    try:
        urllib.request.urlopen(request, jsonBytes)
    except HTTPError as error:
        print(error.reason)
        print(error)
        print(error.read())
        print(error.readlines())


def readable_address(item):
    address = item["address"]["M"]
    return ', '.join((address["city"]["S"], address["street"]["S"], address["building"]["S"]))


def get_schedule(schedule_item) -> [[str, str]]:
    turn_offs = schedule_item["turn_offs"]["L"]

    schedule = []

    for turn_off in turn_offs:
        start = turn_off["M"]["start"]["S"]
        end = turn_off["M"]["end"]["S"]

        schedule.append([start, end])

    return schedule


def get_addresses(schedule_item) -> [str]:
    addresses_items = schedule_item["addresses"]["L"]

    return list(map(lambda item: item["S"], addresses_items))


def get_schedule_message(schedule, date_start):
    message = "Графік вимкнення: "

    item_messages = []
    for item in schedule:
        item_messages.append(f"{item[0]}-{item[1]}")

    if str(date.today()) == date_start:
        date_message = "Діє відсьогодні."
    else:
        date_message = "Діє відзавтра."

    return message + ", ".join(item_messages) + ". " + date_message


def get_address_item(id):
    return dynamodb.get_item(
        TableName='eSvitlo',
        Key={'id': {'S': id}}
    )['Item']


def status_change_handler(record):
    id = record['Sns']['Subject']

    item = get_address_item(id)

    status = item['electricity_status']['S']
    channel_id = item['channel_id']['S']

    address = readable_address(item)

    print(f"Address: {address}")
    print(f"State: {status}")

    if status == "off":
        send_telegram_message(channel_id, "Немає світла 🕯")
    elif status == "on":
        send_telegram_message(channel_id, "Є світло 💡")


def schedule_change_handler(record):
    id = record['Sns']['Subject']

    schedule_item = dynamodb.get_item(
        TableName='eSvitloSchedule',
        Key={'id': {'N': id}}
    )['Item']

    schedule = get_schedule(schedule_item)

    date_start = schedule_item["date_start"]["S"]

    message = get_schedule_message(schedule, date_start)

    addresses = get_addresses(schedule_item)

    for address in addresses:
        item = get_address_item(address)

        send_telegram_message(192484569, message)


def lambda_handler(event, context):
    for record in event['Records']:
        topic = record['Sns']['TopicArn']

        if 'eSvitloScheduleChange' in topic:
            schedule_change_handler(record)
        elif 'eSvitlo' in topic:
            status_change_handler(record)

    return {
        'statusCode': 200,
        'body': "OK"
    }
