import io
import boto3


def open_s3_file(bucket, key):
    """
    Open a file from s3 and return it as a file handler.
    :param bucket: (str)
    :param key: (str)
    :return: (BytesIO buffer)
    """
    f = io.BytesIO()
    bucket = boto3.resource('s3').Bucket(bucket)
    bucket.Object(key).download_fileobj(f)
    f.seek(0)
    return f


def write_s3_file(bucket, key, f):
    """
    Write a file buffer to the given S3 location.
    :param bucket: (str)
    :param key: (str)
    :param f: (BytesIO buffer)
    """
    f.seek(0)
    bucket = boto3.resource('s3').Bucket(bucket)
    bucket.Object(key).upload_fileobj(f)


def write_s3_string(bucket, key, f):
    """
    Write a StringIO file buffer to S3.
    :param bucket: (str)
    :param key: (str)
    :param f: (StringIO buffer)
    """
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

