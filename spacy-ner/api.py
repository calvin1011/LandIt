import spacy
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import logging
from typing import List, Optional, Dict, Any
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load trained spaCy model
try:
    nlp = spacy.load("output")
    logger.info(f"Successfully loaded spaCy model with labels: {nlp.get_pipe('ner').labels}")
except Exception as e:
    logger.error(f"Failed to load spaCy model: {e}")
    # For development, you could fall back to a blank model
    nlp = spacy.blank("en")
    logger.warning("Using blank model - please check your model path")

app = FastAPI(title="LandIt Resume Parser API", version="1.1.0")


class ResumeText(BaseModel):
    text: str


class EntityResponse(BaseModel):
    text: str
    label: str
    start: Optional[int] = None
    end: Optional[int] = None
    confidence: Optional[float] = None


class ParseResponse(BaseModel):
    entities: List[EntityResponse]
    processing_stats: Dict[str, Any]


def estimate_confidence(ent) -> float:
    """
    Estimate confidence for entities based on characteristics
    This helps filter out low-quality extractions
    """
    confidence = 0.8  # Base confidence

    # Boost confidence for well-formed entities
    if ent.label_ == "EMAIL" and "@" in ent.text and "." in ent.text:
        confidence = 0.95
    elif ent.label_ == "PHONE" and re.match(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', ent.text):
        confidence = 0.9
    elif ent.label_ == "NAME" and 2 <= len(ent.text.split()) <= 3:  # First + Last name
        confidence = 0.9
    elif ent.label_ == "SKILL" and len(ent.text.split()) <= 3:  # Short skill names
        confidence = 0.85
    elif ent.label_ == "COMPANY" and len(ent.text.split()) <= 4:  # Company names
        confidence = 0.85
    elif ent.label_ == "TITLE" and len(ent.text.split()) <= 5:  # Job titles
        confidence = 0.8

    # Reduce confidence for suspicious entities
    if len(ent.text) > 50:  # Very long entities are suspicious
        confidence *= 0.7
    if len(ent.text.split()) > 6:  # Too many words
        confidence *= 0.8
    if len(ent.text.strip()) < 2:  # Too short
        confidence *= 0.5

    return min(max(confidence, 0.1), 1.0)  # Clamp between 0.1 and 1.0


def post_process_entities(doc, min_confidence: float = 0.5) -> List[EntityResponse]:
    """
    Post-process entities to improve quality and consistency
    """
    entities = []
    seen_entities = set()

    for ent in doc.ents:
        # Skip empty entities
        entity_text = ent.text.strip()
        if not entity_text:
            continue

        # Calculate confidence
        confidence = estimate_confidence(ent)

        # Skip low-confidence entities
        if confidence < min_confidence:
            continue

        # Create unique key for deduplication
        unique_key = f"{entity_text.lower()}_{ent.label_}"
        if unique_key in seen_entities:
            continue
        seen_entities.add(unique_key)

        # Additional validation per entity type
        if ent.label_ == "EMAIL":
            if not ("@" in entity_text and "." in entity_text):
                continue
        elif ent.label_ == "PHONE":
            digits = re.findall(r'\d', entity_text)
            if len(digits) < 7:  # Minimum digits for a phone number
                continue
        elif ent.label_ == "NAME":
            # Skip names that are too long or contain suspicious patterns
            if len(entity_text) > 30 or re.search(r'\d', entity_text):
                continue
            words = entity_text.split()
            if len(words) > 4:  # Too many words for a name
                continue

        entities.append(EntityResponse(
            text=entity_text,
            label=ent.label_,
            start=ent.start_char,
            end=ent.end_char,
            confidence=confidence
        ))

    return entities


def validate_input_text(text: str) -> str:
    """
    Basic input validation and cleanup
    """
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    # Limit text length to prevent processing issues
    if len(text) > 50000:  # 50K character limit
        logger.warning(f"Text truncated from {len(text)} to 50000 characters")
        text = text[:50000]

    return text.strip()


@app.get("/")
def root():
    return {
        "message": "LandIt Resume Parser is running!",
        "version": "1.1.0",
        "model_labels": list(nlp.get_pipe('ner').labels) if "ner" in nlp.pipe_names else [],
        "features": [
            "Text preprocessing",
            "Confidence scoring",
            "Entity deduplication",
            "Quality filtering"
        ]
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": "ner" in nlp.pipe_names,
        "labels_count": len(nlp.get_pipe('ner').labels) if "ner" in nlp.pipe_names else 0
    }


@app.post("/parse-resume", response_model=ParseResponse)
def parse_resume(data: ResumeText):
    """
    Parse resume text and extract entities with improved processing
    """
    start_time = time.time()

    try:
        # Validate input
        text = validate_input_text(data.text)
        logger.info(f"Processing text of length {len(text)}")

        # Process with spaCy
        doc = nlp(text)

        # Post-process entities
        entities = post_process_entities(doc, min_confidence=0.5)

        processing_time = time.time() - start_time

        # Generate processing stats
        stats = {
            "text_length": len(text),
            "processing_time_seconds": round(processing_time, 3),
            "total_entities_found": len(doc.ents),
            "entities_after_filtering": len(entities),
            "filter_ratio": round(len(entities) / len(doc.ents), 2) if len(doc.ents) > 0 else 0,
            "entity_types": list(set([e.label for e in entities])),
            "average_confidence": round(sum([e.confidence for e in entities]) / len(entities), 2) if entities else 0
        }

        logger.info(f"Processed resume: {len(entities)} entities in {processing_time:.2f}s")

        return ParseResponse(
            entities=entities,
            processing_stats=stats
        )

    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/test-model")
def test_model(data: ResumeText):
    """
    Test endpoint to see raw model output (for debugging)
    """
    try:
        text = validate_input_text(data.text)
        doc = nlp(text)

        raw_entities = [
            {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": estimate_confidence(ent)
            }
            for ent in doc.ents
        ]

        return {
            "text_preview": text[:200] + "..." if len(text) > 200 else text,
            "raw_entities": raw_entities,
            "entity_count": len(raw_entities),
            "model_info": {
                "model_name": nlp.meta.get("name", "custom"),
                "labels": list(nlp.get_pipe('ner').labels) if "ner" in nlp.pipe_names else []
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)