import os
import time
import faiss
import numpy as np
import streamlit as st
from mistralai import Mistral

# ----------------------
# Initialization
# ----------------------
api_key=os.getenv("MISTRAL_API_KEY")

if not api_key:
    st.error("MISTRAL_API_KEY not found in environment variables.")
    st.stop()

client = Mistral(api_key=api_key)

# ----------------------
# Functions
# ----------------------
def ocr_pdf(file):
    uploaded_pdf = client.files.upload(
        file={"file_name": file.name, "content": file.read()},
        purpose="ocr"
    )
    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
    
    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={"type": "document_url", "document_url": signed_url.url},
        include_image_base64=True
    )
    
    # Combine OCR pages
    full_text = "\n".join([page.markdown for page in ocr_response.pages])
    return full_text

def get_text_embedding(text):
    embeddings_response = client.embeddings.create(
        model="mistral-embed",
        inputs=text
    )
    return embeddings_response.data[0].embedding

def run_mistral(user_message, model="mistral-large-latest"):
    messages = [{"role": "user", "content": user_message}]
    chat_response = client.chat.complete(model=model, messages=messages)
    return chat_response.choices[0].message.content

def create_faiss_index(chunks):
    embeddings = []
    progress_bar = st.progress(0)
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        emb = get_text_embedding(chunk)
        embeddings.append(emb)
        time.sleep(2)
        progress_bar.progress((i + 1) / total)
    embeddings = np.array(embeddings)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index, embeddings


# ----------------------
# Streamlit App
# ----------------------
st.title("📄 PDF Q&A with Mistral & FAISS")
st.write("Upload a PDF, OCR it, and ask questions using LLM with vector search.")

# PDF Upload
uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
if uploaded_file:
    with st.spinner("Running OCR..."):
        text = ocr_pdf(uploaded_file)
    st.success("OCR completed!")
    st.text_area("OCR Text", text, height=300)

    # Chunk text
    chunk_size = 2048
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    # Build FAISS index
    with st.spinner("Creating vector embeddings (may take a few minutes)..."):
        index, text_embeddings = create_faiss_index(chunks)
    st.success("Vector database created!")

    # Question input
    question = st.text_input("Enter your question:")
    if question:
        question_emb = np.array([get_text_embedding(question)])
        D, I = index.search(question_emb, k=2)
        retrieved_chunks = [chunks[i] for i in I[0]]

        prompt = f"""
        Context information is below.
        ---------------------
        {retrieved_chunks}
        ---------------------
        Given the context information, answer the query.
        Query: {question}
        Answer:
        """
        with st.spinner("Generating answer..."):
            response = run_mistral(prompt)
        st.markdown("**Answer:**")
        st.write(response)
