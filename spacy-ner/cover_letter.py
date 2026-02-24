"""
Generate cover letter from resume and job description using OpenAI.
Returns 3-paragraph cover letter text in JD tone.
"""
import json
import logging
import os
from typing import Dict, List, Any, Tuple, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)


def _get_openai_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def _resume_context_from_canonical(canonical: Dict[str, Any]) -> str:
    parts = []
    pi = canonical.get("personal_info") or {}
    if pi.get("name"):
        parts.append(f"Candidate: {pi.get('name')}")
    summary = (canonical.get("summary") or "").strip()
    if summary:
        parts.append(f"Summary: {summary[:500]}")
    work = canonical.get("work_experience") or []
    for exp in work[:4]:
        title = exp.get("title") or ""
        company = exp.get("company") or ""
        bullets = exp.get("bullets") or []
        bullets_str = "; ".join((b if isinstance(b, str) else str(b) for b in bullets[:3]))
        parts.append(f"{title} at {company}: {bullets_str}")
    return "\n".join(parts)


def generate_cover_letter_text(
    resume_canonical: Dict[str, Any],
    job_description: str,
    job_title: str = "",
) -> Tuple[str, List[str]]:
    """
    One OpenAI call to generate a 3-paragraph cover letter in JD tone using candidate experience.
    Returns (full_text, list of 3 paragraph strings).
    """
    client = _get_openai_client()
    default_paragraphs = [
        "I am writing to express my interest in this position. My background aligns well with the role.",
        "My experience has prepared me to contribute effectively to your team.",
        "I would welcome the opportunity to discuss how I can contribute to your organization.",
    ]
    if not client:
        return "\n\n".join(default_paragraphs), default_paragraphs

    context = _resume_context_from_canonical(resume_canonical)
    jd_snippet = (job_description or "")[:3000].strip() or "No job description provided."
    title_line = f"Target role: {job_title}\n\n" if job_title else ""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You write a professional cover letter. Output exactly 3 paragraphs. Match the tone of the job description. Use the candidate's experience; be specific and truthful. No greetings or sign-offs; only the 3 body paragraphs. Respond with a JSON object: {\"paragraphs\": [\"...\", \"...\", \"...\"]}.",
                },
                {
                    "role": "user",
                    "content": f"""{title_line}Job description:\n{jd_snippet}\n\nCandidate resume context:\n{context}\n\nWrite 3 paragraphs for the cover letter body. Return JSON with key \"paragraphs\" (array of 3 strings).""",
                },
            ],
            max_tokens=800,
            temperature=0.4,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
        data = json.loads(raw)
        paras = data.get("paragraphs")
        if isinstance(paras, list) and len(paras) >= 3:
            paras = [str(p).strip() for p in paras[:3]]
            return "\n\n".join(paras), paras
        if isinstance(paras, list):
            paras = [str(p).strip() for p in paras if p]
            while len(paras) < 3:
                paras.append("")
            return "\n\n".join(paras), paras[:3]
    except Exception as e:
        logger.warning("Cover letter generation failed: %s", e)
    return "\n\n".join(default_paragraphs), default_paragraphs
