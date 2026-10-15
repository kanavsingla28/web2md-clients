# pip install "web2md-client[langchain]" langchain-community fastembed
# export RAPIDAPI_KEY=...  (free key: https://rapidapi.com/kanavsingla28/api/web2md-webpage-to-markdown-rag-chunks)
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore

from web2md_client.langchain import Web2MDLoader

docs = Web2MDLoader(["https://en.wikipedia.org/wiki/Retrieval-augmented_generation"], max_tokens=400).load()
store = InMemoryVectorStore.from_documents(docs, FastEmbedEmbeddings())
for hit in store.similarity_search("What problem does RAG solve?", k=3):
    print(f"[{hit.metadata['heading_path'] or hit.metadata.get('title', '')}]", hit.page_content[:300], "\n")
