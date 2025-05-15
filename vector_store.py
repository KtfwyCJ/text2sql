from chromadb import Client
import chromadb.config
from sentence_transformers import SentenceTransformer, util

class RAGRetriever:
    def __init__(self, collection_name="schema_chunks"):
        self.client = Client(settings=chromadb.config.Settings(allow_reset=True))
        if collection_name in [col.name for col in self.client.list_collections()]:
            self.collection = self.client.get_collection(name=collection_name)
        else:
            self.collection = self.client.create_collection(name=collection_name)

        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    def add_chunks(self, chunks):
        embeddings = self.embedder.encode(chunks, convert_to_tensor=True)
        self.collection.add(
            documents=chunks,
            metadatas=[{"chunk_id": i} for i in range(len(chunks))],
            ids=[str(i) for i in range(len(chunks))],
            embeddings=embeddings.cpu().numpy()
        )
            

    def retrieve(self, query, k=3):
        query_embedding = self.embedder.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        return results["documents"][0]

    def relevance_score(self, query):
        query_embedding = self.embedder.encode(query, convert_to_tensor=True)
        docs = self.collection.get()["documents"]
        schema_text = " ".join(docs)
        schema_embedding = self.embedder.encode(schema_text, convert_to_tensor=True)
        return util.pytorch_cos_sim(query_embedding, schema_embedding).item()
