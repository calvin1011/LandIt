import spacy
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Load trained spaCy model
try:
    nlp = spacy.load("output")
except Exception as e:
    raise RuntimeError(f"Failed to load spaCy model: {e}")

app = FastAPI(title="LandIt Resume Parser API")


# Request schema
class ResumeText(BaseModel):
    text: str


@app.get("/")
def root():
    return {"message": "LandIt Resume Parser is running!"}


@app.post("/parse-resume")
def parse_resume(data: ResumeText):
    if not data.text:
        raise HTTPException(status_code=400, detail="No resume text provided.")

    doc = nlp(data.text)

    entities = [
        {"text": ent.text, "label": ent.label_}
        for ent in doc.ents
    ]

    return {"entities": entities}
