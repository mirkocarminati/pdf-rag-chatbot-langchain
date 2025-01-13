import os
import time
import boto3
import streamlit as st
from langchain import hub
from langchain_aws import BedrockLLM
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.globals import set_debug

set_debug(True)

s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime')
bucket_name = os.environ.get('BUCKET_NAME')

# Upload PDF files to S3
def upload_to_s3(objects):
    for o in objects:
        s3.upload_fileobj(o, bucket_name, o.name)
        msg = st.toast('Uploading...', icon='⏳')
        time.sleep(1)
        msg.toast('File successfully uploaded', icon='🎉')

# Simulate a stream response
def stream_response(answer):
    for word in answer.split():
        yield word + " "
        time.sleep(0.05)

# Generate a conversation chain
def generate_chat(prompt, file_name):

    # Retrieving index files from S3
    s3.download_file(bucket_name, f"{file_name}/index.faiss", "tmp/index.faiss")
    s3.download_file(bucket_name, f"{file_name}/index.pkl", "tmp/index.pkl")

    # Defining a language model
    llm = BedrockLLM(
        client=bedrock, 
        model_id="amazon.titan-text-express-v1",
        credentials_profile_name="default"
    )

    # Configuring the retriever
    embeddings = BedrockEmbeddings(
        model_id="amazon.titan-embed-text-v1",
        client=bedrock,
        region_name="us-west-2",
    )
    faiss_index = FAISS.load_local(
        "tmp", 
        embeddings, 
        allow_dangerous_deserialization=True
    )
    retriever = faiss_index.as_retriever()

    # Pulling a prompt
    rag_prompt = hub.pull("rlm/rag-prompt")

    # Creating a conversation chain
    conversation = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=False,
        combine_docs_chain_kwargs={"prompt": rag_prompt}
    )
    
    # Invoking the conversation chain
    results = conversation.invoke({'question': prompt, 'chat_history': []})
    return results['answer']

# Streamlit UI
st.set_page_config(
    page_title="PDF Chatbot", 
    layout="centered"
)

# S3 Upload and Select Sidebar
with st.sidebar:

    # Upload S3 files
    with st.container(border=True):
        st.header(f":red[Upload] a PDF file")
        objects = st.file_uploader(label=f"Uploading to: __{bucket_name}__", type="pdf",accept_multiple_files=True)
        st.button("Upload", on_click=upload_to_s3, args=[objects])

    # Select S3 file
    with st.container(border=True):
        st.header(f":red[Select] a PDF file")
        response = s3.list_objects_v2(Bucket=bucket_name)
        object_list = []

        if 'Contents' in response:
            for obj in response['Contents']:
                if not obj['Key'].endswith('/') and obj['Key'].endswith('.pdf'):
                    object_list.append(obj['Key'])
        else:
            st.write(f"S3 bucket is empty")

        selected_obj = st.selectbox(f"Select a file to begin", object_list, index=None)

# Chat UI Elements

st.title(f":red[Chat] with a PDF file")
if selected_obj is None:
    st.caption("Please select a PDF to begin a conversation")
else:
    st.caption(f"Chatting with __{selected_obj}__")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        if message["file"] == selected_obj:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
    if prompt := st.chat_input("What is up?", key="prompt"):
        st.session_state.chat_history.append({"file": selected_obj, "role": "user", "content": prompt})

        with st.chat_message("user"):
            st.write(prompt)

        payload = generate_chat(prompt, selected_obj)

        with st.chat_message("assistant"):
            st.write_stream(stream_response(payload))

        st.session_state.chat_history.append({"file": selected_obj, "role": "assistant", "content": payload})