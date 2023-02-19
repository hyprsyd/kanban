import os
import redis
from flask_sock import Sock
from flask import Flask, render_template, make_response, request
from flask import redirect, url_for, flash, json
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

r = redis.Redis()
r.flushdb()
config = {
    "DEBUG": True,
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_HOST": "localhost",
    "CACHE_REDIS_PORT": 6379,
    "CACHE_REDIS_URL": "redis://localhost:6379"
}

app = Flask(__name__)
sock = Sock(app)
app.config.from_mapping(config)
login_manager = LoginManager()
login_manager.init_app(app)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
                                        os.path.join(basedir, 'app.db')
db = SQLAlchemy(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ['SEC_KEY']
app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 25}
app.config['SESSION_COOKIE_SAMESITE'] = "None"
app.config['SESSION_COOKIE_SECURE'] = True


# Models


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return '<User {}>'.format(self.username)


class List(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, unique=False)
    user_id = db.Column(db.Integer)
    name = db.Column(db.String(64))

    def __repr__(self):
        return '{"title": %r, "id": %r }' % (self.name, self.list_id)


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    card_id = db.Column(db.Integer, unique=False)
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'))
    title = db.Column(db.String(64))
    description = db.Column(db.String(256))
    complete = db.Column(db.Integer, unique=False)

    def __repr__(self):
        return '{"title": %r, "id": %r ,"listId": %r,"description": %r,"complete": %r}' % (
            self.title, self.card_id, self.list_id, self.description, self.complete)


@app.before_first_request
def create_tables():
    db.create_all()


# Routes


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/signup')
def signup_get():
    return render_template('signup.html')


@app.route('/login')
def login_get():
    return render_template('login.html')


@app.route('/signup', methods=['POST'])
def signup():
    # Get the user's username and password from the request
    username = request.form['username']
    password = request.form['password']

    # Check if the user already exists
    user = User.query.filter_by(username=username).first()
    if user is not None:
        # Return an error response if the user already exists
        return "Username already taken", 400
    else:
        # Create a new user if it doesn't exist
        user = User(username=username,
                    password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        # Return a success response
        return make_response(redirect(url_for('login')))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Get the user's username and password from the request
    username = request.form['username']
    password = request.form['password']

    # Check if the user already exists
    user = User.query.filter_by(username=username).first()

    if user is not None:
        if check_password_hash(user.password_hash, password):
            # Login the user
            login_user(user)

            # Return a success response
            return render_template('index.html')
        return "Invalid password", 401
    else:
        # Return an error response
        flash('Invalid username or password')
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    List.query.filter(List.user_id == current_user.id).delete()
    Card.query.filter(Card.user_id == current_user.id).delete()
    for i in (r.json().get('Lists')).values():
        list = List(list_id=i['id'], name=i['title'], user_id=current_user.id)
        db.session.add(list)
        db.session.commit()
    for i in (r.json().get('Cards')).values():
        if db.select(List).where(List.list_id == i['listId']) is not None:
            card = Card(user_id=current_user.id,
                        card_id=i['id'],
                        list_id=i['listId'],
                        title=i['title'],
                        description=i['description'],
                        complete=i['complete'])
            db.session.add(card)
            db.session.commit()
    logout_user()
    return make_response(redirect(url_for('login')))


@login_manager.user_loader
def load_user(user_id):
    # Look up the user in the database
    user = User.query.filter_by(id=user_id).first()

    # If the user exists, return it
    if user is not None:
        return user


@sock.route('/elists')
def elists(ws):
    while True:
        data = json.loads(ws.receive())
        r.json().delete('Lists', f"$.{int(data['id'])}")
        r.json().set('Lists', f"$.{int(data['id'])}", data)


@sock.route('/ecards')
def ecards(ws):
    while True:
        data = json.loads(ws.receive())
        r.json().delete('Cards', f"$.{int(data['id'])}")
        r.json().set('Cards', f"$.{int(data['id'])}", data)


@sock.route('/dlists')
def dlists(ws):
    while True:
        data = ws.receive()
        r.json().delete('Lists', f'$.{int(data)}')


@sock.route('/dcards')
def dcards(ws):
    while True:
        data = ws.receive()
        r.json().delete('Cards', f'$.{int(data)}')


def list_json(List):
    return {
        "id": List.list_id,
        "title": List.name
    }


def card_json(Card):
    return {
        "id": Card.card_id,
        "title": Card.title,
        "listId": Card.list_id,
        "description": Card.description,
        "complete": Card.complete
    }


def empty_json():
    return {}


@sock.route('/lists')
def alists(ws):
    ll = db.session.execute(db.select(List).where(
        List.user_id == current_user.id)).scalars().all()
    r.json().set('Lists', '$', empty_json())
    for i in ll:
        r.json().set('Lists', f'$.{i.list_id}', list_json(i))
    doc = r.json().get('Lists')
    doc = ([i for i in (doc.values())])
    ws.send(str(doc).replace("'", '"'))
    while True:
        data = ws.receive()
        x = json.loads(data)
        r.json().set('Lists', f"$.{x['id']}", x)


@sock.route('/cards')
def acards(ws):
    cc = db.session.execute(db.select(Card).where(
        Card.user_id == current_user.id)).scalars().all()
    r.json().set('Cards', '$', empty_json())
    for i in cc:
        r.json().set('Cards', f'$.{i.card_id}', card_json(i))
    doc = r.json().get('Cards')
    doc = ([i for i in (doc.values())])
    ws.send(str(doc).replace("'", '"'))
    while True:
        data = ws.receive()
        x = json.loads(data)
        r.json().set('Cards', f"$.{x['id']}", x)
