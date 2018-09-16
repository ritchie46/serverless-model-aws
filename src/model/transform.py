import json
import os
import io
import time
from datetime import datetime
import boto3
import pandas as pd
from model import modelwrapper
from cloudhelper import open_s3_file, write_s3_string

sqs = boto3.resource('sqs', region_name=modelwrapper.config['AWS_REGION'])
s3 = boto3.resource('s3', region_name=modelwrapper.config['AWS_REGION'])


class BatchTransformJob:
    def __init__(self, q_name):
        self.q_name = q_name
        self.q = sqs.get_queue_by_name(
            QueueName=q_name
        )
        self.messages = None

    def fetch_messages(self):
        self.messages = self.q.receive_messages()
        return self.messages

    def process_q(self):
        for message in self.messages:
            m = json.loads(message.body)

            print(f"Downloading key: {m['key']} from bucket: {m['bucket']}")

            f = open_s3_file(m['bucket'], m['key'])
            x = pd.read_csv(f)

            print('Invoked with {} records'.format(x.shape[0]))
            # Do the prediction
            predictions = modelwrapper.predict(x)

            f = io.StringIO()
            predictions.to_csv(f, index=False)
            if write_s3_string(bucket=m['output_bucket'],
                               key=os.path.join(f"{m['output_key']}",
                                                datetime.now().strftime('%d-%m-%Y'), f"{int(time.time())}.csv"),
                               f=f):
                print('Success, delete message.')
                message.delete()


def run_batch_transform_job():
    btj = BatchTransformJob(os.environ['SQS_QUEUE'])

    t0 = time.time()
    btj.fetch_messages()

    c = 0
    while len(btj.messages) == 0:
        c += 1
        back_off = 2 ** c
        print(f'No messages ready, back off for {back_off} seconds.')

        time.sleep(back_off)  # back off
        btj.fetch_messages()

        if (time.time() - t0) > 900:
            print('Maximum time exceeded, close the container')
            return False

    print('Found messages, process the queue')
    btj.process_q()



