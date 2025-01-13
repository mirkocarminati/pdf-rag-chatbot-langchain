import os
import json
import boto3
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain_community.vectorstores import FAISS

DOCUMENT_TABLE = os.environ["DOCUMENT_TABLE"]
BUCKET = os.environ["BUCKET"]

s3 = boto3.client("s3")
ddb = boto3.resource("dynamodb")
document_table = ddb.Table(DOCUMENT_TABLE)

def set_doc_status(document_id, created, status):
    document_table.update_item(
        Key={"document_id": document_id, "created": created},
        UpdateExpression="SET docstatus = :docstatus",
        ExpressionAttributeValues={":docstatus": status},
    )

def lambda_handler(event, context):
    event_body = json.loads(event["Records"][0]["body"])
    document_id = event_body["documentid"]
    created = event_body["created"]
    key = event_body["key"]
    file_name_full = key.split("/")[-1]

    set_doc_status(document_id, created, "PROCESSING")

    s3.download_file(BUCKET, key, f"/tmp/{file_name_full}")
    loader = PyPDFLoader(f"/tmp/{file_name_full}")

    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-west-2",
    )

    embeddings = BedrockEmbeddings(
        model_id="amazon.titan-embed-text-v1",
        client=bedrock_runtime,
        region_name="us-west-2",
    )

    index_creator = VectorstoreIndexCreator(
        vectorstore_cls=FAISS,
        embedding=embeddings,
    )

    index_from_loader = index_creator.from_loaders([loader])
    index_from_loader.vectorstore.save_local("/tmp")

    s3.upload_file(
        "/tmp/index.faiss", BUCKET, f"{file_name_full}/index.faiss"
    )
    s3.upload_file("/tmp/index.pkl", BUCKET, f"{file_name_full}/index.pkl")

    set_doc_status(document_id, created, "READY")