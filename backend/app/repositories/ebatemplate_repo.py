from app.models.ebatemplate import EbaTemplate

def get_eba_template(db):
    # for now return first template
    return db.query(EbaTemplate).first()

