import pytest
from fastapi.testclient import TestClient
@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv("DATABASE_URL",f"sqlite:///{tmp_path/'test.db'}")
    from app.db import Base,engine
    from app.main import app
    Base.metadata.drop_all(engine);Base.metadata.create_all(engine)
    yield TestClient(app)
    Base.metadata.drop_all(engine)
