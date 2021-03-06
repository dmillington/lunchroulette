import pytest
from unittest.mock import MagicMock, patch
from lunchroulette.models import SlackAccessToken, RouletteMessage

# test / (hello world)
def test_root(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert resp.get_data() == b'Hello World'

# test /begin_auth
def test_begin_auth(client):
    CLIENT_ID = 'NOCLIENTID'
    OAUTH_SCOPE = 'NOBOTSCOPE'
    resp = client.get('/begin_auth')
    assert resp.status_code == 200
    assert resp.get_data().decode() == f'<a href="https://slack.com/oauth/authorize?scope={ OAUTH_SCOPE }&client_id={ CLIENT_ID }">Add to Slack</a>'

# test /finish_auth
@patch('slack.WebClient.oauth_access')
def test_finish_auth_new_token(mock_oa, client, session):
    mock_oa.return_value = dict(team_id='a', bot={'bot_access_token': 'b'})

    resp = client.get('/finish_auth', query_string=dict(code='thecode'))
    mock_oa.assert_called_once()
    assert resp.status_code == 200
    assert resp.get_data().decode() == 'Auth complete!'
    tokens = session.query(SlackAccessToken).all()
    assert len(tokens) == 1
    assert tokens[0].team_id == 'a'
    assert tokens[0].access_token == 'b'

    # Test requesting for same team updates existing row
    mock_oa.return_value = dict(team_id='a', bot={'bot_access_token': 'c'})
    resp = client.get('/finish_auth', query_string=dict(code='thecode'))
    mock_oa.assert_called()
    assert resp.status_code == 200
    assert resp.get_data().decode() == 'Auth complete!'
    tokens = session.query(SlackAccessToken).all()
    assert len(tokens) == 1
    assert tokens[0].team_id == 'a'
    assert tokens[0].access_token == 'c'

# test /start_roulette
@patch('slack.WebClient.chat_postMessage')
def test_start_roulette_success(mock_pm, client, session):
    mock_pm.return_value = dict(channel='C012AB3CD', ts='1234567890.123456')

    session.add(SlackAccessToken(team_id='T12345', access_token='xoxa-access-token-string'))
    session.commit()
    resp = client.post('/start_roulette', data=dict(team_id='T12345', channel_id='C012AB3CD'))
    mock_pm.assert_called()

    assert resp.status_code == 200
    messages = session.query(RouletteMessage).all()
    assert len(messages) == 1
    assert messages[0].channel == 'C012AB3CD'
    assert messages[0].timestamp == '1234567890.123456'

@patch('slack.WebClient.chat_postMessage')
def test_start_roulette_already_started(mock_pm, client, session):
    session.add(SlackAccessToken(team_id='T12345', access_token='xoxa-access-token-string'))
    session.add(RouletteMessage(channel='C012AB3CD', timestamp='1234567890.123456'))
    session.commit()
    resp = client.post('/start_roulette', data=dict(team_id='T12345', channel_id='C012AB3CD'))
    mock_pm.assert_not_called()

    assert resp.status_code == 500
    assert resp.headers.get('error') == 'There is already a roulette happening in this channel!'

# test /end_roulette
@patch('slack.WebClient.chat_postMessage')
@patch('slack.WebClient.conversations_open')
@patch('slack.WebClient.reactions_get')
def test_end_roulette_success(mock_reactions, mock_conversations_open, mock_pm, client, session):
    mock_reactions.return_value = dict(message=dict(reactions=[dict(users=['ABCD','EFGH'])]), ts='1234567890.123456')
    mocked_channel_id = 'C012AB3CD'
    mocked_group_channel_id = 'D012AB3CD'
    mock_conversations_open.return_value = dict(channel=dict(id=mocked_group_channel_id))

    session.add(SlackAccessToken(team_id='T12345', access_token='xoxa-access-token-string'))
    session.add(RouletteMessage(channel=mocked_channel_id, timestamp='1234567890.123456'))
    session.commit()

    resp = client.post('/end_roulette', data=dict(team_id='T12345', channel_id=mocked_channel_id))
    mock_pm.assert_called_once_with(channel=mocked_group_channel_id, text="Hi! You all are going to get Lunch! You can use this channel to coordinate logistics.")
    assert resp.get_data() == b'Roulette ended! Matching people for lunch now. Participants will receive a group DM with their lunch buddies.'

@patch('slack.WebClient.chat_postMessage')
def test_end_roulette_not_started(mock_pm, client, session):
    mocked_channel_id = 'C012AB3CD'

    session.add(SlackAccessToken(team_id='T12345', access_token='xoxa-access-token-string'))
    session.commit()

    resp = client.post('/end_roulette', data=dict(team_id='T12345', channel_id=mocked_channel_id))
    mock_pm.assert_not_called()
    assert resp.status_code == 500
    assert resp.headers.get('error') == 'No roulette started. Try /lr_start first'
