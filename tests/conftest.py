import pytest
import routes.data as _data_mod
import routes.pdf as _pdf_mod
from app import create_app
from tests.fixtures.constants import STORE_NAMES


@pytest.fixture(scope='session')
def app():
    application = create_app()
    application.config['TESTING'] = True
    return application


@pytest.fixture()
def data_dir(tmp_path):
    store_dir = tmp_path / 'data'
    store_dir.mkdir()
    test_stores = {name: store_dir / f'{name}.json' for name in STORE_NAMES}

    orig_stores = _data_mod.STORES
    orig_data_dir = _pdf_mod.DATA_DIR
    _data_mod.STORES = test_stores
    _pdf_mod.DATA_DIR = store_dir

    yield store_dir, test_stores

    _data_mod.STORES = orig_stores
    _pdf_mod.DATA_DIR = orig_data_dir


@pytest.fixture()
def client(app, data_dir):
    return app.test_client()
