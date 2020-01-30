import pytest

from lunchroulette.app import create_app
from lunchroulette.app import db as _db
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

# test / (hello world)
def test_root(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert resp.get_data() == b'Hello World'
# test /begin_auth
# test /finish_auth
# test /start_roulette
# test /end_roulette