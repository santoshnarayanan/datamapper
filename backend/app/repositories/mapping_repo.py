from app.models.mappinginfo import MappingInfo

def get_mapping(db, workflow_id):
    return db.query(MappingInfo).filter(MappingInfo.workflow_id == workflow_id).first()

def save_or_update_mapping(db, workflow_id, mapping_data):
    mapping = get_mapping(db, workflow_id)

    if mapping:
        mapping.mapping = mapping_data
    else:
        mapping = MappingInfo(workflow_id=workflow_id, mapping=mapping_data)
        db.add(mapping)

    db.commit()
    db.refresh(mapping)

    return mapping
