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


def get_feedback_stats(db, workflow_id, source_field):
    feedbacks = db.query(MappingFeedback).filter(
        MappingFeedback.workflow_id == workflow_id,
        MappingFeedback.source_field == source_field
    ).all()

    stats = {
        "accepted": {},
        "rejected": {}
    }

    for f in feedbacks:
        if f.action == "ACCEPT":
            stats["accepted"][f.final_field] = stats["accepted"].get(f.final_field, 0) + 1

        elif f.action == "REJECT":
            # Reject refers to suggested_field (what system got wrong)
            if f.suggested_field:
                stats["rejected"][f.suggested_field] = stats["rejected"].get(f.suggested_field, 0) + 1

    return stats