import io
from unittest.mock import patch


def _pdf_upload(client, filename='char.pdf', data=b'%PDF-1.4 fake'):
    return client.post(
        '/parse-pdf',
        data={'file': (io.BytesIO(data), filename)},
        content_type='multipart/form-data',
    )


def test_no_file_returns_400(client):
    r = client.post('/parse-pdf', data={}, content_type='multipart/form-data')
    assert r.status_code == 400


def test_wrong_extension_returns_400(client):
    r = client.post(
        '/parse-pdf',
        data={'file': (io.BytesIO(b'hello'), 'char.txt')},
        content_type='multipart/form-data',
    )
    assert r.status_code == 400


def test_success_returns_parser_result(client):
    mock_result = {'charName': 'Aria', 'level': 5}
    with patch('routes.pdf.parse_pdf_file', return_value=mock_result):
        r = _pdf_upload(client)
    assert r.status_code == 200
    assert r.get_json() == mock_result


def test_fatal_result_returns_422(client):
    fatal = {'fatal': True, 'error': 'visual_render'}
    with patch('routes.pdf.parse_pdf_file', return_value=fatal):
        r = _pdf_upload(client)
    assert r.status_code == 422


def test_parser_exception_returns_error(client):
    with patch('routes.pdf.parse_pdf_file', side_effect=RuntimeError('boom')):
        r = _pdf_upload(client)
    assert r.status_code != 200


def test_tmp_file_cleaned_up(client, data_dir):
    store_dir, _ = data_dir
    with patch('routes.pdf.parse_pdf_file', return_value={'charName': 'Test'}):
        _pdf_upload(client)
    remaining = list(store_dir.glob('*.pdf'))
    assert remaining == []


def test_pdf_fields_no_file_returns_400(client):
    r = client.post('/pdf-fields', data={}, content_type='multipart/form-data')
    assert r.status_code == 400
