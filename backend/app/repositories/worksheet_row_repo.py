# app/repositories/worksheet_row_repo.py
from app.models.worksheet_rows import WorksheetRow


def bulk_insert_rows(db, worksheet_id, rows, batch_size=1000):
    from app.models.worksheet_rows import WorksheetRow

    for i in range(0, len(rows), batch_size):
        chunk = rows[i:i + batch_size]

        objects = [
            WorksheetRow(
                worksheet_id=worksheet_id,
                row_index=i + idx,
                row_data=row
            )
            for idx, row in enumerate(chunk)
        ]

        db.bulk_save_objects(objects)
        db.commit()


def get_paginated_rows(db, worksheet_id, page, page_size):
    offset = (page - 1) * page_size

    return db.query(WorksheetRow).filter(
        WorksheetRow.worksheet_id == worksheet_id
    ).order_by(WorksheetRow.row_index)\
     .offset(offset)\
     .limit(page_size)\
     .all()


def get_total_rows(db, worksheet_id):
    return db.query(WorksheetRow).filter(
        WorksheetRow.worksheet_id == worksheet_id
    ).count()



def delete_rows_by_worksheet(db, worksheet_id):
    from app.models.worksheet_rows import WorksheetRow

    db.query(WorksheetRow).filter(
        WorksheetRow.worksheet_id == worksheet_id
    ).delete()

    db.commit()