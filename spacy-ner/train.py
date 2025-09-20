import spacy
from spacy.training.example import Example
import random
import json
import warnings
from pathlib import Path

# Suppress alignment warnings for spaCy
warnings.filterwarnings("ignore", category=UserWarning, module="spacy")


# In your train.py, replace the load_clean_training_data function:
def load_clean_training_data():
    """Load cleaned training data"""
    training_files = [
        "train_data_cleaned.json",  # Use cleaned data first
        "train_data.json"
    ]

    for filename in training_files:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                training_data = json.load(f)
            print(f"✅ Loaded {len(training_data)} examples from {filename}")

            # Simplify labels further
            training_data = simplify_training_labels(training_data)
            print(f"📊 Simplified to {len(training_data)} examples with core labels")

            return training_data
        except FileNotFoundError:
            continue

    print("❌ No training data file found!")
    return []

def filter_quality_examples(training_data, max_examples=200):
    """Filter and limit to highest quality examples"""
    if not training_data:
        return []

    # Filter examples with reasonable entity counts (5-25 entities)
    quality_examples = []
    for text, annotations in training_data:
        entities = annotations.get("entities", [])
        if 5 <= len(entities) <= 25:  # Sweet spot for learning
            quality_examples.append((text, annotations))

    # Limit total examples for efficiency
    if len(quality_examples) > max_examples:
        quality_examples = quality_examples[:max_examples]
        print(f"⚡ Limited to {max_examples} examples for efficient training")

    print(f"📊 Using {len(quality_examples)} quality examples")
    return quality_examples


def validate_example(nlp, text, entities):
    """Validate a single training example"""
    try:
        doc = nlp.make_doc(text)
        example = Example.from_dict(doc, {"entities": entities})
        return example
    except Exception as e:
        print(f"❌ Invalid example: {text[:30]}... - {str(e)[:50]}...")
        return None


def analyze_labels(training_data):
    """Analyze and categorize labels from training data"""
    all_labels = set()
    label_counts = {}

    for text, annotations in training_data:
        entities = annotations.get("entities", [])
        for start, end, label in entities:
            all_labels.add(label)
            label_counts[label] = label_counts.get(label, 0) + 1

    return all_labels, label_counts

def simplify_training_labels(training_data):
    """Simplify training data labels to reduce complexity"""
    simplified_data = []

    for text, annotations in training_data:
        entities = annotations.get("entities", [])
        simplified_entities = []

        for start, end, label in entities:
            simplified_label = simplify_label(label)
            if simplified_label != "OTHER":  # Skip "OTHER" labels
                simplified_entities.append([start, end, simplified_label])

        if simplified_entities:
            simplified_data.append([text, {"entities": simplified_entities}])

    return simplified_data

def simplify_label(label: str) -> str:
    """Simplify labels to core categories"""
    label = label.upper()

    # Core resume labels
    core_mapping = {
        # Personal info
        'NAME': 'NAME', 'EMAIL': 'EMAIL', 'PHONE': 'PHONE',
        'LOCATION': 'LOCATION', 'ADDRESS': 'LOCATION',

        # Professional
        'TITLE': 'TITLE', 'COMPANY': 'COMPANY', 'ORGANIZATION': 'COMPANY',
        'EXPERIENCE': 'EXPERIENCE', 'INDUSTRY': 'SKILL',

        # Skills
        'SKILL': 'SKILL', 'TECHNOLOGY': 'SKILL', 'PLATFORM': 'SKILL',
        'PROGRAMMING_LANGUAGE': 'SKILL', 'TECHNICAL_SKILL': 'SKILL',
        'LANGUAGE': 'LANGUAGE', 'LANGUAGE_SKILL': 'LANGUAGE',

        # Education
        'EDUCATION': 'EDUCATION', 'DEGREE': 'DEGREE', 'SCHOOL': 'SCHOOL',
        'UNIVERSITY': 'SCHOOL', 'COLLEGE': 'SCHOOL', 'GPA': 'EDUCATION',

        # Other
        'CERTIFICATION': 'CERTIFICATION', 'PROJECT': 'PROJECT',
        'ACHIEVEMENT': 'ACHIEVEMENT', 'DATE': 'DATE', 'YEAR': 'DATE'
    }

    return core_mapping.get(label, 'OTHER')

def main():
    print("🚀 HYBRID RESUME NER TRAINING")
    print("=" * 50)
    print("Using: en_core_web_sm + Your Custom Resume Labels")
    print("=" * 50)

    # Load the pre-trained English model (the hybrid foundation)
    try:
        nlp = spacy.load("en_core_web_sm")
        print("✅ Loaded en_core_web_sm as base model")
        print(f"   Existing labels: {len(nlp.get_pipe('ner').labels)}")
    except OSError:
        print("❌ en_core_web_sm not found!")
        print("   Install it with: python -m spacy download en_core_web_sm")
        return

    # Load only your clean training data (skip Kaggle for now)
    training_data = load_clean_training_data()
    if not training_data:
        print("❌ No training data available. Exiting.")
        return

    # Filter to highest quality examples for efficient training
    quality_data = filter_quality_examples(training_data, max_examples=150)

    # Analyze labels
    custom_labels, label_counts = analyze_labels(quality_data)
    print(f"\n🏷️  Found {len(custom_labels)} custom resume labels:")

    # Group labels logically
    label_groups = {
        "Contact": ["NAME", "EMAIL", "PHONE", "ADDRESS", "LOCATION"],
        "Professional": ["TITLE", "COMPANY", "SKILL", "EXPERIENCE"],
        "Education": ["EDUCATION", "DEGREE", "FIELD", "GRAD_YEAR", "GPA"],
        "Other": []
    }

    for label in sorted(custom_labels):
        categorized = False
        for category, category_labels in label_groups.items():
            if label in category_labels:
                categorized = True
                break
        if not categorized:
            label_groups["Other"].append(label)

    for category, labels in label_groups.items():
        if labels:
            label_list = [f"{label}({label_counts.get(label, 0)})" for label in labels]
            print(f"   {category}: {', '.join(label_list)}")

    # Add your custom labels to the existing NER pipe
    ner = nlp.get_pipe("ner")
    print(f"\n🎯 Adding custom labels to existing NER...")

    for label in custom_labels:
        ner.add_label(label)

    print(f"   Total labels now: {len(ner.labels)}")

    # Prepare training examples
    print(f"\n📋 Preparing training examples...")
    valid_examples = []
    skipped = 0

    for text, annotations in quality_data:
        entities = annotations.get("entities", [])
        example = validate_example(nlp, text, entities)
        if example:
            valid_examples.append(example)
        else:
            skipped += 1

    print(f"   ✅ Valid examples: {len(valid_examples)}")
    print(f"   ❌ Skipped: {skipped}")

    if not valid_examples:
        print("❌ No valid training examples. Check your data format.")
        return

    # Fine-tune the model (fewer iterations since we have a good base)
    print(f"\n🚀 Starting hybrid training with {len(valid_examples)} examples...")

    # Get pipes to disable (keep only NER active)
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
    print(f"   🔇 Disabling pipes: {other_pipes}")

    # Training loop - fewer iterations since we're fine-tuning
    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.resume_training()

        # Reduced iterations for fine-tuning
        n_iter = 15  # less than from-scratch training

        for iteration in range(n_iter):
            print(f"\n   📈 Iteration {iteration + 1}/{n_iter}")

            # Initialize losses for this iteration
            losses = {}

            # Shuffle examples
            random.shuffle(valid_examples)

            # Process in batches
            batch_size = 8
            batches = [valid_examples[i:i + batch_size]
                       for i in range(0, len(valid_examples), batch_size)]

            successful_batches = 0

            for batch in batches:
                try:
                    # Lower dropout for fine-tuning
                    nlp.update(batch, drop=0.2, losses=losses)
                    successful_batches += 1
                except Exception as e:
                    print(f"      ⚠️  Batch failed: {str(e)[:50]}...")

            print(f"      ✅ Successful batches: {successful_batches}/{len(batches)}")

            # Print losses every few iterations
            if iteration % 3 == 0 or iteration == n_iter - 1:
                if losses:
                    print(f"      📊 Loss: {losses.get('ner', 'N/A'):.4f}")

    print("\n🎉 Hybrid training completed!")

    # Test the hybrid model
    print("\n🧪 Testing hybrid model:")
    test_sentences = [
        "John Smith is a Senior Software Engineer at Google with 5 years experience.",
        "Jane graduated from MIT with a Computer Science degree in 2020.",
        "Skills: Python, JavaScript, React, AWS, Docker, Kubernetes.",
        "Contact: john.doe@email.com | Phone: (555) 123-4567 | Boston, MA",
        "John Smith is a Senior Software Engineer at Google with Python and JavaScript skills.",
        "Jane Doe graduated from MIT with a Computer Science degree and knows Python, Java, and React.",
        "Skills: Python, JavaScript, React, AWS, Docker, Kubernetes, machine learning.",
        "Contact: john.doe@email.com | Phone: (555) 123-4567 | Location: Boston, MA",
        "Worked as a Software Developer at Microsoft from 2020 to 2023 building cloud applications."
    ]

    for sentence in test_sentences:
        doc = nlp(sentence)
        print(f"\n   📝 '{sentence}'")
        if doc.ents:
            for ent in doc.ents:
                entity_type = "CUSTOM" if ent.label_ in custom_labels else "PRETRAINED"
                print(f"      🎯 '{ent.text}' → {ent.label_} ({entity_type})")
        else:
            print("      ❌ No entities found")

    # Save the hybrid model
    output_dir = Path("output_hybrid")
    try:
        nlp.to_disk(output_dir)
        print(f"\n💾 Hybrid model saved to: {output_dir}/")

        # Save metadata
        metadata = {
            "model_type": "hybrid_pretrained_custom",
            "base_model": "en_core_web_sm",
            "custom_labels": list(custom_labels),
            "training_examples": len(valid_examples),
            "training_iterations": n_iter,
            "total_labels": len(ner.labels)
        }

        with open(output_dir / "training_info.json", "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"📊 Training metadata saved")

    except Exception as e:
        print(f"❌ Failed to save model: {e}")
        return

    # Update your API to use the hybrid model
    print(f"\n🔧 Next steps:")
    print(f"   1. Update your api.py to load from 'output_hybrid' instead of 'output'")
    print(f"   2. Restart your FastAPI server")
    print(f"   3. Test with the diagnostic tool")
    print(f"   4. The hybrid model should give much more consistent results!")

    print(f"\n✨ Benefits of hybrid approach:")
    print(f"   • Better entity boundaries from pre-trained model")
    print(f"   • General entities (PERSON, ORG) still work")
    print(f"   • Your custom resume labels added on top")
    print(f"   • More consistent extraction overall")

if __name__ == "__main__":
    main()