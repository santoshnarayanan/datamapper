from app.models.mapping_feedback import MappingFeedback


def save_feedback(
    db,
    workflow_id,
    source_field,
    suggested_field,
    final_field,
    action
):
    feedback = MappingFeedback(
        workflow_id=workflow_id,
        source_field=source_field,
        suggested_field=suggested_field,
        final_field=final_field,
        action=action
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback


def get_feedback_mapping(db, workflow_id, source_field):
    return db.query(MappingFeedback).filter(
        MappingFeedback.workflow_id == workflow_id,
        MappingFeedback.source_field == source_field
    ).order_by(MappingFeedback.created_at.desc()).first()