# pdf-rag-chatbot-langchain
Deploying a PDF chatbot that uses retrieval-augmented generation to answer prompts based on embeddings generated from PDF documents.

## Embedding Solution Overview

This project deploys the PDF embedding solution using AWS SAM. At a high level, the solution extracts metadata from PDF documents and generates embeddings using LangChain and Amazon Bedrock.
The PDF chatbot application will use the embeddings to answer user prompts based on the content of the PDF documents.

The solution consists of the following components:

- An S3 bucket to store the PDF documents
- A DynamoDB table to store the metadata and status of the uploaded documents
- A Lambda function to extract metadata from the PDF documents
- A Lambda function to generate embeddings from the PDF documents
- An SQS queue to store the PDF document processing requests
  
The embedding process is summarized below:

1. A PDF document is uploaded to the S3 bucket and an S3 event triggers the ExtractMetadata Lambda function.
2. The ExtractMetadata Lambda function extracts metadata from the PDF document and sends a message to the SQS queue with the metadata.
3. The GenerateEmbeddings Lambda function reads the message from the SQS queue and generates embeddings from the PDF document using LangChain and Amazon Bedrock. The embeddings are stored in the same S3 bucket.

We will use the AWS SAM CLI configured with the _samconfig.toml_ file to deploy the embedding application.
