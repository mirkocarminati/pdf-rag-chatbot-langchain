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

The following diagram shows the architecture of the embedding solution:

![embedding-solution](https://github.com/user-attachments/assets/91b85eb6-7b01-452c-ac56-91c0988f46ea)

  
The embedding process is summarized below:

1. A PDF document is uploaded to the S3 bucket and an S3 event triggers the ExtractMetadata Lambda function.
2. The ExtractMetadata Lambda function extracts metadata from the PDF document and sends a message to the SQS queue with the metadata.
3. The GenerateEmbeddings Lambda function reads the message from the SQS queue and generates embeddings from the PDF document using LangChain and Amazon Bedrock. The embeddings are stored in the same S3 bucket.

We will use the AWS SAM CLI configured with the _samconfig.toml_ file to deploy the embedding application.
```
sam deploy --resolve-image-repos
```

## Chatbot Application Overview

The application code has already been built and packaged into a Docker image. The Docker image will be deployed to an Amazon ECS Service using the AWS Serverless Application Model (SAM) CLI.

The _Main.py_ file contains the Streamlit application code that will be deployed to the ECS Service. The streamlit framework is used to render the user interface and interact with the chatbot application.

The LangChain methods used in the application include:

- LangChain Hub: opens in a new tab: a version control system for LLM prompts. You can import prompts to use in your applications. 
- BedrockLLM: LangChain BedrockLLM is used to generate responses for the chatbot. The amazon.titan-text-express-v1 model will be used to generate text responses for the chatbot.
- BedrockEmbeddings: this class generates embeddings for the uploaded PDF documents, the amazon.titan-embed-text-v1 model will be used to generate embeddings for the uploaded documents.
- FAISS: this class is used as the vector store to store the embeddings and create the index. FAISS is a library for efficient similarity search and clustering of dense vectors.
- ConversationalRetrievalChain: a conversational retrieval chain uses a vector store to represent the documents in the embedding space and uses a retrieval model to retrieve the most relevant documents based on the query.
- LangChain Debugging: setting the set_debug method to True will enable debugging mode for the LangChain framework.

The _generate_chat_ function contains the main logic for the chatbot application. This function employs the retrieval-augmented generation technique to generate responses for the chatbot. It accepts a user prompt and a file_name to begin the conversation. The function performs the following steps:

- The embedding solution creates a folder with the index files for each document. The index files generated for the uploaded PDF documents are loaded into memory.
- The BedrockLLM is initialized with the _amazon.titan-text-express-v1_ model and AWS credentials. The Docker image used to deploy this application will have IAM roles attached to it through the Amazon ECS task role, removing the need to hardcode the AWS credentials.
- The BedrockEmbeddings class is initialized with _the amazon.titan-embed-text-v1 model_. This embeddings object will be used to embed user prompts.
- The _index.faiss_ and _index.pkl_ files are loaded into a FAISS index object. The object can then be used as a retriever to fetch documents from the index vector store relevant to the user prompt.
- The _hub.pull_ method is used to pull the RAG prompt from the LangChain Hub. The rlm/rag-prompt, opens in a new tab is used to generate responses for the chatbot.
- The ConversationalRetrievalChain is initialized with the llm, retriever, and rag_prompt. The _return_source_documents_ parameter is set to False to return the generated response only.
- The conversation chain is invoked by passing in the question and chat_history arguments. Chat history is used to maintain the context of the conversation.
