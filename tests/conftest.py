import pytest
from config import Config


@pytest.fixture
def tmp_config(tmp_path):
    cfg = Config()
    cfg.working_dir = str(tmp_path)
    return cfg
