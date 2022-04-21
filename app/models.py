from app import db
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection


# Fix for CASCADE


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


__all__ = ["Doc", "Page"]


class Doc(db.Model):
    doc_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    doc_title = db.Column(db.String(128), nullable=False)


class Page(db.Model):
    page_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    page_title = db.Column(db.String(128), nullable=False)
    page_content = db.Column(db.Text, nullable=False)
    doc_id = db.Column(db.Integer, db.ForeignKey('doc.doc_id', ondelete="CASCADE"), nullable=False)
    doc = db.relationship('Doc', backref=db.backref('pages', passive_deletes=True))