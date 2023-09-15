#!/usr/bin/env python
import datetime
import json
import os
import time

import boto3
import requests

JENKINS_URL = os.environ['JENKINS_URL']
SQS_ENDPOINT_URL = os.environ.get('SQS_ENDPOINT_URL')
SQS_QUEUE = os.environ['SQS_QUEUE']
SQS_REGION = os.environ['SQS_REGION']

if SQS_ENDPOINT_URL:
    sqs = boto3.resource('sqs',
                         endpoint_url=SQS_ENDPOINT_URL,
                         region_name=SQS_REGION,
                         use_ssl=False)
else:
    sqs = boto3.resource('sqs', region_name=SQS_REGION)

print("Webhook consumer starting up!")

while True:
    queue = sqs.get_queue_by_name(QueueName=SQS_QUEUE)
    message_list = queue.receive_messages(
        WaitTimeSeconds=5,
        MaxNumberOfMessages=10
    )
    if not message_list:
        time.sleep(5)
        continue

    for message in message_list:
        print(f"Got message: {message.message_id} at {datetime.datetime.now().isoformat()}")
        parsed = json.loads(message.body)
        original_headers = parsed['headers']
        payload = parsed['payload']

        # Set up our headers.
        headers = {}
        headers['Content-Type'] = "application/json"
        headers['X-Github-Event'] = original_headers['X-Github-Event']

        # Post the message to jenkins.
        resp = requests.post(
            JENKINS_URL,
            headers=headers,
            data=json.dumps(payload),
            verify=False
        )
        print(resp.text)

        # Delete the message if we made it this far.
        queue.delete_messages(Entries=[dict(
            Id=message.message_id,
            ReceiptHandle=message.receipt_handle
        )])

    time.sleep(5)
