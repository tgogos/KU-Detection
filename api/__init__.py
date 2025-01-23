from flask import Flask
from flask_cors import CORS
from api.routes import init_routes
from api.data_db import create_tables

def create_app():
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    init_routes(app)

    create_tables()
    
    return app