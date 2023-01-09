import boto3

dynamodb = boto3.client('dynamodb')


def readable_address(item):
    address = item["address"]["M"]
    return ', '.join((address["city"]["S"], address["street"]["S"], address["building"]["S"]))


def lambda_handler(event, context):
    items = dynamodb.scan(
        TableName='eSvitlo',
    )['Items']

    response = []
    for item in items:
        address = item["address"]["M"]
        address_response = readable_address(item)
        lat = address["lat"]["N"]
        lng = address["lng"]["N"]

        item_response = {
            "electricity_status": item['electricity_status']['S'],
            "lat": lat,
            "lng": lng,
            "address": address_response,
            "channel_link": item["channel_link"]["S"]
        }
        response.append(item_response)

    return response
