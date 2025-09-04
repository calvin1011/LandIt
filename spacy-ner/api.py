import spacy
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import logging
from typing import List, Optional, Dict, Any
import time
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load hybrid trained spaCy model
try:
    # Try hybrid model first
    model_path = "output_hybrid"
    nlp = spacy.load(model_path)
    logger.info(f"✅ Successfully loaded HYBRID model from: {model_path}")

    # Load training metadata if available
    metadata_path = Path(model_path) / "training_info.json"
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            training_info = json.load(f)
        logger.info(
            f"📊 Model info: {training_info.get('model_type', 'unknown')} with {training_info.get('total_labels', 'unknown')} labels")
    else:
        training_info = {}

except Exception as e:
    logger.error(f"❌ Failed to load hybrid model: {e}")
    try:
        # Fallback to original custom model
        nlp = spacy.load("output")
        training_info = {"model_type": "custom_only"}
        logger.warning("⚠️ Using fallback custom model")
    except Exception as e2:
        logger.error(f"❌ Failed to load any model: {e2}")
        nlp = spacy.blank("en")
        training_info = {"model_type": "blank"}
        logger.warning("⚠️ Using blank model - please check your model paths")

app = FastAPI(title="LandIt Resume Parser API - Hybrid Edition", version="2.0.0")


class ResumeText(BaseModel):
    text: str


class EntityResponse(BaseModel):
    text: str
    label: str
    start: Optional[int] = None
    end: Optional[int] = None
    confidence: Optional[float] = None
    source: Optional[str] = None  # "pretrained" or "custom"


class ParseResponse(BaseModel):
    entities: List[EntityResponse]
    processing_stats: Dict[str, Any]
    model_info: Dict[str, Any]


# Define custom resume labels (these are your specific ones)
CUSTOM_RESUME_LABELS = {
    "NAME", "EMAIL", "PHONE", "TITLE", "COMPANY", "SKILL",
    "EDUCATION", "DEGREE", "FIELD", "EXPERIENCE", "LOCATION"
}


def estimate_confidence(ent) -> float:
    """Enhanced confidence estimation for hybrid model"""
    confidence = 0.8  # Base confidence

    # Higher confidence for well-formed entities
    if ent.label_ == "EMAIL" and "@" in ent.text and "." in ent.text:
        confidence = 0.95
    elif ent.label_ == "PHONE" and re.match(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', ent.text):
        confidence = 0.95
    elif ent.label_ == "NAME" and 2 <= len(ent.text.split()) <= 3:
        confidence = 0.9
    elif ent.label_ in ["SKILL", "TITLE", "COMPANY"] and len(ent.text.split()) <= 4:
        confidence = 0.85

    # Pre-trained model labels get different confidence
    elif ent.label_ in ["PERSON", "ORG", "GPE", "DATE"]:  # spaCy's standard labels
        confidence = 0.9  # Pre-trained model is usually quite good

    # Reduce confidence for suspicious entities
    if len(ent.text) > 50:
        confidence *= 0.7
    if len(ent.text.split()) > 6:
        confidence *= 0.8
    if len(ent.text.strip()) < 2:
        confidence *= 0.5

    return min(max(confidence, 0.1), 1.0)


def determine_entity_source(label: str) -> str:
    """Determine if entity comes from custom training or pre-trained model"""
    if label in CUSTOM_RESUME_LABELS:
        return "custom"
    elif label in ["PERSON", "ORG", "GPE", "DATE", "TIME", "PERCENT", "MONEY", "CARDINAL"]:
        return "pretrained"
    else:
        return "unknown"


def post_process_entities(doc, min_confidence: float = 0.5) -> List[EntityResponse]:
    """Enhanced post-processing for hybrid model"""
    entities = []
    seen_entities = set()

    for ent in doc.ents:
        entity_text = ent.text.strip()
        if not entity_text:
            continue

        confidence = estimate_confidence(ent)

        if confidence < min_confidence:
            continue

        # Enhanced deduplication - consider both text and position
        unique_key = f"{entity_text.lower()}_{ent.label_}_{ent.start_char}"
        if unique_key in seen_entities:
            continue
        seen_entities.add(unique_key)

        # Enhanced validation per entity type
        if ent.label_ == "EMAIL":
            if not ("@" in entity_text and "." in entity_text):
                continue
        elif ent.label_ == "PHONE":
            digits = re.findall(r'\d', entity_text)
            if len(digits) < 7:
                continue
        elif ent.label_ in ["NAME", "PERSON"]:
            if len(entity_text) > 30 or re.search(r'\d', entity_text):
                continue
            words = entity_text.split()
            if len(words) > 4:
                continue

        # Map some pre-trained labels to custom ones for consistency
        mapped_label = ent.label_
        if ent.label_ == "PERSON" and not any(e.label_ == "NAME" for e in entities):
            mapped_label = "NAME"  # Use NAME instead of PERSON for resumes
        elif ent.label_ == "ORG":
            mapped_label = "COMPANY"  # Use COMPANY instead of ORG for resumes

        entities.append(EntityResponse(
            text=entity_text,
            label=mapped_label,
            start=ent.start_char,
            end=ent.end_char,
            confidence=confidence,
            source=determine_entity_source(ent.label_)
        ))

    return entities


def validate_input_text(text: str) -> str:
    """Enhanced input validation"""
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    if len(text) > 50000:
        logger.warning(f"Text truncated from {len(text)} to 50000 characters")
        text = text[:50000]

    return text.strip()


@app.get("/")
def root():
    model_type = training_info.get("model_type", "unknown")
    return {
        "message": "LandIt Resume Parser - Hybrid Edition is running!",
        "version": "2.0.0",
        "model_type": model_type,
        "model_labels": list(nlp.get_pipe('ner').labels) if "ner" in nlp.pipe_names else [],
        "custom_labels": list(CUSTOM_RESUME_LABELS),
        "features": [
            "Hybrid pre-trained + custom model",
            "Enhanced confidence scoring",
            "Label mapping for consistency",
            "Source tracking (custom vs pretrained)"
        ]
    }


@app.get("/health")
def health_check():
    """Enhanced health check"""
    model_labels = list(nlp.get_pipe('ner').labels) if "ner" in nlp.pipe_names else []
    custom_count = len([l for l in model_labels if l in CUSTOM_RESUME_LABELS])
    pretrained_count = len(model_labels) - custom_count

    return {
        "status": "healthy",
        "model_loaded": "ner" in nlp.pipe_names,
        "model_type": training_info.get("model_type", "unknown"),
        "total_labels": len(model_labels),
        "custom_labels": custom_count,
        "pretrained_labels": pretrained_count
    }


@app.post("/parse-resume", response_model=ParseResponse)
def parse_resume(data: ResumeText):
    """Enhanced parsing with hybrid model"""
    start_time = time.time()

    try:
        text = validate_input_text(data.text)
        logger.info(f"Processing text of length {len(text)}")

        # Process with hybrid spaCy model
        doc = nlp(text)

        # Enhanced post-processing
        entities = post_process_entities(doc, min_confidence=0.5)

        processing_time = time.time() - start_time

        # Enhanced processing stats
        custom_entities = [e for e in entities if e.source == "custom"]
        pretrained_entities = [e for e in entities if e.source == "pretrained"]

        stats = {
            "text_length": len(text),
            "processing_time_seconds": round(processing_time, 3),
            "total_entities_found": len(doc.ents),
            "entities_after_filtering": len(entities),
            "custom_entities": len(custom_entities),
            "pretrained_entities": len(pretrained_entities),
            "filter_ratio": round(len(entities) / len(doc.ents), 2) if len(doc.ents) > 0 else 0,
            "entity_types": list(set([e.label for e in entities])),
            "average_confidence": round(sum([e.confidence for e in entities]) / len(entities), 2) if entities else 0
        }

        model_info = {
            "model_type": training_info.get("model_type", "unknown"),
            "base_model": training_info.get("base_model", "unknown"),
            "total_labels": training_info.get("total_labels", len(nlp.get_pipe('ner').labels)),
            "training_examples": training_info.get("training_examples", "unknown")
        }

        logger.info(
            f"Processed resume: {len(entities)} entities ({len(custom_entities)} custom, {len(pretrained_entities)} pretrained) in {processing_time:.2f}s")

        return ParseResponse(
            entities=entities,
            processing_stats=stats,
            model_info=model_info
        )

    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/test-model")
def test_model(data: ResumeText):
    """Enhanced test endpoint for hybrid model"""
    try:
        text = validate_input_text(data.text)
        doc = nlp(text)

        raw_entities = []
        for ent in doc.ents:
            raw_entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": estimate_confidence(ent),
                "source": determine_entity_source(ent.label_)
            })

        # Group by source
        custom_entities = [e for e in raw_entities if e["source"] == "custom"]
        pretrained_entities = [e for e in raw_entities if e["source"] == "pretrained"]

        return {
            "text_preview": text[:200] + "..." if len(text) > 200 else text,
            "raw_entities": raw_entities,
            "entity_count": len(raw_entities),
            "custom_entities": len(custom_entities),
            "pretrained_entities": len(pretrained_entities),
            "model_info": {
                "model_type": training_info.get("model_type", "unknown"),
                "model_name": nlp.meta.get("name", "custom"),
                "labels": list(nlp.get_pipe('ner').labels) if "ner" in nlp.pipe_names else []
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)