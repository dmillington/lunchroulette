from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class SlackAccessToken(db.Model):
    team_id = db.Column(db.String(), primary_key=True)
    access_token = db.Column(db.String())

class RouletteMessage(db.Model):
    channel = db.Column(db.String(), primary_key=True)
    timestamp = db.Column(db.String())