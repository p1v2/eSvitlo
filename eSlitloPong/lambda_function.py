import json
from datetime import datetime

import boto3

dynamodb = boto3.client('dynamodb')


def lambda_handler(event, context):
    id = event['id']

    dynamodb.update_item(
        TableName='eSvitlo',
        Key={'id': {"S": id}},
        UpdateExpression="set pong=:pong",
        ExpressionAttributeValues={":pong": {"S": datetime.now().isoformat()}}
    )

    return {
        'statusCode': 200,
        'body': json.dumps('Ping')
    }
