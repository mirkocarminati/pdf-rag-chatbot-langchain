import os
import json
import boto3
import PyPDF2
import shortuuid
import urllib
from datetime import datetime

DOCUMENT_TABLE = os.environ["DOCUMENT_TABLE"]
QUEUE = os.environ["QUEUE"]
BUCKET = os.environ["BUCKET"]

ddb = boto3.resource("dynamodb")
document_table = ddb.Table(DOCUMENT_TABLE)
sqs = boto3.client("sqs")
s3 = boto3.client("s3")

def lambda_handler(event, context):
    key = urllib.parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"])
    split = key.split("/")
    file_name = split[0]
    document_id = shortuuid.uuid()

    s3.download_file(BUCKET, key, f"/tmp/{file_name}")

    with open(f"/tmp/{file_name}", "rb") as f:
        reader = PyPDF2.PdfReader(f)
        pages = str(len(reader.pages))

    timestamp = datetime.utcnow()
    timestamp_str = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    document = {
        "document_id": document_id,
        "filename": file_name,
        "created": timestamp_str,
        "pages": pages,
        "filesize": str(event["Records"][0]["s3"]["object"]["size"]),
        "docstatus": "UPLOADED"
    }

    document_table.put_item(Item=document)

    message = {
        "documentid": document_id,
        "created": timestamp_str,
        "key": key,
    }

    sqs.send_message(QueueUrl=QUEUE, MessageBody=json.dumps(message))