from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

models = [
    {'id': 0,
     'name': 'A Fire Upon the Deep',
     'owner': 'Vernor Vinge',
     'category': 'Cars',
     'published': '1992'},
    {'id': 1,
     'name': 'The Ones Who Walk Away From Omelas',
     'owner': 'Ursula K. Le Guin',
     'category': 'Cars',
     'published': '1973'},
    {'id': 2,
     'name': 'Dhalgren',
     'owner': 'Samuel R. Delany',
     'category': 'flowers',
     'published': '1975'},
    {'id': 3,
     'name': 'Model 3',
     'owner': 'Samuel R. Delany',
     'category': 'flowers',
     'published': '1975'},
    {'id': 4,
     'name': 'Model 4',
     'owner': 'Samuel R. Delany',
     'category': 'flowers',
     'published': '1975'}
]
#
# db = SQLAlchemy()
# print("Sadly now")
#



def setup_db(app):
    global db
    db = SQLAlchemy(app)
    print("Creating")
    db.create_all()


def get_models():
    return jsonify(models)


def create_model(data):
    print(data)
    print(User.query.filter_by(username=data['username']).first())


