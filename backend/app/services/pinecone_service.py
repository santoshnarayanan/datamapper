import os
from pinecone import Pinecone

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

index = pc.Index(host=os.getenv("PINECONE_HOST"))


def upsert_vectors(vectors):
    """
    vectors = [
        {
            "id": "unique-id",
            "values": [...embedding...],
            "metadata": {...}
        }
    ]
    """
    index.upsert(vectors=vectors)


def query_vector(vector, top_k=1):
    result = index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=True
    )
    return result.matches