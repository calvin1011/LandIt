"""
Pipeline for enhancing a resume for a specific job description.
Steps: JD analysis, gap analysis, experience rewriting, skills reordering, summary generation.
"""
import json
import logging
import os
from typing import Dict, List, Any, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)


def _get_openai_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def analyze_job_description(job_description: str) -> Dict[str, Any]:
    """
    One OpenAI call to extract from raw JD: job title, experience level, required years,
    key responsibilities, company tone, and repeated keywords (important for ATS).
    """
    client = _get_openai_client()
    if not client:
        return {
            "title": "",
            "experience_level": "mid",
            "required_years": None,
            "key_responsibilities": [],
            "company_tone": "professional",
            "repeated_keywords": [],
            "description": job_description[:2000],
        }

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You extract structured data from job descriptions. Respond only with valid JSON.",
                },
                {
                    "role": "user",
                    "content": f"""From this job description extract and return a single JSON object with these exact keys:
- title (string): job title
- experience_level (string): one of entry, mid, senior, executive
- required_years (number or null): years of experience if stated
- key_responsibilities (array of strings): 3-5 main responsibilities
- company_tone (string): e.g. professional, startup, formal, collaborative
- repeated_keywords (array of strings): terms that appear multiple times or are clearly important for ATS (skills, tools, verbs)

Job description:
{job_description[:4000]}
""",
                },
            ],
            max_tokens=800,
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
        data = json.loads(raw)
        return {
            "title": data.get("title") or "",
            "experience_level": data.get("experience_level") or "mid",
            "required_years": data.get("required_years"),
            "key_responsibilities": data.get("key_responsibilities") or [],
            "company_tone": data.get("company_tone") or "professional",
            "repeated_keywords": data.get("repeated_keywords") or [],
            "description": job_description[:2000],
        }
    except Exception as e:
        logger.warning(f"JD analysis failed: {e}")
        return {
            "title": "",
            "experience_level": "mid",
            "required_years": None,
            "key_responsibilities": [],
            "company_tone": "professional",
            "repeated_keywords": [],
            "description": job_description[:2000],
        }


def rewrite_experience_bullets(
    bullets: List[str],
    jd_keywords: List[str],
    job_tone: str,
    job_title: str,
) -> List[str]:
    """
    Rewrite work-experience bullets to incorporate JD keywords and tone; keep truthful, quantify where possible.
    Single batched OpenAI call.
    """
    if not bullets:
        return []
    client = _get_openai_client()
    if not client:
        return bullets

    keywords_str = ", ".join(jd_keywords[:25]) if jd_keywords else "general professional"
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You rewrite resume bullet points to better match a job description. Keep facts truthful. Prefer adding numbers/metrics where plausible. Output a JSON array of strings, one per bullet, in the same order.",
                },
                {
                    "role": "user",
                    "content": f"""Job title: {job_title}. Tone: {job_tone}. Keywords to weave in where relevant: {keywords_str}.

Rewrite each of these bullets to better match the job while staying truthful. Return only a JSON array of strings (same length and order):
{json.dumps(bullets)}
""",
                },
            ],
            max_tokens=2000,
            temperature=0.4,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
        rewritten = json.loads(raw)
        if isinstance(rewritten, list) and len(rewritten) == len(bullets):
            return [str(b).strip() for b in rewritten]
    except Exception as e:
        logger.warning(f"Bullet rewrite failed: {e}")
    return bullets


def reorder_skills_for_jd(
    skills_dict: Dict[str, List[str]],
    jd_keywords: List[str],
) -> Dict[str, List[str]]:
    """
    Reorder skills so JD-heavy categories and JD-matching skills appear first.
    Same category order as used by Go (order of keys; within each key, list order).
    """
    if not skills_dict or not jd_keywords:
        return skills_dict

    jd_set = {k.lower().strip() for k in jd_keywords if k}
    if not jd_set:
        return skills_dict

    def score_category(skill_list: List[str]) -> int:
        count = sum(1 for s in skill_list if (s if isinstance(s, str) else str(s)).lower().strip() in jd_set)
        return count

    def sort_skills_in_category(skill_list: List[str]) -> List[str]:
        def key(s: str) -> tuple:
            s_str = s if isinstance(s, str) else str(s)
            return (0 if s_str.lower().strip() in jd_set else 1, s_str.lower())
        return sorted(skill_list, key=key)

    categories_with_scores = [(cat, score_category(slist), slist) for cat, slist in skills_dict.items()]
    categories_with_scores.sort(key=lambda x: -x[1])
    return {
        cat: sort_skills_in_category(slist)
        for cat, _, slist in categories_with_scores
    }


def generate_summary_for_job(
    work_experience: List[Dict],
    education: List[Dict],
    jd_title: str,
    jd_tone: str,
    key_responsibilities: List[str],
    current_summary: str,
) -> str:
    """
    One OpenAI call to generate a 3-4 sentence summary mirroring JD language and job title.
    """
    client = _get_openai_client()
    if not client:
        return current_summary or "Experienced professional."

    exp_preview = []
    for we in (work_experience or [])[:3]:
        title = we.get("title") or ""
        company = we.get("company") or ""
        bullets = we.get("bullets") or []
        first_bullets = [b if isinstance(b, str) else str(b) for b in bullets[:2]]
        exp_preview.append(f"{title} at {company}: " + "; ".join(first_bullets))
    edu_preview = []
    for ed in (education or [])[:2]:
        degree = ed.get("degree") or ""
        school = ed.get("school") or ""
        edu_preview.append(f"{degree} at {school}")
    context = "Work: " + " | ".join(exp_preview) + ". Education: " + " | ".join(edu_preview)

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You write a 3-4 sentence professional resume summary that mirrors the job title and tone. Reference the candidate's relevant experience. No placeholder text.",
                },
                {
                    "role": "user",
                    "content": f"""Target job title: {jd_title}. Tone: {jd_tone}. Key responsibilities: {', '.join(key_responsibilities[:5])}.

Candidate context: {context}
Current summary (can use as base): {current_summary or 'None'}

Write a 3-4 sentence summary for the resume.""",
                },
            ],
            max_tokens=300,
            temperature=0.5,
        )
        summary = (response.choices[0].message.content or "").strip()
        return summary if summary else (current_summary or "Experienced professional.")
    except Exception as e:
        logger.warning(f"Summary generation failed: {e}")
        return current_summary or "Experienced professional."


def run_enhance_pipeline(
    canonical_payload: Dict[str, Any],
    jd_analysis: Dict[str, Any],
    extract_skills_fn,
    user_experience_level: str = "mid",
) -> Dict[str, Any]:
    """
    Run the five-step enhance pipeline. canonical_payload is the initial payload from
    build_canonical_payload (from structured_data). jd_analysis from analyze_job_description.
    extract_skills_fn is api.extract_skills (injected to avoid circular import).
    Returns the enhanced canonical payload (with metadata preserved/updated).
    """
    jd_keywords = list(
        set(
            (jd_analysis.get("repeated_keywords") or [])
            + extract_skills_fn(jd_analysis.get("description") or "")
        )
    )[:40]
    job_title = jd_analysis.get("title") or ""
    job_tone = jd_analysis.get("company_tone") or "professional"
    key_responsibilities = jd_analysis.get("key_responsibilities") or []

    enhanced = dict(canonical_payload)
    work = list(enhanced.get("work_experience") or [])
    personal = enhanced.get("personal_info") or {}
    education = list(enhanced.get("education") or [])
    skills = dict(enhanced.get("skills") or {})

    for exp in work:
        bullets = exp.get("bullets") or []
        if isinstance(bullets[0], dict):
            bullets = [b.get("text") or str(b) for b in bullets]
        rewritten = rewrite_experience_bullets(bullets, jd_keywords, job_tone, job_title)
        exp["bullets"] = rewritten

    enhanced["work_experience"] = work
    enhanced["skills"] = reorder_skills_for_jd(skills, jd_keywords)
    current_summary = (enhanced.get("summary") or "").strip()
    enhanced["summary"] = generate_summary_for_job(
        work, education, job_title, job_tone, key_responsibilities, current_summary
    )
    if enhanced.get("metadata") is None:
        enhanced["metadata"] = {}
    enhanced["metadata"]["job_title"] = job_title

    return enhanced
