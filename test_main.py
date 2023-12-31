import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from .main import Hero, Team, app, get_session


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_create_team(client: TestClient):
    response = client.post(
        "/teams/", json={"name": "Preventers", "headquarters": "Sister Margaret's Bar"}
    )
    data = response.json()

    assert response.status_code == 200
    assert data["name"] == "Preventers"
    assert data["headquarters"] == "Sister Margaret's Bar"
    assert data["id"] is not None


def test_create_team_incomplete(client: TestClient):
    response = client.post("/heroes/", json={"name": "Preventers"})
    assert response.status_code == 422


def test_create_team_invalid(client: TestClient):
    response = client.post(
        "/heroes/",
        json={"name": "Preventers", "headquarters": {"message": "this is not HQ"}},
    )
    assert response.status_code == 422


def test_read_teams(session: Session, client: TestClient):
    team_1 = Team(name="Preventers", headquarters="Sister Margaret's Bar")
    team_2 = Team(name="Z-Force", headquarters="ZHQ")
    session.add(team_1)
    session.add(team_2)
    session.commit()

    response = client.get("/teams/")
    data = response.json()

    assert response.status_code == 200

    assert len(data) == 2
    assert data[0]["name"] == "Preventers"
    assert data[0]["headquarters"] == "Sister Margaret's Bar"
    assert data[0]["id"] is not None
    assert data[1]["name"] == "Z-Force"
    assert data[1]["headquarters"] == "ZHQ"
    assert data[1]["id"] is not None


def test_read_team(session: Session, client: TestClient):
    team_1 = Team(name="Preventers", headquarters="Sister Margaret's Bar")
    session.add(team_1)
    session.commit()

    response = client.get(f"/teams/{team_1.id}")
    data = response.json()

    assert response.status_code == 200
    assert data["name"] == "Preventers"
    assert data["headquarters"] == "Sister Margaret's Bar"
    assert data["id"] is not None


def test_update_team(session: Session, client: TestClient):
    team_1 = Team(name="Preventers", headquarters="Sister Margaret's Bar")
    session.add(team_1)
    session.commit()

    response = client.patch(f"/teams/{team_1.id}", json={"name": "Avengers"})
    data = response.json()

    assert data["name"] == "Avengers"
    assert data["headquarters"] == "Sister Margaret's Bar"
    assert data["id"] is not None


def test_delete_team(session: Session, client: TestClient):
    team_1 = Team(name="Preventers", headquarters="Sister Margaret's Bar")
    session.add(team_1)
    session.commit()

    response = client.delete(f"/teams/{team_1.id}")
    team_in_db = session.get(Team, team_1.id)
    assert response.status_code == 200
    assert team_in_db is None


def test_create_hero(client: TestClient):
    response = client.post(
        "/heroes/", json={"name": "Deadpond", "secret_name": "Dive Wilson"}
    )
    data = response.json()

    assert response.status_code == 200
    assert data["name"] == "Deadpond"
    assert data["secret_name"] == "Dive Wilson"
    assert data["age"] is None
    assert data["id"] is not None


def test_create_hero_incomplete(client: TestClient):
    response = client.post("/heroes/", json={"name": "Deadpond"})
    assert response.status_code == 422


def test_create_hero_invalid(client: TestClient):
    response = client.post(
        "/heroes/",
        json={
            "name": "Deadpond",
            "secret_name": {"message": "Do you wanna know my secret identity?"},
        },
    )
    assert response.status_code == 422


def test_read_heroes(session: Session, client: TestClient):
    hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
    hero_2 = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=48)
    session.add(hero_1)
    session.add(hero_2)
    session.commit()

    response = client.get("/heroes/")
    data = response.json()

    assert response.status_code == 200

    assert len(data) == 2
    assert data[0]["name"] == hero_1.name
    assert data[0]["secret_name"] == hero_1.secret_name
    assert data[0]["age"] == hero_1.age
    assert data[0]["id"] == hero_1.id
    assert data[1]["name"] == hero_2.name
    assert data[1]["secret_name"] == hero_2.secret_name
    assert data[1]["age"] == hero_2.age
    assert data[1]["id"] == hero_2.id


def test_read_hero(session: Session, client: TestClient):
    hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
    session.add(hero_1)
    session.commit()

    response = client.get(f"/heroes/{hero_1.id}")
    data = response.json()

    assert response.status_code == 200
    assert data["name"] == hero_1.name
    assert data["secret_name"] == hero_1.secret_name
    assert data["age"] == hero_1.age
    assert data["id"] == hero_1.id


def test_update_hero(session: Session, client: TestClient):
    hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
    session.add(hero_1)
    session.commit()

    response = client.patch(f"/heroes/{hero_1.id}", json={"name": "Deadpuddle"})
    data = response.json()

    assert data["name"] == "Deadpuddle"
    assert data["secret_name"] == "Dive Wilson"
    assert data["age"] is None
    assert data["id"] == hero_1.id


def test_delete_hero(session: Session, client: TestClient):
    hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
    session.add(hero_1)
    session.commit()

    response = client.delete(f"/heroes/{hero_1.id}")
    hero_in_db = session.get(Hero, hero_1.id)
    assert response.status_code == 200
    assert hero_in_db is None
