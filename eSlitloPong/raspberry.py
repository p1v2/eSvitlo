import json
import os

import boto3

lambda_ = boto3.client('lambda')

payload = {"id": os.environ["ADDRESS_ID"]}

if __name__ == "__main__":
    lambda_.invoke(
        FunctionName="eSvitloPong",
        InvocationType='RequestResponse',
        Payload=json.dumps(payload).encode(),
    )
