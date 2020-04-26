from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
# from database import get_models
from shutil import copyfile
import urllib.request

# EB looks for an 'application' callable by default.
application = Flask(__name__)
CORS(application)
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(application)

FRAMEWORKS = dict(fastai='FASTAI', pytorch='PYTORCH', tensorflow='TENSORFLOW')


def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]


def generate_folder_name(model):
    return model.name.replace(" ", "") + model.owner.username + str(model.id)

class User(db.Model):
    username = db.Column(db.String(80), unique=True, nullable=False, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'username': self.username,
            'email': self.email
        }


class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=True)
    framework = db.Column(db.String(20), nullable=False)
    download_link = db.Column(db.Text, nullable=True)
    requirements = db.Column(db.Text, nullable=False)
    script = db.Column(db.Text, nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.username'), nullable=False)
    owner = db.relationship('User', backref=db.backref('models', lazy=True))

    def __repr__(self):
        return '<Model %r>' % self.id

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'framework': self.framework,
            'published': dump_datetime(self.pub_date),
            'owner_id': self.owner.username
        }


db.create_all()


def line_prepender(filename, newcontent):
    with open(filename, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write(newcontent + '\n' + content)


def create_env(model):
    foldername = generate_folder_name(model)
    if not os.path.exists(foldername):
        try:
            original_umask = os.umask(0)
            os.makedirs(f"/var/www/html/dex-server/{foldername}", mode=0o777)
        finally:
            os.umask(original_umask)
            #os.makedirs(foldername)
    f = open(f"/var/www/html/dex-server/{foldername}/requirements.txt", "w+")
    f.write(model.requirements)
    f.close()
    copyfile(f"/var/www/html/dex-server/{model.framework.lower()}-app.py", f"/var/www/html/dex-server/{foldername}/{model.framework.lower()}-app.py")
    line_prepender(f"/var/www/html/dex-server/{foldername}/{model.framework.lower()}-app.py", model.script)
    # urllib.request.urlretrieve(model.download_link, f"{foldername}/model.pkl")
    # f = open(f"{foldername}/{model.framework.lower()}-app.py", "a+")
    # f.write(model.script)
    # f.close()
    os.system(
        f" cd /var/www/html/dex-server/{foldername}\n "
        f"python3 -m venv {foldername} \n"
        f"source /var/www/html/dex-server/{foldername}/{foldername}/bin/activate \n"
        f"curl -L -o export.pkl {model.download_link}\n"  
        f"pip3 install --upgrade --no-use-pep517 --no-cache-dir -r /var/www/html/dex-server/{foldername}/requirements.txt\n")
    print("Done")


def create_model(data):
    user = User.query.filter_by(username=data['username']).first()
    if user is None:
        user = User(username=data['username'], email=data['email'])
        db.session.add(user)
        db.session.commit()
    model = Model(name=data['modelName'], description=data['modelDescription'],
                  framework=FRAMEWORKS[data['modelFramework']], script=data['modelScript'],
                  download_link=data['modelDownloadLink'],
                  requirements=data['modelRequirements'], owner=user)
    db.session.add(model)
    db.session.commit()
    print(model)
    return model


# ###############RULES################# #


@application.route('/api/v1/resources/models/all', methods=['GET'])  # allow both GET
def get_models():
    models = Model.query.all()
    print(models)
    return jsonify([i.serialize for i in Model.query.all()])


@application.route('/api/v1/resources/model', methods=['GET'])
def get_model():
    model_id = request.args.get('modelId')
    return jsonify(Model.query.filter_by(id=int(model_id)).first().serialize)


@application.route('/api/v1/resources/deletemodel', methods=['GET'])
def delete_model():
    model_id = request.args.get('modelId')
    model = Model.query.filter_by(id=int(model_id)).first()
    db.session.delete(model)
    db.session.commit()
    return jsonify({'status': True, 'modelId': model_id})


@application.route('/api/v1/models/create_model', methods=['POST'])  # allow both GET and POST requests
def handle_create():
    data = request.get_json()  # data is empty
    print(data['modelDownloadLink'])
    model = create_model(data)
    print(model.download_link)
    create_env(model)
    return jsonify({'status': True, 'modelId': model.id})


@application.route('/api/v1/models/analyze', methods=['POST'])  # allow both GET and POST requests
def analyze_image():
    model_id = request.form.get('modelId')  # data is empty
    request_id = request.form.get('requestId')
    image = request.files["image"]
    model = Model.query.filter_by(id=int(model_id)).first()
    if Model is None:
        return jsonify({'status': "Model not found"})
    else:
        foldername = generate_folder_name(model)
        image.save(f"/var/www/html/dex-server/{foldername}/{request_id}.jpg")
        print(request_id)
        output = os.popen(
            f" cd /var/www/html/dex-server/{foldername}\n "
            f"source {foldername}/bin/activate \n"
            f"python3 fastai-app.py ./{request_id}.jpg\n").read()

        return jsonify({'status': True, 'output': output})


# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()
