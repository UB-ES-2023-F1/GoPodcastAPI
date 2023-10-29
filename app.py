import os
import re
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (JWTManager, create_access_token, get_jwt,
                                get_jwt_identity, jwt_required,
                                set_access_cookies, unset_jwt_cookies)
from werkzeug.security import check_password_hash, generate_password_hash

from models import User, db


def create_app(testing=False):
    app = Flask(__name__)
    load_dotenv(dotenv_path='.env')

    if (testing):
        app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('POSTGRES_TEST_URL')
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('POSTGRES_URL')
    db.init_app(app)
    app.config['JWT_TOKEN_LOCATION'] = ['cookies', 'headers']
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    app.config["JWT_SECRET_KEY"] = os.getenv('JWT_SECRET_KEY')
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173",
         os.getenv('FRONTEND_URL')], supports_credentials=True)
    JWTManager(app)

    @app.after_request
    def refresh_expiring_jwts(response):
        try:
            exp_timestamp = get_jwt()["exp"]
            now = datetime.now(timezone.utc)
            target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
            if target_timestamp > exp_timestamp:
                access_token = create_access_token(identity=get_jwt_identity())
                set_access_cookies(response, access_token)
            return response
        except (RuntimeError, KeyError):
            return response

    @app.route('/')
    def hello_world():  # put application's code here
        return 'Hello World!'

    @app.post('/user')
    def create_user():
        data_dict = request.get_json()

        username = data_dict['username']
        email = data_dict['email']
        password = data_dict['password']

        if not username or not email:
            return jsonify({'mensaje': 'Se requiere introducir usuario y contraseña'}), 400

        # check if email is valid
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_pattern, email):
            return jsonify({'mensaje': 'Dirección email no válida'}), 400

        # check if password is valid
        password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{6,}$'
        if not re.match(password_pattern, password):
            return jsonify({'mensaje': 'Contraseña no válida. La contraseña debe tener '
                            'como mínimo 6 caracteres, entre los cuales debe '
                            'haber almenos una letra, un número y una mayúscula'}), 400

        # Check if the user with the same username or email already exists
        existing_user = db.session.query(
            User).filter_by(username=username).first()
        if existing_user:
            return jsonify({'mensaje': 'Nombre de usuario ya existente'}), 400

        existing_email = db.session.query(User).filter_by(email=email).first()
        if existing_email:
            return jsonify({'mensaje': 'Dirección email ya existente'}), 400

        # Create a new user
        new_user = User(username=username, email=email,
                        password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'mensaje': 'Usuario '+username+' registrado correctamente'}), 201

    @app.post('/login')
    def login_user():
        data = request.get_json()
        email = data['email']
        password = data['password']

        user = db.session.query(User).filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            return jsonify({'success': False, 'error': 'Login details are incorrect'}), 401
        access_token = create_access_token(identity=user.id)
        resp = jsonify({'success': True})
        set_access_cookies(resp, access_token)
        return resp, 200

    @app.post("/logout")
    def logout():
        response = jsonify({'success': True})
        unset_jwt_cookies(response)
        return response

    @app.get('/protected')
    @jwt_required()
    def protected():
        current_user = get_jwt_identity()
        return jsonify(logged_in_as=current_user), 200

    return app


if __name__ == '__main__':
    app = create_app()
    app.run()
