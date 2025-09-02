import spacy
from spacy.training.example import Example
import random
import json
import warnings
import os

# Suppress alignment warnings for spaCy
warnings.filterwarnings("ignore", category=UserWarning, module="spacy")

# --- Function Definitions ---
# All helper functions should be defined at the beginning of the script.

def load_training_data():
    """Load existing training data with fallback options."""
    try:
        # Try to load fixed data first
        with open("train_data_fixed.json", "r", encoding="utf-8") as f:
            training_data = json.load(f)
        print(f"✅ Loaded {len(training_data)} examples from train_data_fixed.json")
        return training_data
    except FileNotFoundError:
        try:
            # Fall back to original data
            with open("train_data.json", "r", encoding="utf-8") as f:
                training_data = json.load(f)
            print(f"⚠️  Using original train_data.json with {len(training_data)} examples")
            print("   Consider running the data fixer first!")
            return training_data
        except FileNotFoundError:
            print("❌ No training data file found!")
            return []

def load_all_prelabeled_data(directory):
    """Load all pre-labeled JSON files from a directory."""
    all_data = []
    file_count = 0
    # List all files in the specified directory
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    new_data = json.load(f)
                    all_data.extend(new_data)
                    file_count += 1
                    print(f"✅ Loaded {len(new_data)} examples from {filename}")
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"❌ Failed to load {filename}: {e}")
    print(f"✅ Loaded data from a total of {file_count} file(s).")
    return all_data

def validate_example(nlp, text, entities):
    """Validate a single training example against the spaCy model's vocabulary."""
    try:
        doc = nlp.make_doc(text)
        example = Example.from_dict(doc, {"entities": entities})
        return example
    except Exception as e:
        print(f"❌ Invalid example: {text[:30]}... - {str(e)[:50]}...")
        return None

# --- Main Script Execution ---

# Load the English model
try:
    nlp = spacy.load("en_core_web_sm")
    print("✅ Loaded en_core_web_sm model")
except OSError:
    print("⚠️  en_core_web_sm not found, creating blank model")
    nlp = spacy.blank("en")

# Add NER pipe if missing
if "ner" not in nlp.pipe_names:
    ner = nlp.add_pipe("ner")
    print("✅ Added NER pipe")
else:
    ner = nlp.get_pipe("ner")
    print("✅ Using existing NER pipe")

# Get other pipes to disable during training
other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
if other_pipes:
    print(f"🔇 Will disable pipes during training: {other_pipes}")

# Load existing training data
TRAIN_DATA = load_training_data()

# Load ALL pre-labeled data from a folder and combine
NEW_DATA = load_all_prelabeled_data("../data/kaggle/processed/")
if NEW_DATA:
    TRAIN_DATA.extend(NEW_DATA)
    print(f"✅ Combined datasets. Total examples: {len(TRAIN_DATA)}")

if not TRAIN_DATA:
    print("❌ No training data available after combining datasets. Exiting.")
    exit(1)

# Collect all labels and validate examples
print("\n📋 Processing training examples...")
all_labels = set()
valid_examples = []
skipped_examples = 0

for text, annotations in TRAIN_DATA:
    entities = annotations.get("entities", [])

    # Collect labels
    for start, end, label in entities:
        all_labels.add(label)

    # Validate example
    example = validate_example(nlp, text, entities)
    if example:
        valid_examples.append(example)
    else:
        skipped_examples += 1

print(f"✅ Valid examples: {len(valid_examples)}")
print(f"❌ Skipped examples: {skipped_examples}")
print(f"🏷️  Found {len(all_labels)} unique labels:")

# Print labels in organized groups
label_groups = {
    "Basic Info": ["NAME", "TITLE", "COMPANY", "EMAIL", "PHONE", "ADDRESS", "LOCATION"],
    "Education": ["EDUCATION", "DEGREE", "FIELD", "GRAD_YEAR", "GPA", "DISTINCTION"],
    "Skills": ["SKILL", "TECHNOLOGY", "TOOL", "LANGUAGE", "PROFICIENCY_LEVEL"],
    "Experience": ["EXPERIENCE", "EXPERIENCE_DURATION", "ACHIEVEMENT", "LEADERSHIP"],
    "Other": []
}

for label in sorted(all_labels):
    categorized = False
    for category, category_labels in label_groups.items():
        if label in category_labels:
            categorized = True
            break
    if not categorized:
        label_groups["Other"].append(label)

for category, labels in label_groups.items():
    if labels:
        print(f"  {category}: {', '.join(sorted(labels))}")

# Add labels to NER
print(f"\n🎯 Adding {len(all_labels)} labels to NER...")
for label in all_labels:
    ner.add_label(label)

# --- KEY FIX: Initialize the model before training ---
print("\n🛠️ Initializing model for training...")
nlp.initialize()

print(f"\n🚀 Starting training with {len(valid_examples)} examples...")

# Training loop
with nlp.disable_pipes(*other_pipes):
    optimizer = nlp.resume_training()

    for iteration in range(20):
        print(f"\n📈 Iteration {iteration + 1}/20")

        # Shuffle data
        random.shuffle(valid_examples)
        losses = {}

        # Process in batches for better memory management
        batch_size = 8
        total_batches = len(valid_examples) // batch_size + (1 if len(valid_examples) % batch_size else 0)

        successful_updates = 0

        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(valid_examples))
            batch = valid_examples[start_idx:end_idx]

            try:
                nlp.update(batch, drop=0.3, losses=losses)
                successful_updates += 1
            except Exception as e:
                print(f"    ⚠️  Batch {batch_num + 1} failed: {str(e)[:50]}...")
                continue

        print(f"    ✅ Successful batches: {successful_updates}/{total_batches}")

        # Print losses every 5 iterations
        if iteration % 5 == 0 or iteration == 19:
            if losses:
                print(f"    📊 Losses: {losses}")

print("\n🎉 Training completed!")

# Test the model
print("\n🧪 Testing trained model:")
test_sentences = [
    "John Smith is a Software Engineer at Google.",
    "Jane graduated from MIT with a Computer Science degree in 2020.",
    "Proficient in Python, JavaScript, and React with 5 years experience.",
    "Contact: john.doe@email.com | Phone: (555) 123-4567"
]

for sentence in test_sentences:
    doc = nlp(sentence)
    print(f"\n📝 Text: {sentence}")
    if doc.ents:
        for ent in doc.ents:
            print(f"    🎯 '{ent.text}' → {ent.label_}")
    else:
        print("    ❌ No entities found")

# Save the trained model
output_dir = "output"
try:
    nlp.to_disk(output_dir)
    print(f"\n💾 Model saved to /{output_dir}/")
    print(f"📁 You can now use this model in your resume parser!")
except Exception as e:
    print(f"❌ Failed to save model: {e}")

print("\n✨ Training complete! Next steps:")
print("1. Test the model with real resume data")
print("2. Integrate with your resume parser application")
print("3. Monitor performance and add more training data as needed")