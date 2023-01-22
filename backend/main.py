import os
from flask_sock import Sock
from flask import Flask, render_template, make_response, request
from flask import redirect, url_for, flash, json
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required
from flask_login import login_user, logout_user, current_user
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
sock = Sock(app)
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
    lists = db.relationship('List', backref='user', lazy='dynamic')
    cards = db.relationship('Card', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def get_id(self):
        return self.id


class List(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(64))
    cards = db.relationship('Card', backref='list', lazy='dynamic')

    def __repr__(self):
        return '{}'.format({'title': self.name, 'id': self.id})


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'))
    title = db.Column(db.String(64))
    description = db.Column(db.String(256))

    def __repr__(self):
        return '{}'.format({'title': self.title, 'id': self.id,
                            'listId': self.list_id,
                            'description': self.description})


@app.before_first_request
def create_tables():
    db.create_all()


def get_db():
    engine = create_engine('sqlite:///app.db')
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
@login_required
def logout():
    # Remove the user's token from the database
    current_user.auth_token = None
    db.session.commit()

    # Log out the user
    logout_user()

    # Return a success response
    return make_response(redirect(url_for('login')))


@login_manager.user_loader
def load_user(user_id):
    # Look up the user in the database
    user = User.query.filter_by(id=user_id).first()

    # If the user exists, return it
    if user is not None:
        return user


@sock.route('/dlists')
def dlists(ws):
    while True:
        data = ws.receive()
        db.session.execute(db.delete(Card).where(Card.list_id == int(data)))
        print(db.session.get(List, int(data)))
        db.session.delete(db.session.get(List, int(data)))
        db.session.commit()
        ws.send(data)


@sock.route('/dcards')
def dcards(ws):
    while True:
        data = ws.receive()
        db.session.delete(db.session.get(Card, int(data)))
        print(data)
        ws.send(data)


@sock.route('/lists')
def alists(ws):
    while True:
        data = ws.receive()
        x = json.loads(data)
        print(data, x)
        list = List(id=x['id'], name=x['title'], user_id=current_user.id)
        db.session.add(list)
        db.session.commit()
        ws.send(data)


@sock.route('/cards')
def acards(ws):
    while True:
        data = ws.receive()
        x = json.loads(data)
        card = Card(id=x['id'], title=x['title'],
                    user_id=current_user.id, list_id=x['listId'],
                    description=x['description'])
        db.session.add(card)
        db.session.commit()
        print(data)
        ws.send(data)


@app.route('/protected')
@login_required
def protected():
    return "You are logged in"
