import os
from pinecone import Pinecone

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

index = pc.Index(host=os.getenv("PINECONE_HOST"))


# Upsert vectors into Pinecone (handles both insert and update)
# Vectors include embeddings + metadata for semantic search
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

# Query Pinecone for top_k most similar vectors
# Returns similarity score + metadata (computed at query time)
def query_vector(vector, top_k=3):
    result = index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=True
    )
    return result.matches