from sentence_transformers import SentenceTransformer
import faiss
import os
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

def load_documents(folder_path):
    documents = []
    for file in os.listdir(folder_path):
        with open(os.path.join(folder_path, file), "r", encoding="utf-8") as f:
            documents.append(f.read())
    return documents

def create_vector_store(documents):
    embeddings = model.encode(documents)
    dimension = embeddings.shape[1]
    
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))
    
    return index, documents

def retrieve(query, index, documents, top_k=2):
    query_embedding = model.encode([query])
    distances, indices = index.search(np.array(query_embedding), top_k)
    
    results = [documents[i] for i in indices[0]]
    return results