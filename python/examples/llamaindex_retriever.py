# pip install "web2md-client[llamaindex]" llama-index-embeddings-fastembed
from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from web2md_client.llamaindex import Web2MDReader

Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")
docs = Web2MDReader(max_tokens=400).load_data(["https://en.wikipedia.org/wiki/Retrieval-augmented_generation"])
index = VectorStoreIndex.from_documents(docs)
for hit in index.as_retriever(similarity_top_k=3).retrieve("What problem does RAG solve?"):
    print(hit.node.metadata.get("heading_path"), hit.node.get_content()[:200])
