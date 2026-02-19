def test_extract_skills_importable_and_callable():
    from api import extract_skills
    assert callable(extract_skills)
