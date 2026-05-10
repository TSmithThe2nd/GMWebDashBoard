import json
import pytest
from tests.fixtures.constants import STORE_NAMES


def test_get_missing_file_returns_null(client):
    r = client.get('/data/players')
    assert r.status_code == 200
    assert r.get_json() is None


def test_get_unknown_store_returns_404(client):
    r = client.get('/data/nonexistent_store')
    assert r.status_code == 404


def test_post_then_get_round_trip(client):
    payload = {'name': 'Aria', 'level': 5}
    client.post('/data/players', json=payload)
    r = client.get('/data/players')
    assert r.get_json() == payload


def test_post_writes_file_to_disk(client, data_dir):
    store_dir, test_stores = data_dir
    payload = {'hp': 30}
    client.post('/data/players', json=payload)
    assert test_stores['players'].exists()
    with open(test_stores['players']) as f:
        assert json.load(f) == payload


def test_post_overwrites_existing(client):
    client.post('/data/players', json={'v': 1})
    client.post('/data/players', json={'v': 2})
    assert client.get('/data/players').get_json() == {'v': 2}


def test_post_accepts_array(client):
    payload = [1, 2, 3]
    client.post('/data/encounters', json=payload)
    assert client.get('/data/encounters').get_json() == payload


def test_post_accepts_null(client):
    client.post('/data/clock', json=None)
    assert client.get('/data/clock').get_json() is None


def test_post_unknown_store_returns_404(client):
    r = client.post('/data/nope', json={})
    assert r.status_code == 404


def test_delete_removes_file(client, data_dir):
    store_dir, test_stores = data_dir
    client.post('/data/players', json={'x': 1})
    r = client.delete('/data/players')
    assert r.status_code == 200
    assert r.get_json() == {'ok': True}
    assert not test_stores['players'].exists()


def test_delete_missing_file_is_idempotent(client):
    r = client.delete('/data/players')
    assert r.status_code == 200
    assert r.get_json() == {'ok': True}


def test_delete_unknown_store_returns_404(client):
    r = client.delete('/data/nope')
    assert r.status_code == 404


@pytest.mark.parametrize('store', STORE_NAMES)
def test_all_12_stores_reachable(client, store):
    r = client.get(f'/data/{store}')
    assert r.status_code == 200
