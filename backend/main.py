import os
import redis
from flask_sock import Sock
from flask import Flask, render_template, make_response, request
from flask import redirect, url_for, flash, json, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_login import login_user, logout_user, current_user
from flask_caching import Cache
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
cache = Cache(app)
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
            # return render_template('index.html')
            return redirect('http://localhost:5173')
        return "Invalid password", 401
    else:
        # Return an error response
        flash('Invalid username or password')
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
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
        print(data, type(data))
        db.session.execute(db.delete(List).where(
            List.user_id == current_user.id).where(List.list_id == data['id']))
        db.session.commit()
        list = List(list_id=data['id'],
                    name=data['title'], user_id=current_user.id)
        db.session.add(list)
        db.session.commit()


@sock.route('/ecards')
@cache.cached(timeout=50)
def ecards(ws):
    while True:
        data = json.loads(ws.receive())
        # print(data, type(data))
        db.session.execute(db.delete(Card).where(
            Card.user_id == current_user.id).where(Card.card_id == data['id']))
        db.session.commit()
        card = Card(card_id=data['id'], title=data['title'],
                    user_id=current_user.id, list_id=data['listId'],
                    description=data['description'], complete=data['complete'])
        print(card)
        db.session.add(card)
        db.session.commit()
        cache.set(f"{card.card_id}", data)
        print(cache.get(f"{card.card_id}"))


@sock.route('/dlists')
def dlists(ws):
    while True:
        data = ws.receive()
        db.session.execute(db.delete(Card).where(Card.list_id == int(data)))
        db.session.commit()
        db.session.execute(db.delete(List).where(List.list_id == int(data)))
        db.session.commit()


@sock.route('/dcards')
def dcards(ws):
    while True:
        data = ws.receive()
        db.session.execute(db.delete(Card).where(Card.card_id == int(data)))
        db.session.commit()
        print(data)


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
        "discription": Card.description,
        "complete": Card.complete
    }


@sock.route('/lists')
def alists(ws):
    ll = db.session.execute(db.select(List).where(
        List.user_id == current_user.id)).scalars().all()
    r.json().set('Lists', '$', [list_json(i) for i in ll])
    doc = r.json().get('Lists')
    print(doc)
    ws.send(str(doc).replace("'", '"'))
    while True:
        data = ws.receive()
        x = json.loads(data)
        r.json().arrappend('Lists', '$', x)
        print(type(data), x)
        list = List(list_id=x['id'], name=x['title'], user_id=current_user.id)
        db.session.add(list)
        db.session.commit()


@sock.route('/cards')
def acards(ws):
    cc = db.session.execute(db.select(Card).where(
        Card.user_id == current_user.id)).scalars().all()
    r.json().set('Cards', '$', [card_json(i) for i in cc])
    doc = r.json().get('Cards')
    print(doc)
    ws.send(str(doc).replace("'", '"'))
    while True:
        data = ws.receive()
        x = json.loads(data)
        r.json().arrappend('Cards', '$', x)
        card = Card(card_id=x['id'], title=x['title'],
                    user_id=current_user.id, list_id=x['listId'],
                    description=x['description'], complete=x['complete'])
        db.session.add(card)
        print(card)
        db.session.commit()
