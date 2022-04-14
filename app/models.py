from app import db


__all__ = ["Doc", "Page"]


class Doc(db.Model):
    doc_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    doc_title = db.Column(db.String(128), nullable=False)


class Page(db.Model):
    page_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    page_title = db.Column(db.String(128), nullable=False)
    page_content = db.Column(db.Text, nullable=False)
    doc_id = db.Column(db.Integer, db.ForeignKey('doc.doc_id', ondelete="CASCADE"), nullable=False)
