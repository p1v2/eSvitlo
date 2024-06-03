import re
from io import BytesIO

import boto3
from PyPDF2 import PdfReader

dynamodb = boto3.client("dynamodb")
s3 = boto3.client("s3")

addresses_regex = {
    1: r"Крушельницької.*69",
    2: r"Тракторна.*7",
    3: r"Відінська.*35а"

}
schedule_regex = r"([0-9]{2}:[0-9]{2}-[0-9]{2}:[0-9]{2})+"


def get_reader(s3_key):
    s3_body = BytesIO(s3.get_object(Bucket="e-svitlo-schedules", Key=s3_key)["Body"].read())
    return PdfReader(s3_body)


def find_schedule(reader, regex):
    for page_number in range(len(reader.pages)):
        page = reader.pages[page_number]

        text = page.extract_text()

        lines = text.split("\n")

        for i, line in enumerate(lines):
            if re.search(regex, line):
                for another_line in lines[i:]:
                    if re.search(schedule_regex, another_line):
                        return re.findall(schedule_regex, another_line)


def to_turn_offs(schedule):
    schedule_items = [item.split("-") for item in schedule]
    sorted_schedule_items = sorted(schedule_items, key=lambda item: (int(item[0].split(":")[0]) - 7) % 24)
    return [
        {"M": {"start": {"S": item[0]}, "end": {"S": item[1]}}}
        for item in sorted_schedule_items
    ]


def record_handler(record, items):
    key = record["s3"]["object"]["key"]

    reader = get_reader(key)

    for item in items:
        turn_offs = item["turn_offs"]["L"]
        id = item["id"]["N"]
        regex = addresses_regex[int(id)]

        new_schedule = find_schedule(reader, regex)
        print(new_schedule)
        new_turn_offs = to_turn_offs(new_schedule)

        if new_turn_offs == turn_offs:
            print(f"{id} - unchanged")
            continue

        print(f"{id} - changed")

        print(turn_offs)
        print(new_turn_offs)
        # dynamodb.update_item(
        #     TableName='eSvitloSchedule',
        #     Key={'id': {"N": id}},
        #     UpdateExpression="set turn_offs=:turnOffs",
        #     ExpressionAttributeValues={":turnOffs": {"L": new_turn_offs}}
        # )


def lambda_handler(event, context):
    items = dynamodb.scan(TableName='eSvitloSchedule')['Items']

    for record in event["Records"]:
        record_handler(record, items)
