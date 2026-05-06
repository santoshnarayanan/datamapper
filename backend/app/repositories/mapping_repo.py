"""
Mapping Repository

This module handles persistence and overwrite logic for column-level mappings.

Key Concepts:
- Mapping is stored per (workflow_id, source_worksheet, target_worksheet)
- Each mapping entry represents: source_column → target_column

Core Rules Enforced:
1. Global Target Uniqueness:
   - A target column can be mapped only once across the entire workflow.

2. Source Worksheet → Single Active Target:
   - A source worksheet can map to only one target worksheet at a time.
   - Changing target removes all previous mappings for that source.

3. Bi-directional Overwrite:
   - Re-mapping a source or target removes previous conflicting mappings.

4. No Empty Records:
   - If all mappings are removed from a record, the record itself is deleted.

Design Intent:
- Ensure deterministic mapping behavior
- Keep DB clean (no stale or empty mappings)
- Align backend logic with UI drag-and-drop behavior
"""


from uuid import UUID
from app.models.mappinginfo import MappingInfo
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
import uuid



def get_mapping(db: Session, workflow_id, source_ws, target_ws):
    return db.query(MappingInfo).filter(
        MappingInfo.workflow_id == workflow_id,
        MappingInfo.source_worksheet == source_ws,
        MappingInfo.target_worksheet == target_ws
    ).first()


"""
Save or update mapping for a given workflow and worksheet context.

Steps:
1. Remove all existing mappings for the given source worksheet
   (enforces single active target per source).

2. Enforce global target uniqueness across the workflow
   (removes any mapping using same target column).

3. Generate IDs for new mappings if missing.

4. Insert new mapping as a fresh record.

Args:
- db: Database session
- workflow_id: Workflow identifier
- source_ws: Source worksheet name
- target_ws: Target worksheet name
- new_mapping: List of mapping entries
- decision_trace: explain trace of audit

Returns:
- Newly created MappingInfo record
"""

def save_or_update_mapping(
    db: Session,
    workflow_id,
    source_ws,
    target_ws,
    new_mapping: list,
    decision_trace=None  # ✅ NEW: optional decision trace
):
    # =========================================
    # 🔥 STEP 0: REMOVE ALL mappings for SOURCE
    # Remove all mappings for this source worksheet.
    # This ensures a source worksheet can map to only ONE target at a time.
    # =========================================
    existing_source_records = db.query(MappingInfo).filter(
        MappingInfo.workflow_id == workflow_id,
        MappingInfo.source_worksheet == source_ws
    ).all()

    for record in existing_source_records:
        db.delete(record)

    db.flush()  # ensure deletion before next step

    # =========================================
    # 🔥 STEP 1: GLOBAL TARGET UNIQUENESS
    # Enforce global target uniqueness.
    # A target column should not be mapped more than once across the workflow.
    # =========================================
    all_records = db.query(MappingInfo).filter(
        MappingInfo.workflow_id == workflow_id
    ).all()

    target_columns = set(
        m["target"]["column"] for m in new_mapping
    )

    for record in all_records:
        updated_mapping = []

        for m in (record.mapping or []):
            if m["target"]["column"] in target_columns:
                continue  # remove conflict
            updated_mapping.append(m)

        # =========================================
        # 🔥 FIX: delete empty records
        # If no mappings remain after cleanup, delete the record
        # to avoid storing empty mapping entries.
        # =========================================
        if not updated_mapping:
            db.delete(record)
        else:
            record.mapping = updated_mapping
            flag_modified(record, "mapping")
            db.add(record)

    # =========================================
    # 🔥 STEP 2: GENERATE IDs
    # Ensure every mapping entry has a unique ID.
    # IDs are generated server-side for consistency.
    # =========================================
    for m in new_mapping:
        if not m.get("id"):
            m["id"] = str(uuid.uuid4())

    # =========================================
    # 🔥 STEP 3: INSERT NEW RECORD
    # Insert new mapping as a fresh record for the given context
    # (workflow_id + source_ws + target_ws).
    # =========================================
    new_record = MappingInfo(
        workflow_id=workflow_id,
        source_worksheet=source_ws,
        target_worksheet=target_ws,
        mapping=new_mapping
    )

    # =========================================
    # 🟣 STEP 3.1 — STORE DECISION TRACE
    # Store explainability trace for audit + debugging (Phase 11)
    # =========================================
    if decision_trace:
        new_record.decision_trace = decision_trace

    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return new_record