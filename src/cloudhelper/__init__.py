import io
import boto3


def open_s3_file(bucket, key):
    """
    Open a file from s3 and return it as a file handler.
    :param bucket: (str)
    :param key: (str)
    :return: (stream)
    """
    f = io.BytesIO()
    bucket = boto3.resource('s3').Bucket(bucket)
    bucket.Object(key).download_fileobj(f)
    f.seek(0)
    return f


def write_s3_file(bucket, key, f):
    f.seek(0)
    bucket = boto3.resource('s3').Bucket(bucket)
    bucket.Object(key).upload_fileobj(f)


def write_s3_string(bucket, key, f):
    try:
        f.seek(0)
        bf = io.BytesIO()
        bf.write(f.read().encode('utf-8'))
        bf.seek(0)
        bucket = boto3.resource('s3').Bucket(bucket)
        bucket.Object(key).upload_fileobj(bf)
    except Exception as e:
        print('Exception: ', e)
    return True

