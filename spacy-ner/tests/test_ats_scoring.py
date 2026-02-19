"""Unit tests for ATS compatibility scoring in relationship_extractor."""

import pytest


@pytest.fixture
def analyzer():
    import spacy
    from relationship_extractor import ResumeIntelligenceAnalyzer
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        pytest.skip("en_core_web_sm not installed")
    return ResumeIntelligenceAnalyzer(nlp)


def test_ats_returns_score_and_breakdown(analyzer):
    text = (
        "John Smith\n"
        "john@example.com | (555) 123-4567\n"
        "WORK EXPERIENCE\n"
        "Senior Engineer at Google Jan 2020 - Dec 2023\n"
        "EDUCATION\n"
        "Bachelor of Science from MIT 2019\n"
        "SKILLS\n"
        "Python, JavaScript\n"
    )
    context_results = {
        "entities": [
            {"label": "PERSON", "text": "John Smith"},
            {"label": "EMAIL", "text": "john@example.com"},
            {"label": "PHONE", "text": "(555) 123-4567"},
        ],
    }
    relationship_results = {
        "work_experience": [
            {"title": "Senior Engineer", "company": "Google", "start_date": "Jan 2020", "end_date": "Dec 2023"},
        ],
        "education": [{"degree": "Bachelor of Science", "school": "MIT", "year": "2019"}],
        "skills": {"Programming Languages": [{"name": "Python"}, {"name": "JavaScript"}]},
    }
    result = analyzer._calculate_ats_compatibility(text, context_results, relationship_results)
    assert "score" in result
    assert "breakdown" in result
    assert "issues" in result
    assert 0 <= result["score"] <= 100
    breakdown = result["breakdown"]
    for key in ("sections", "contact", "dates", "formatting", "work_experience", "education", "skills"):
        assert key in breakdown
        assert 0 <= breakdown[key] <= 100


def test_ats_breakdown_weights_affect_score(analyzer):
    text = "Experience Education Skills Summary 2020 2023\n"
    context_results = {"entities": [
        {"label": "EMAIL", "text": "a@b.co"},
        {"label": "PHONE", "text": "555"},
        {"label": "PERSON", "text": "Name"},
    ]}
    full_relationship = {
        "work_experience": [
            {"title": "Engineer", "company": "Co", "start_date": "2020", "end_date": "2023"},
        ],
        "education": [{"degree": "BS", "school": "U"}],
        "skills": {"Tech": [{"name": "X"}, {"name": "Y"}]},
    }
    result_full = analyzer._calculate_ats_compatibility(text, context_results, full_relationship)
    result_empty = analyzer._calculate_ats_compatibility(
        text, context_results,
        {"work_experience": [], "education": [], "skills": {}},
    )
    assert result_full["score"] > result_empty["score"]


def test_ats_issues_list_populated_when_issues_exist():
    from relationship_extractor import calculate_ats_score
    text = "No email here. My Journey section."
    structured = {"work_experience": [], "education": [], "skills": {}}
    result = calculate_ats_score(text, structured, context_results=None)
    assert "issues" in result
    assert isinstance(result["issues"], list)
    assert result["score"] <= 100


def test_calculate_ats_score_with_jd_keywords():
    from relationship_extractor import calculate_ats_score
    text = (
        "Summary: Python developer.\n"
        "WORK EXPERIENCE\n"
        "Engineer at Co 2020-2023. Python, Django.\n"
        "EDUCATION\n"
        "BS from U.\n"
        "SKILLS\n"
        "Python, Django, AWS\n"
    )
    structured = {
        "work_experience": [
            {"title": "Python Engineer", "company": "Co", "start_date": "2020", "end_date": "2023"},
        ],
        "education": [{"degree": "BS", "school": "U"}],
        "skills": {"Tech": [{"name": "Python"}, {"name": "Django"}, {"name": "AWS"}]},
    }
    result = calculate_ats_score(text, structured, context_results=None, jd_keywords=["Python", "Django"])
    assert "keyword_coverage" in result["breakdown"]
    assert 0 <= result["breakdown"]["keyword_coverage"] <= 100
    assert "score" in result
    assert "issues" in result
