import spacy
from spacy.training.example import Example
import random
import json

# Load small English model
nlp = spacy.load("en_core_web_sm")

# Add NER pipe if missing
if "ner" not in nlp.pipe_names:
    ner = nlp.add_pipe("ner")
else:
    ner = nlp.get_pipe("ner")

# Load training data
with open("train_data.json", "r") as f:
    TRAIN_DATA = json.load(f)

# Add labels
for _, annotations in TRAIN_DATA:
    for ent in annotations.get("entities"):
        ner.add_label(ent[2])

# Fine-tune model
optimizer = nlp.resume_training()
for i in range(20):
    random.shuffle(TRAIN_DATA)
    losses = {}
    for text, annotations in TRAIN_DATA:
        example = Example.from_dict(nlp.make_doc(text), annotations)
        nlp.update([example], drop=0.5, losses=losses)
    print(f"Losses at iteration {i}: {losses}")

# Save trained model
nlp.to_disk("output")
print("Model saved to /output/")
