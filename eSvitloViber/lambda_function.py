import boto3

from sns import sns_handler
from webhook import viber_webhook_handler

dynamodb = boto3.client("dynamodb")


def lambda_handler(event, context):
    if 'Records' in event:
        return sns_handler(event)
    else:
        return viber_webhook_handler(event)

