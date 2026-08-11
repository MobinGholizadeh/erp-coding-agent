import pytest
from fastapi.testclient import TestClient

from erp_coding_agent.main import app

@pytest.fixture
def client():
    return TestClient(app)
