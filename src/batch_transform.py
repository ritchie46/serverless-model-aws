from wsgi import app
from model.sqs import run_batch_transform_job

run_batch_transform_job()