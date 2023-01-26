import json
import os

import boto3

sns = boto3.client("sns")


def lambda_handler(event, context):
    for record in event["Records"]:
        dynamo_key = record['dynamodb']['Keys']['id']['N']

        sns.publish(
            TopicArn=os.environ["SNS_TOPIC_ARN"],
            Message=json.dumps({"id": dynamo_key, "default": dynamo_key}),
            MessageStructure="json",
            Subject=dynamo_key,
        )

    return {
        'statusCode': 200,
        'body': json.dumps('Ok')
    }
