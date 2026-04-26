import uuid
from app.services.embedding_service import get_embedding
from app.services.pinecone_service import upsert_vectors, query_vector


def store_target_columns(target_columns):
    vectors = []

    for col in target_columns:
        vectors.append({
            "id": f"target-{col}",
            "values": get_embedding(col),
            "metadata": {
                "type": "target",
                "column": col
            }
        })

    upsert_vectors(vectors)


def store_mapping_history(mapping_list):
    vectors = []

    for m in mapping_list:
        text = f"{m['source']['column']} -> {m['target']['column']}"

        vectors.append({
            "id": str(uuid.uuid4()),
            "values": get_embedding(text),
            "metadata": {
                "type": "mapping",
                "source": m["source"]["column"],
                "target": m["target"]["column"]
            }
        })

    upsert_vectors(vectors)

def semantic_search(source_column):
    embedding = get_embedding(source_column)

    matches = query_vector(embedding, top_k=1)

    if not matches:
        return None

    match = matches[0]

    metadata = match.metadata

    if metadata["type"] == "target":
        return metadata["column"]

    if metadata["type"] == "mapping":
        return metadata["target"]

    return None