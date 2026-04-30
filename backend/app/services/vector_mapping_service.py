"""
VECTOR MAPPING SERVICE (Phase 7.7B + Phase 10 Enhancements)

Responsibilities:
- Store embeddings for target columns
- Perform semantic similarity search
- Store mapping history for learning
- Inject feedback-driven candidates

Key Concept:
Semantic retrieval is augmented with feedback to overcome retrieval limitations.
"""

import uuid
from app.services.embedding_service import get_embedding
from app.services.pinecone_service import upsert_vectors, query_vector
from app.repositories.mapping_feedback_repo import get_feedback_mapping
import os


# Store target columns as embeddings for semantic matching
def store_target_columns(target_columns):
    """
    Store target columns as embeddings in vector DB.

    Used for:
    - Semantic similarity matching
    - Candidate retrieval
    """

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
    """
    Store mapping history in vector DB.

    Purpose:
    - Improve future semantic retrieval
    - Enable learning from past mappings
    """

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

# ----------------------------------------
# FEEDBACK-AWARE CANDIDATE INJECTION
# ----------------------------------------
# Ensures feedback targets are considered even if
# semantic search does not return them.
#
# Behavior:
# - Inject feedback.final_field into candidates
# - Assign base score slightly below top match
#
# Why:
# Prevent loss of user intent due to retrieval limitations
def semantic_search_candidates(source_column, db=None, workflow_id=None):
    """
    Perform semantic search using embeddings.

    Enhanced with:
    - Feedback-based candidate injection

    Why:
    Pure semantic search may miss business-relevant mappings.
    Feedback ensures user intent is always considered.
    """

    embedding = get_embedding(source_column)
    matches = query_vector(embedding, top_k=10)

    unique_targets = {}
    results = []

    # ----------------------------------------
    # 🟢 EXISTING LOGIC (UNCHANGED)
    # ----------------------------------------
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

    # ----------------------------------------
    # FEEDBACK-AWARE INJECTION
    # ----------------------------------------
    if db and workflow_id:

        feedback = get_feedback_mapping(db, workflow_id, source_column)

        if feedback and feedback.final_field:
            feedback_target = feedback.final_field

            # Inject ONLY if not already present
            if feedback_target not in unique_targets:

                # Slightly lower than best score
                base_score = max(unique_targets.values(), default=0.5) - 0.05

                unique_targets[feedback_target] = base_score

    # ----------------------------------------
    # 🟢 FINAL RESULT BUILD (UNCHANGED)
    # ----------------------------------------
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