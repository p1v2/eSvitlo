import asyncio.exceptions
import json

import aiohttp
from datetime import datetime

import boto3


dynamodb = boto3.client("dynamodb")


async def ping_router(ip: str, port: str):
    async with aiohttp.ClientSession() as session:
        try:
            await session.head(url=f"http://{ip}:{port}", timeout=10)
            return True
        except (asyncio.exceptions.TimeoutError, aiohttp.ClientConnectorError):
            return False


async def item_handler(item):
    id = item['id']['S']

    if 'ip' not in item:
        print(f"skip {id}")
        return

    ip = item['ip']['S']
    port = item['port']['S']

    alive = await ping_router(ip, port)

    if alive:
        print(f"{id} is alive")
        pong = datetime.now().isoformat()

        dynamodb.update_item(
            TableName='eSvitlo',
            Key={'id': {"S": id}},
            UpdateExpression="set pong=:pong",
            ExpressionAttributeValues={":pong": {"S": pong}}
        )
    else:
        print(f"{id} is not alive")


async def main():
    items = dynamodb.scan(
        TableName='eSvitlo',
    )['Items']

    coroutines = []
    for item in items:
        coroutines.append(item_handler(item))

    await asyncio.gather(*coroutines)


def lambda_handler(event, context):
    asyncio.run(main())

    return {
        'statusCode': 200,
        'body': json.dumps('Ok')
    }
