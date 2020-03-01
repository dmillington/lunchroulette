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

def test_finish_auth_no_authcode(client):
    pass

def test_finish_auth_bad_slack_response(client):
    pass


# test /start_roulette
# test /end_roulette
