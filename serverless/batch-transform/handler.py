import json
import time
import random
import os
import re
from datetime import date, datetime
import boto3

# SETTINGS
DESIRED_COUNT = int(os.environ['DESIRED_COUNT'])
OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET']
OUTPUT_KEY = os.environ['OUTPUT_KEY']
SQS_NAME = os.environ['RESOURCE_NAME']
ECS_CLUSTER = os.environ['RESOURCE_NAME']
TASK_DEFINITION = os.environ['RESOURCE_NAME']
SUBNET = os.environ['SUBNET']
SECURITY_GROUP = os.environ['SECURITY_GROUP']
MODEL = os.environ['MODEL']

s3 = boto3.resource('s3')
sqs = boto3.resource('sqs')
ecs_client = boto3.client('ecs')


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def lambda_handler(event, context):
    try:
        # determine the version of the latest data partitions.
        q = re.compile(r'version=(\d*)')
        version = max(map(lambda x: 0 if x is None else int(x.group(1)),
                          map(lambda x: q.search(x['Key']),
                              boto3.client('s3').list_objects_v2(Bucket=OUTPUT_BUCKET,
                                                                 Prefix=os.path.join(OUTPUT_KEY, f'model={MODEL}'))[
                                  'Contents']))) + 1
    except KeyError:
        version = 0

    # Add messages to SQS Queue.
    # The message contains:
    # {   bucket: <input-data-bucket>,
    #     key: <input-data-key>,
    #     output_bucket: <storage-bucket>,
    #     output_key: <storage-key>
    #     model: <model-name>
    #     version: <int>
    # }
    event_info = event['Records'][0]['s3']
    key = event_info['object']['key']
    q = sqs.get_queue_by_name(QueueName=SQS_NAME)
    message = json.dumps(dict(
        bucket=event_info['bucket']['name'],
        key=key,
        output_bucket=OUTPUT_BUCKET,
        output_key=OUTPUT_KEY,
        model=MODEL,
        version=version))

    print(f'Add {message} to queue')
    response = q.send_message(
        MessageBody=message
    )

    # Add the key as seed so that all lambda sleep different times.
    # Otherwise N files lead to N tasks
    # The first sleep is so that the tasks don't start before the lambda's are finished. This will result in different
    # versions.
    time.sleep(60 + 120 * random.Random(key).random())
    # if needed start the container in ECS
    if len(ecs_client.list_tasks(cluster=ECS_CLUSTER)['taskArns']) == 0:

        print('RUN ECS task')

        response = ecs_client.run_task(
            cluster=ECS_CLUSTER,
            taskDefinition=TASK_DEFINITION,
            count=DESIRED_COUNT,
            launchType='FARGATE',
            networkConfiguration=dict(
                awsvpcConfiguration=dict(subnets=[SUBNET],
                                         securityGroups=[SECURITY_GROUP],
                                         assignPublicIp='ENABLED')

            ),
        )
    else:
        print('ECS cluster already running, lay back')

    return {
        "statusCode": 200,
        "body": json.dumps(response, default=json_serial)
    }
