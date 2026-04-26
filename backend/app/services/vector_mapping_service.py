import uuid
from app.services.embedding_service import get_embedding
from app.services.pinecone_service import upsert_vectors, query_vector
import os


# Store target columns as embeddings for semantic matching
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


# Store mapping history to enable learning from previous mappings
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


# Perform semantic search using embedding similarity
# Falls back when rule-based confidence is low
def semantic_search_candidates(source_column):
    embedding = get_embedding(source_column)
    matches = query_vector(embedding, top_k=10)

    unique_targets = {}
    results = []

    for m in matches:
        metadata = m.metadata

        # 🔴 Skip knowledge entries
        if metadata.get("type") == "knowledge":
            continue

        # 🟢 Handle target type
        if metadata.get("type") == "target":
            target = metadata.get("column")

        # 🟢 Handle mapping history
        elif metadata.get("type") == "mapping":
            target = metadata.get("target")

        else:
            continue

        if not target:
            continue

        # Deduplicate (keep highest score)
        if target not in unique_targets or m.score > unique_targets[target]:
            unique_targets[target] = m.score

    for target, score in unique_targets.items():
        results.append({
            "target": target,
            "score": score
        })

    return results


def store_domain_knowledge():
    knowledge = [
        "Acct No means Account Number",
        "Cust Ref means Customer Identification",
        "Loan No means Loan Identification"
    ]

    vectors = []

    for text in knowledge:
        vectors.append({
            "id": f"knowledge-{text}",
            "values": get_embedding(text),
            "metadata": {
                "type": "knowledge",
                "text": text
            }
        })

    upsert_vectors(vectors)


def load_domain_knowledge_from_file(file_path="domain_knowledge.txt"):
    """
    Load domain knowledge from text file and store in Pinecone
    """

    # Build absolute path (important)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    full_path = os.path.join(base_dir, file_path)

    if not os.path.exists(full_path):
        print(f"File not found: {full_path}")
        return

    with open(full_path, "r") as f:
        lines = f.readlines()

    vectors = []

    for line in lines:
        text = line.strip()

        if not text:
            continue

        vectors.append({
            "id": f"knowledge-{text}",  # prevents duplicates
            "values": get_embedding(text),
            "metadata": {
                "type": "knowledge",
                "text": text
            }
        })

    if vectors:
        upsert_vectors(vectors)
        print(f"Loaded {len(vectors)} knowledge entries into Pinecone")


def get_domain_knowledge(source_column):
    embedding = get_embedding(source_column)
    matches = query_vector(embedding, top_k=10)

    knowledge = []

    for m in matches:
        if m.metadata.get("type") == "knowledge":
            knowledge.append(m.metadata.get("text"))

    return knowledge