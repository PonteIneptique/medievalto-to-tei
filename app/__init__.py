import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


def get_local_path(*path) -> str:
    return os.path.join(os.path.dirname(__file__), *path)


app = Flask(
    __name__,
    static_folder=get_local_path("statics"),
    template_folder=get_local_path("templates")
)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{get_local_path("sqllite.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


from app.routes import *
from app.models import *


@app.cli.group("db")
def db_grp():
    """ Database commands"""


@db_grp.command("create")
def db_build():
    """ Builds database """
    with app.app_context():
        db.create_all()


@db_grp.command("drop")
def db_build():
    """ Builds database """
    with app.app_context():
        db.drop_all()
