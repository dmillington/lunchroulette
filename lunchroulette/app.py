from flask import Flask, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .models import SlackAccessToken, RouletteMessage
import psycopg2
import slack
import os
import random

CLIENT_ID = os.getenv('SLACK_CLIENT_ID', '')
CLIENT_SECRET = os.getenv('SLACK_CLIENT_SECRET', '')
OAUTH_SCOPE = os.getenv('SLACK_BOT_SCOPE', '')

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    from .models import db
    db.init_app(app)

    return app

app = create_app()

from .models import db as _db
migrate = Migrate(app, _db)

@app.route("/begin_auth", methods=["GET"])
def pre_install():
    return f'<a href="https://slack.com/oauth/authorize?scope={ OAUTH_SCOPE }&client_id={ CLIENT_ID }">Add to Slack</a>'

@app.route("/finish_auth", methods=["GET", "POST"])
def post_install():
    # Retrieve the auth code from the request params
    auth_code = request.args['code']

    # An empty string is a valid token for this request
    client = slack.WebClient(token="")

    # Request the auth tokens from Slack
    response = client.oauth_access(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        code=auth_code
    )

    team_id = response['team_id']
    bot_access_token = response['bot']['bot_access_token']
    sat = SlackAccessToken()
    sat.team_id = team_id
    sat.access_token = bot_access_token
    db.session.add(sat)
    db.session.commit()

    return "Auth complete!"

@app.route('/')
def hello():
    return "Hello World"

@app.route('/start_roulette', methods=['POST'])
def start_roulette():
    team_id = request.form['team_id']
    channel_id = request.form['channel_id']
    
    # Lookup the token for the team_id
    try:
        sat = db.session.query(SlackAccessToken).filter(SlackAccessToken.team_id==team_id).one()
    except:
        return ('Unauthorized', 500)

    client = slack.WebClient(sat.access_token)

    if db.session.query(RouletteMessage).filter(RouletteMessage.channel==channel_id).count() > 0:
        return ('There is already a roulette happening in this channel!', 200)

    # post message to channel starting roulette
    response = client.chat_postMessage(channel=channel_id, text="Starting a lunch roulette! Reaction to this message if you're in!")
    message = RouletteMessage()
    message.channel = response.get('channel')
    message.timestamp = response.get('ts')
    db.session.add(message)
    db.session.commit()
    
    return ('', 200)

@app.route('/end_roulette', methods=['POST'])
def end_roulette():
    team_id = request.form['team_id']
    channel_id = request.form['channel_id']
    
    # Lookup the token for the team_id
    try:
        sat = db.session.query(SlackAccessToken).filter(SlackAccessToken.team_id==team_id).one()
    except:
        return ('Unauthorized', 500)

    client = slack.WebClient(sat.access_token)

    try:
        message = db.session.query(RouletteMessage).filter(RouletteMessage.channel==channel_id).one()
    except:
        return ('No roulette started. Try /lr_start first', 200)
    
    response = client.reactions_get(channel=message.channel, timestamp=message.timestamp)

    db.session.delete(message)
    db.session.commit()

    # Gather unique participants
    reactions = response.get('message').get('reactions', [])
    participants = set()
    for r in reactions:
        for u in r.get('users', []):
            participants.add(u)

    # create random groups of group_size
    groups = []
    group_size = 4
    while len(participants) >= group_size:
        g = random.sample(participants, group_size)
        for p in g:
            participants.remove(p)

    if len(participants) > 0:
        # if no other groups, make a single group
        if len(groups) == 0:
            groups.append(list(participants))
        # else, merge with the first group
        else:
            groups[0].extend(participants)

    for g in groups:
        response = client.conversations_open(users=",".join(g))
        ch = response.get('channel').get('id')
        client.chat_postMessage(channel=ch, text="Hi! You all are going to get Lunch! You can use this channel to coordinate logistics.")

    return ('Roulette ended! Matching people for lunch now. Participants will receive a group DM with their lunch buddies.', 200)

