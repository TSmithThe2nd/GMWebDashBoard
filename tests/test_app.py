from tests.fixtures.constants import STORE_NAMES


def test_health_returns_ok(client):
    r = client.get('/health')
    assert r.status_code == 200
    data = r.get_json()
    assert data['status'] == 'ok'


def test_health_lists_all_12_stores(client):
    r = client.get('/health')
    assert len(r.get_json()['stores']) == 12


def test_health_pdf_support_field_is_bool(client):
    r = client.get('/health')
    assert isinstance(r.get_json()['pdf_support'], bool)


def test_cors_header_present_on_get(client):
    r = client.get('/health')
    assert r.headers.get('Access-Control-Allow-Origin') == '*'


def test_options_returns_200(client):
    r = client.options('/')
    assert r.status_code == 200


def test_unknown_route_returns_404(client):
    r = client.get('/this-route-does-not-exist')
    assert r.status_code == 404
