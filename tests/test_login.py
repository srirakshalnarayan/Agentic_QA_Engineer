from app.main import app


def test_valid_login():
    client = app.test_client()

    response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123"
        }
    )

    assert response.status_code == 200
    assert response.data == b"Login successful"
    
def test_invalid_password():
    client = app.test_client()

    response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 200
    assert response.data == b"Invalid username or password"