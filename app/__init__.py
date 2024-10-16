# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# import os

# # Initialize the app and db
# db = SQLAlchemy()

# def create_app():
#     app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))
#     app.config['SECRET_KEY']='434c29b387cb5f2b1f0694d7374865fe92c277150dcd8b24'
    
#     # Configurations
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'  # Database file path
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking

#     # Initialize extensions
#     db.init_app(app)

#     # Import and register blueprints
#     from .routes import main_bp
#     app.register_blueprint(main_bp)

#     # Create the database tables
#     with app.app_context():
#         db.create_all()  # Create all tables defined in the models

    # return app
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize the app and db
db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))
    
    # Use the provided secret key directly
    app.config['SECRET_KEY'] = '434c29b387cb5f2b1f0694d7374865fe92c277150dcd8b24'  # Your secret key

    # Configure the database URI
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///orders.db')  # Use Heroku's DATABASE_URL or fallback to SQLite

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking

    # Initialize extensions
    db.init_app(app)

    # Import and register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    # Create the database tables if they don't exist
    with app.app_context():
        db.create_all()  # Create all tables defined in the models

    return app
