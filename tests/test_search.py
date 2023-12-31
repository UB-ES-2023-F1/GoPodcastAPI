import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from models import Podcast, User, db


@pytest.fixture
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()


def test_search_perfect_match(app):
    with app.app_context():
        user = User(
            email="test@example.com",
            username="Carl Sagan",
            password=generate_password_hash("Test1234"),
            verified=True,
            image=b""
        )
        db.session.add(user)
        db.session.commit()
        id_user = user.id
        user = User(
            email="test2@example.com",
            username="Carlos Latre",
            password=generate_password_hash("Test1234"),
            verified=True,
        )
        db.session.add(user)
        db.session.commit()
        id_user2 = user.id
        user = User(
            email="test3@example.com",
            username="Andreu Buenafuente",
            password=generate_password_hash("Test1234"),
            verified=True,
        )
        db.session.add(user)
        db.session.commit()
        id_user3 = user.id
        podcast = Podcast(
            cover=b"",
            name="Programming for dummies",
            summary="summary",
            description="buenisimo",
            id_author=id_user,
        )
        db.session.add(podcast)
        db.session.commit()
        id_podcast = podcast.id
        podcast = Podcast(
            cover=b"",
            name="Programming for fun",
            summary="summary",
            description="buenisimo",
            id_author=id_user,
        )
        db.session.add(podcast)
        db.session.commit()
        id_podcast2 = podcast.id
        podcast = Podcast(
            cover=b"",
            name="Cooking master",
            summary="summary",
            description="buenisimo",
            id_author=id_user,
        )
        db.session.add(podcast)
        db.session.commit()
        id_podcast3 = podcast.id

    client = app.test_client()

    # search podcast by name, a perfect match
    response = client.get("/search/podcast/Programming for dummies")
    assert response.status_code == 201
    expected_response = [
        {
            "id": str(id_podcast),
            "id_author": str(id_user),
            "author": {
                "id": str(id_user),
                "username": "Carl Sagan",
            },
            "cover": f"/podcasts/{id_podcast}/cover",
            "name": "Programming for dummies",
            "summary": "summary",
            "description": "buenisimo",
            "category": None,
            "match_percentage": 100,
        }
    ]
    assert response.get_json() == expected_response

    # search author by username, perfect match
    response = client.get("/search/user/Carl Sagan")
    assert response.status_code == 201
    expected_response = [
        {
            "id": str(id_user),
            "image_url": f"/users/{id_user}/image",
            "username": "Carl Sagan",
            "email": "test@example.com",
            "verified": True,
            "match_percentage": 100,
        }
    ]
    assert response.get_json() == expected_response

    # search by podcast, partial matches
    response = client.get("/search/podcast/programin for dúmies")
    assert response.status_code == 200
    expected_response = [
        {
            "id": str(id_podcast),
            "id_author": str(id_user),
            "author": {
                "id": str(id_user),
                "username": "Carl Sagan",
            },
            "cover": f"/podcasts/{id_podcast}/cover",
            "name": "Programming for dummies",
            "summary": "summary",
            "description": "buenisimo",
            "category": None,
            "match_percentage": 86.96,
        },
        {
            "id": str(id_podcast2),
            "id_author": str(id_user),
            "author": {
                "id": str(id_user),
                "username": "Carl Sagan",
            },
            "cover": f"/podcasts/{id_podcast2}/cover",
            "name": "Programming for fun",
            "summary": "summary",
            "description": "buenisimo",
            "category": None,
            "match_percentage": 65.00,
        },
    ]
    assert response.get_json() == expected_response

    # search by user, partial matches
    response = client.get("/search/user/cárlös Sagan")
    assert response.status_code == 200
    expected_response = [
        {
            "id": str(id_user),
            "image_url": f"/users/{id_user}/image",
            "username": "Carl Sagan",
            "email": "test@example.com",
            "verified": True,
            "match_percentage": 83.33,
        },
        {
            "id": str(id_user2),
            "image_url": f"/users/{id_user2}/image",
            "username": "Carlos Latre",
            "email": "test2@example.com",
            "verified": True,
            "match_percentage": 66.67,
        },
    ]
    assert response.get_json() == expected_response

    # search by podcast, no good matches found
    response = client.get("/search/podcast/No good matches")
    assert response.status_code == 404

    # search by user, no good matches found
    response = client.get("/search/user/Pirlo")
    assert response.status_code == 404
    expected_response = {"message": "No good matches found"}
    assert response.get_json() == expected_response

    # Get image profile of the searched users
    response = client.get(f"/users/{id_user}/image")
    assert response.status_code == 200
    assert response.data == b""

    # Image from non-existent user
    response = client.get(f"/users/00000000-0000-0000-0000-000000000000/image")
    assert response.status_code == 404
