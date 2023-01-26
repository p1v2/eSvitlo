import json
import traceback

from api import api
from buttons import change_address_button, schedule_button
from dynamodb import dynamodb
from utils import get_schedule, get_schedule_message
from viberbot.api.messages import TextMessage, KeyboardMessage


def get_addresses(schedule_item) -> [str]:
    addresses_items = schedule_item["addresses"]["L"]

    return list(map(lambda item: item["S"], addresses_items))


def send_message_to_records(records, message):
    for record in records:
        sender_id = record['id']['S']
        try:
            api.send_messages(sender_id, messages=[TextMessage(text=message), KeyboardMessage(
                tracking_data='choice',
                keyboard={
                    'Type': "keyboard",
                    'Buttons': [
                        schedule_button,
                        change_address_button
                    ]
                }
            )])
        except:
            traceback.print_exc()


def schedule_change_handler(sns_record, all_viber_records):
    id = sns_record['Sns']['Subject']

    schedule_item = dynamodb.get_item(
        TableName='eSvitloSchedule',
        Key={'id': {'N': id}}
    )['Item']

    schedule = get_schedule(schedule_item)

    date_start = schedule_item["date_start"]["S"]

    message = get_schedule_message(schedule, date_start)

    addresses = get_addresses(schedule_item)

    records = list(filter(lambda viber_record: viber_record["address"]["S"] in addresses, all_viber_records))

    send_message_to_records(records, message)


def status_change_handler(sns_record, all_viber_records):
    id = sns_record['Sns']['Subject']

    esvitlo_item = dynamodb.get_item(
        TableName='eSvitlo',
        Key={'id': {'S': id}}
    )['Item']
    status = esvitlo_item['electricity_status']['S']

    records = list(filter(lambda viber_record: 'address' in viber_record and viber_record["address"]["S"] == id, all_viber_records))

    if status == "off":
        message = "Немає світла 🕯"
    else:
        message = "Є світло 💡"

    send_message_to_records(records, message)


def sns_handler(event):
    all_viber_records = dynamodb.scan(TableName='eSvitloViber')['Items']

    for sns_record in event['Records']:
        topic = sns_record['Sns']['TopicArn']

        if 'eSvitloScheduleChange' in topic:
            schedule_change_handler(sns_record, all_viber_records)
        elif 'eSvitlo' in topic:
            status_change_handler(sns_record, all_viber_records)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
