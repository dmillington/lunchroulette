from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class SlackAccessToken(db.Model):
    team_id = db.Column(db.String(), primary_key=True)
    access_token = db.Column(db.String())

class RouletteMessage(db.Model):
    channel = db.Column(db.String(), primary_key=True)
    timestamp = db.Column(db.String())