"""
Build canonical resume payload for the Go export service.
Payload shape is agreed with go-export-service; both FastAPI and Go use this contract.
"""
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def _ensure_dict(obj: Any) -> dict:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, str):
        try:
            return json.loads(obj)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def _ensure_list(obj: Any) -> list:
    if obj is None:
        return []
    if isinstance(obj, list):
        return obj
    return []


def _work_exp_to_canonical(exp: Dict) -> Dict:
    bullets = exp.get("bullets") or exp.get("achievements") or []
    if not isinstance(bullets, list):
        bullets = [str(bullets)] if bullets else []
    bullets = [b if isinstance(b, str) else (b.get("text") or str(b)) for b in bullets]
    end = (exp.get("end_date") or "").strip().lower()
    is_current = end in ("present", "current", "now", "")
    return {
        "title": exp.get("title") or "",
        "company": exp.get("company") or "",
        "location": (exp.get("location") or "").strip(),
        "start_date": exp.get("start_date") or "",
        "end_date": exp.get("end_date") or "",
        "is_current": is_current,
        "bullets": bullets,
    }


def _education_to_canonical(edu: Dict) -> Dict:
    return {
        "degree": edu.get("degree") or "",
        "field": edu.get("field") or "",
        "school": edu.get("school") or "",
        "gpa": edu.get("gpa"),
        "honors": edu.get("honors"),
    }


def _skills_to_canonical(skills: Any) -> Dict[str, List[str]]:
    out = {}
    if not skills or not isinstance(skills, dict):
        return out
    for category, skill_list in skills.items():
        if not isinstance(skill_list, list):
            continue
        names = []
        for s in skill_list:
            if isinstance(s, dict):
                name = (s.get("name") or "").strip()
                if name:
                    names.append(name)
            elif isinstance(s, str) and s.strip():
                names.append(s.strip())
        if names:
            out[str(category).strip() or "Other"] = names
    return out


def _personal_info_to_canonical(personal: Any) -> Dict[str, str]:
    if not personal or not isinstance(personal, dict):
        return {}
    return {
        "name": (personal.get("name") or "").strip(),
        "email": (personal.get("email") or "").strip(),
        "phone": (personal.get("phone") or "").strip(),
        "location": (personal.get("location") or "").strip(),
        "linkedin": (personal.get("linkedin") or "").strip(),
        "github": (personal.get("github") or "").strip(),
        "portfolio": (personal.get("portfolio") or "").strip(),
    }


def build_canonical_payload(
    resume_source: Dict,
    template_name: str = "classic",
    export_format: str = "pdf",
    ats_mode: bool = False,
    job_title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build the canonical JSON payload for the Go export service from either
    a DB user_resume row (with structured_data or enhanced_resume) or an
    already-canonical enhanced resume dict.

    resume_source: either full user_resume row (with structured_data, enhanced_resume)
                   or a dict that may already be in canonical shape (e.g. enhanced_resume).
    """
    enhanced = resume_source.get("enhanced_resume")
    if enhanced is not None:
        raw = enhanced if isinstance(enhanced, dict) else _ensure_dict(enhanced)
        if raw.get("metadata") is not None and "work_experience" in raw:
            payload = dict(raw)
            payload.setdefault("metadata", {})
            payload["metadata"].update({
                "template_name": template_name,
                "export_format": export_format,
                "ats_mode": ats_mode,
                "job_title": (job_title or (payload["metadata"].get("job_title") or "")).strip(),
            })
            return payload

    structured = _ensure_dict(resume_source.get("structured_data"))
    personal = _personal_info_to_canonical(structured.get("personal_info"))
    summary = (structured.get("summary") or "").strip()
    if not summary and resume_source.get("resume_text"):
        summary = (resume_source.get("resume_text") or "")[:500].strip()

    work = [_work_exp_to_canonical(e) for e in _ensure_list(structured.get("work_experience"))]
    education = [_education_to_canonical(e) for e in _ensure_list(structured.get("education"))]
    skills = _skills_to_canonical(structured.get("skills"))
    certs = _ensure_list(structured.get("certifications"))
    certs = [c if isinstance(c, str) else str(c) for c in certs]

    return {
        "personal_info": personal,
        "summary": summary,
        "work_experience": work,
        "education": education,
        "skills": skills,
        "certifications": certs,
        "metadata": {
            "template_name": template_name,
            "export_format": export_format,
            "ats_mode": ats_mode,
            "job_title": (job_title or "").strip(),
        },
    }
