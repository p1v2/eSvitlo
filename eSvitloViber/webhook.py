import json

import boto3

from api import api
from buttons import start_button, schedule_button, change_address_button
from utils import get_schedule, get_schedule_message
from viberbot.api.messages import KeyboardMessage
from viberbot.api.messages.text_message import TextMessage

dynamodb = boto3.client("dynamodb")


def get_viber_item(sender_id):
    key = {'id': {'S': sender_id}}
    print(key)
    item = dynamodb.get_item(TableName='eSvitloViber', Key=key).get('Item')
    print(item)

    if not item:
        item = {**key, 'bot_state': {'S': 'hello'}}
        dynamodb.put_item(TableName='eSvitloViber', Item=item)

    return item


def readable_address(item):
    address = item["address"]["M"]
    return ', '.join((address["city"]["S"], address["street"]["S"], address["building"]["S"]))


def get_addresses_items():
    items = dynamodb.scan(
        TableName='eSvitlo',
    )['Items']

    return {
        item['id']['S']: readable_address(item)
        for item in items
    }


def get_addresses():
    return get_addresses_items().values()


def get_user_schedule_item(user_id):
    viber_item = dynamodb.get_item(
        TableName='eSvitloViber',
        Key={'id': {'S': user_id}}
    )['Item']
    address_id = viber_item["address"]["S"]

    schedules = dynamodb.scan(
        TableName='eSvitloSchedule'
    )["Items"]

    for schedule in schedules:
        addresses = list(map(lambda address_item: address_item["S"], schedule["addresses"]["L"]))

        if address_id in addresses:
            return schedule


def update_state(sender_id, state):
    dynamodb.update_item(
        TableName='eSvitloViber',
        Key={'id': {"S": sender_id}},
        UpdateExpression="set bot_state=:bot_state",
        ExpressionAttributeValues={":bot_state": {"S": state}}
    )


def update_address(sender_id, address):
    dynamodb.update_item(
        TableName='eSvitloViber',
        Key={'id': {"S": sender_id}},
        UpdateExpression="set address=:address",
        ExpressionAttributeValues={":address": {"S": address}}
    )


def message_handler(body):
    sender_id = body['sender']['id']
    text = body['message']['text']

    viber_item = get_viber_item(sender_id)
    state = viber_item['bot_state']['S']

    if "графік" in text.lower():
        schedule_item = get_user_schedule_item(sender_id)
        schedule = get_schedule(schedule_item)
        schedule_message = get_schedule_message(schedule, schedule_item["date_start"]["S"])

        messages = [TextMessage(text=schedule_message), KeyboardMessage(
            tracking_data='choice',
            keyboard={
                'Type': "keyboard",
                'Buttons': [
                    change_address_button
                ]
            }
        )]

        api.send_messages(
            sender_id,
            messages,
        )

    elif state == "hello":
        addresses = get_addresses()
        messages = [TextMessage(text="Для того щоб надсилати Вам сповіщення, бот повинен зберігати інформацію про "
                                     "Вашу адресу. "
                                     "Вибираючи адресу, ви надаєте згоду на зберігання і обробку Ваших даних."),
                    TextMessage(text="Виберіть адресу для продовження:"),
                    KeyboardMessage(
            tracking_data='choice',
            keyboard={
                'Type': "keyboard",
                'Buttons': [
                    {'ActionType': 'reply', "ActionBody": address,
                     "ReplyType": "message", 'Text': address}
                    for address in addresses
                ]
            }
        )]

        api.send_messages(
            sender_id,
            messages,
        )

        update_state(sender_id, "select_address")
    elif state == "select_address":
        addresses = get_addresses_items()

        try:
            address_id, addresses_value = next(
                (key, value) for key, value in addresses.items() if value == text.strip())
            update_state(sender_id, 'hello')
            update_address(sender_id, address_id)
            api.send_messages(sender_id, [
                TextMessage(text=f"Вас було підписано на сповіщення про відключення світла. "
                                 f"Натисніть на кнопки нижче щоб дізнатись актуальний графік або змінити адресу."),
                KeyboardMessage(tracking_data='choice',
                                keyboard={
                                    'Type': "keyboard",
                                    'Buttons': [
                                        schedule_button,
                                        change_address_button
                                    ]
                                })])

        except StopIteration:
            pass


def unsubscribe_handler(body):
    sender_id = body["user_id"]

    dynamodb.delete_item(
        TableName='eSvitloViber',
        Key={'id': {"S": sender_id}},
    )


def conversation_started_handler(body):
    user_id = body["user"]["id"]

    messages = [KeyboardMessage(
        tracking_data='choice',
        keyboard={
            'Type': "keyboard",
            'Buttons': [
                start_button
            ]
        }
    )]

    update_state(user_id, 'hello')

    api.send_messages(
        user_id,
        messages,
    )


def viber_webhook_handler(event):
    print(event)
    body = json.loads(event['body'])
    event = body["event"]
    print(body)

    if event == "message":
        message_handler(body)
    elif event == "unsubscribe":
        message_handler(body)
    elif event == "conversation_started":
        conversation_started_handler(body)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
