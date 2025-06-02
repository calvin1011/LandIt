import spacy

# Load the trained model
nlp = spacy.load("output")

# Try it on a new resume sentence
doc = nlp("Jordan Smith earned a degree in Cybersecurity from UCLA in 2023.")

# Print out the detected entities
for ent in doc.ents:
    print(ent.text, "→", ent.label_)
