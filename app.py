from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import uuid  # for public id
from werkzeug.security import generate_password_hash, check_password_hash
# imports for PyJWT authentication
import jwt
from datetime import datetime, timedelta
from functools import wraps

# creates Flask object
app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], methods=['GET', 'POST'], allow_headers=['Authorization', 'Content-Type','x-access-token'])

# configuration
# NEVER HARDCODE YOUR CONFIGURATION IN YOUR CODE
# INSTEAD CREATE A .env FILE AND STORE IN IT
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with your actual secret key
# database name
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Database.db'
app.config['SQLALCHEMY_DATABASE_URI'] = ' postgres://asohpktmgfbzhc:79d74a63bc741df797b28254081c1dac9c5b5e8cfdfa5636f7c2b81c865e84ad@ec2-35-169-9-79.compute-1.amazonaws.com:5432/d4ma3ijujgsjuq'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# creates SQLALCHEMY object
db = SQLAlchemy(app)

# Database ORMs
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(70), unique=True)
    password = db.Column(db.String(80))

# decorator for verifying the JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        # return 401 if token is not passed
        if not token:
            return jsonify({'message': 'Token is missing !!'}), 401

        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query \
                .filter_by(public_id=data['public_id']) \
                .first()
        except:
            return jsonify({
                'message': 'Token is invalid !!'
            }), 401
        # returns the current logged in users context to the routes
        return f(current_user, *args, **kwargs)

    return decorated

# User Database Route
# this route sends back a list of users
@app.route('/user', methods=['GET'])
@token_required
def get_all_users(current_user):
    # querying the database
    # for all the entries in it
    users = User.query.all()
    # converting the query objects
    # to a list of JSONs
    output = []
    for user in users:
        # appending the user data JSON 
        # to the response list
        output.append({
            'public_id': user.public_id,
            'name': user.name,
            'email': user.email
        })

    return jsonify({'users': output})

# route for logging a user in
@app.route('/login', methods=['POST'])
def login():
    # creates a dictionary of form data
    auth = request.get_json()

    if not auth or not auth.get('email') or not auth.get('password'):
        # returns 401 if any email or / and password is missing
        return make_response(
            'Could not verify',
            401,
            {'WWW-Authenticate': 'Basic realm ="Login required !!"'}
        )

    user = User.query \
        .filter_by(email=auth.get('email')) \
        .first()

    if not user:
        # returns 401 if the user does not exist
        return make_response(
            'Could not verify',
            401,
            {'WWW-Authenticate': 'Basic realm ="User does not exist !!"'}
        )

    if check_password_hash(user.password, auth.get('password')):
        # Generate the JWT Token
        token = jwt.encode({
            'public_id': user.public_id,
            'exp': datetime.utcnow() + timedelta(minutes=30)
        }, app.config['SECRET_KEY'], algorithm="HS256")

        # Print the generated token for debugging
        print(f"Token generated: {token}")

        return make_response(jsonify({'token': token}), 201)
    # returns 403 if the password is wrong
    return make_response(
        'Could not verify',
        403,
        {'WWW-Authenticate': 'Basic realm ="Wrong Password !!"'}
    )

# signup route
@app.route('/signup', methods=['POST'])
def signup():
    try:
        # Parse JSON data from the request body
        data = request.get_json()

        # Extract name, email, and password
        name, email, password = data.get('name'), data.get('email'), data.get('password')

        # Check for an existing user with the same email
        user = User.query.filter_by(email=email).first()
        if not user:
            # Create a new user
            new_user = User(
                public_id=str(uuid.uuid4()),
                name=name,
                email=email,
                password=generate_password_hash(password)
            )
            db.session.add(new_user)
            db.session.commit()
            return make_response('Successfully registered.', 201)
        else:
            # Return a 202 response if the user already exists
            return make_response('User already exists. Please Log in.', 202)
    except Exception as e:
        # Handle exceptions, such as JSON parsing errors
        return make_response(f'Error: {str(e)}', 400)

if __name__ == "__main__":
    # setting debug to True enables hot reload
    # and also provides a debugger shell
    # if you hit an error while running the server
    app.run(debug=True)



from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, Product

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

CORS(app)
migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)

class Products(Resource):
    def get(self):
        products_dict_list = [d.to_dict() for d in Product.query.all()]
        response = make_response(
            jsonify(products_dict_list),
            200,
        )
        return response

    def post(self):
        products = []
        for data in request.json:
            name = data['product_name']
            quantity = data['product_quantity']
            price = data['product_price']

            new_product = Product(
                product_name=name,
                product_quantity=quantity,
                product_price=price,
            )

            db.session.add(new_product)
            products.append(new_product)

        db.session.commit()

        products_dicts = [products.to_dict() for product in products]

        response = make_response(
            jsonify(products_dicts),
            201
        )

        return response

api.add_resource(Products, '/products')

from models import db, Transaction

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transactions.db'

class Transactions(Resource):
    def get(self):
        transactions_dict_list = [d.to_dict() for d in Transaction.query.all()]
        response = make_response(
            jsonify(transactions_dict_list),
            200,
        )
        return response

    def post(self):
        transactions = []
        for data in request.json:
            product_name = data['product_name']
            product_quantity = data['product_quantity']
            product_price = data['product_price']

            new_transaction = Transaction(
                product_name=product_name,
                product_quantity=product_quantity,
                product_price=product_price,
            )

            db.session.add(new_transaction)
            transactions.append(new_transaction)

        db.session.commit()

        transaction_dicts = [transaction.to_dict() for transaction in transactions]

        response = make_response(
            jsonify(transaction_dicts),
            201
        )

        return response

api.add_resource(Transactions, '/transactions')


if __name__ == '_main_':
    app.run(debug=True)