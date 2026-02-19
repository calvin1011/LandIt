"""Tests for POST /resume/enhance-for-job endpoint."""

import pytest
from unittest.mock import patch, MagicMock


def test_enhance_for_job_returns_404_when_no_resume():
    from fastapi.testclient import TestClient
    from api import app

    with patch("api.db") as mock_db:
        mock_db.get_user_resume.return_value = None
        client = TestClient(app)
        response = client.post(
            "/resume/enhance-for-job",
            json={"user_email": "nobody@example.com", "job_description": "Python developer needed."},
        )
        assert response.status_code == 404
        mock_db.get_user_resume.assert_called_once_with("nobody@example.com")


def test_enhance_for_job_returns_400_when_no_job_description_and_no_job_id():
    from fastapi.testclient import TestClient
    from api import app

    with patch("api.db") as mock_db:
        mock_db.get_user_resume.return_value = {
            "user_email": "u@example.com",
            "structured_data": {
                "work_experience": [],
                "education": [],
                "skills": {},
                "personal_info": {},
                "summary": "",
            },
        }
        client = TestClient(app)
        response = client.post(
            "/resume/enhance-for-job",
            json={"user_email": "u@example.com"},
        )
        assert response.status_code == 400
        assert "job_description" in response.json().get("detail", "").lower() or "job_id" in response.json().get("detail", "").lower()
