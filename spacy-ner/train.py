import spacy
from spacy.training.example import Example
import random
import json
import warnings
from pathlib import Path

# Suppress alignment warnings for spaCy
warnings.filterwarnings("ignore", category=UserWarning, module="spacy")


# load_clean_training_data function:
def load_clean_training_data():
    """Load cleaned training data from multiple files"""
    training_files = [
        "train_data_contextual.json",
        "train_data_experience_refined.json",
        "train_data_address.json",
        "train_data_dataturks.json",
        "train_data_education_complex.json",
        "train_data_gpa.json",
        "train_data_skills_prose.json",
        "train_data_hr_analytics.json",
        "kaggle_prelabeled_20251004_163122.json",
        "train_data_skills.json",
        "train_data_contacts.json",
        "train_data_companies.json",
        "train_data_schools.json",
        "train_data_degrees.json",
        "train_data_experience.json",
        "train_data_fields.json",
        "train_data_grad_year.json",
        "train_data_augmented.json",
        "train_data_cleaned.json",
    ]

    all_training_data = []
    file_stats = {}  # Track examples per file

    for filename in training_files:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                training_data = json.load(f)
            print(f" Loaded {len(training_data)} examples from {filename}")
            all_training_data.extend(training_data)
            file_stats[filename] = len(training_data)

        except FileNotFoundError:
            print(f"️  {filename} not found, skipping")
            continue
        except Exception as e:
            print(f" Error loading {filename}: {e}")
            continue

    print(f" Total examples before simplification: {len(all_training_data)}")

    # Show breakdown by file
    print(" File breakdown:")
    for filename, count in file_stats.items():
        print(f"   {filename}: {count} examples")

    # Simplify labels for all combined data
    all_training_data = simplify_training_labels(all_training_data)
    print(f" Simplified to {len(all_training_data)} examples with core labels")

    return all_training_data

def filter_quality_examples(training_data, max_examples=200):
    """Filter and limit to highest quality examples"""
    if not training_data:
        return []

    quality_examples = []

    for text, annotations in training_data:
        entities = annotations.get("entities", [])
        if 1 <= len(entities) <= 25:
            quality_examples.append((text, annotations))

    # SHUFFLE before limiting to get diverse examples
    random.shuffle(quality_examples)

    # Limit total examples for efficiency
    if len(quality_examples) > max_examples:
        quality_examples = quality_examples[:max_examples]
        print(f"⚡ Limited to {max_examples} examples for efficient training")

    print(f" Using {len(quality_examples)} quality examples")
    return quality_examples


def validate_example(nlp, text, entities):
    """Validate a single training example"""
    try:
        doc = nlp.make_doc(text)
        example = Example.from_dict(doc, {"entities": entities})
        return example
    except Exception as e:
        print(f" Invalid example: {text[:30]}... - {str(e)[:50]}...")
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


def calculate_class_weights(training_data):
    """Calculate class weights based on entity frequency"""
    entity_counts = {}
    total_entities = 0

    for text, annotations in training_data:
        entities = annotations.get("entities", [])
        for start, end, label in entities:
            entity_counts[label] = entity_counts.get(label, 0) + 1
            total_entities += 1

    # Calculate weights: inverse frequency with smoothing
    class_weights = {}
    for label, count in entity_counts.items():
        # Inverse frequency with smoothing to avoid extreme weights
        weight = total_entities / (count + 1)  # +1 for smoothing
        # Cap weights to reasonable range (e.g., 1-10)
        class_weights[label] = min(max(weight, 1.0), 10.0)

    print(" Class weights:")
    for label, weight in sorted(class_weights.items(), key=lambda x: x[1], reverse=True):
        print(f"   {label}: {weight:.2f}x (count: {entity_counts[label]})")

    return class_weights

def enhance_minority_classes(training_data, target_min_count=10):
    """Oversample minority classes to balance the dataset"""
    # Count entities per class
    entity_counts = {}
    for text, annotations in training_data:
        entities = annotations.get("entities", [])
        for start, end, label in entities:
            entity_counts[label] = entity_counts.get(label, 0) + 1

    # Identify minority classes
    minority_classes = [label for label, count in entity_counts.items()
                        if count < target_min_count]

    if not minority_classes:
        return training_data

    print(f" Enhancing minority classes: {minority_classes}")

    enhanced_data = training_data.copy()

    # Oversample examples containing minority classes
    for text, annotations in training_data:
        entities = annotations.get("entities", [])
        has_minority = any(label in minority_classes for _, _, label in entities)

        if has_minority:
            # Add 2-3 extra copies of minority examples
            enhancement_factor = 3
            for _ in range(enhancement_factor):
                enhanced_data.append((text, annotations))

    print(f" Enhanced dataset: {len(training_data)} → {len(enhanced_data)} examples")
    return enhanced_data

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

def apply_class_weights_to_examples(examples, class_weights):
    """Apply class weights by duplicating examples with minority classes"""
    weighted_examples = []

    for example in examples:
        # Count how many minority classes are in this example
        minority_count = 0
        if hasattr(example, 'reference') and hasattr(example.reference, 'ents'):
            for ent in example.reference.ents:
                weight = class_weights.get(ent.label_, 1.0)
                if weight > 1.5:  # Only duplicate for significantly weighted classes
                    minority_count += 1

        # Add the example multiple times based on minority class count
        repetitions = max(1, minority_count)
        for _ in range(repetitions):
            weighted_examples.append(example)

    print(f" Weighted examples: {len(examples)} → {len(weighted_examples)}")
    return weighted_examples

def simplify_label(label: str) -> str:
    """
    Combines robust mapping for general labels with granular categorization for skills.
    """
    label = label.upper()

    # ranular logic for all skill-related labels
    if any(keyword in label for keyword in ["PROGRAMMING", "TECHNOLOGY", "PLATFORM", "FRAMEWORK", "TOOL"]):
        return "TECHNOLOGY"
    if any(keyword in label for keyword in ["SKILL", "INDUSTRY"]):
        return "HARD_SKILL"
    if "SOFT_SKILL" in label:
        return "SOFT_SKILL"

    core_mapping = {
        # Personal info
        'NAME': 'NAME', 'PERSON': 'NAME', 'FULL_NAME': 'NAME',
        'EMAIL': 'EMAIL', 'EMAIL_ADDRESS': 'EMAIL', 'CONTACT_EMAIL': 'EMAIL',
        'PHONE': 'PHONE', 'PHONE_NUMBER': 'PHONE', 'TELEPHONE': 'PHONE', 'MOBILE': 'PHONE',
        'LOCATION': 'LOCATION', 'ADDRESS': 'LOCATION', 'CITY': 'LOCATION', 'STATE': 'LOCATION',

        # Professional
        'TITLE': 'TITLE', 'JOB_TITLE': 'TITLE', 'POSITION': 'TITLE',
        'COMPANY': 'COMPANY', 'ORGANIZATION': 'COMPANY', 'ORG': 'COMPANY', 'EMPLOYER': 'COMPANY',
        'EXPERIENCE': 'EXPERIENCE', 'WORK_EXPERIENCE': 'EXPERIENCE',

        # Education
        'EDUCATION': 'EDUCATION', 'DEGREE': 'DEGREE', 'SCHOOL': 'SCHOOL',
        'UNIVERSITY': 'SCHOOL', 'COLLEGE': 'SCHOOL', 'GPA': 'GPA',
        'FIELD': 'EDUCATION',

        # Other
        'CERTIFICATION': 'CERTIFICATION',
        'PROJECT': 'PROJECT',
        'ACHIEVEMENT': 'ACHIEVEMENT',
        'DATE': 'DATE', 'GRAD_YEAR': 'DATE', 'YEAR': 'DATE',
        'LANGUAGE': 'LANGUAGE' # For spoken languages, not programming
    }

    # Return the mapped label, or the original label if not in the map
    return core_mapping.get(label, label)

def main():
    model_name = "en_core_web_lg"
    print(" HYBRID RESUME NER TRAINING")
    print("=" * 50)
    print("Using: en_core_web_lg + Your Custom Resume Labels")
    print("=" * 50)

    # Load the pre-trained English model (the hybrid foundation)
    try:
        nlp = spacy.load(model_name)
        print(" Loaded en_core_web_lg as base model")
        print(f"   Existing labels: {len(nlp.get_pipe('ner').labels)}")
    except OSError:
        print(" en_core_web_sm not found!")
        print("   Install it with: python -m spacy download en_core_web_sm")
        return

    # Load only your clean training data (skip Kaggle for now)
    training_data = load_clean_training_data()
    if not training_data:
        print(" No training data available. Exiting.")
        return

    # Filter to highest quality examples for efficient training
    quality_data = filter_quality_examples(training_data, max_examples=3000)

    # ENHANCE MINORITY CLASSES
    print("\n Enhancing minority classes...")
    enhanced_data = enhance_minority_classes(quality_data, target_min_count=10)
    # quality_data = filter_quality_examples(enhanced_data, max_examples=600)
    quality_data = enhanced_data

    # CALCULATE CLASS WEIGHTS - ADD THIS
    print("\n Calculating class weights...")
    class_weights = calculate_class_weights(quality_data)

    # Analyze labels
    custom_labels, label_counts = analyze_labels(quality_data)
    print(f"\n  Found {len(custom_labels)} custom resume labels:")

    # Group labels logically
    label_groups = {
        "Contact": ["NAME", "PHONE", "EMAIL", "LOCATION"],
        "Professional": ["TITLE", "COMPANY", "EXPERIENCE", "TECHNOLOGY", "HARD_SKILL"],
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
    print(f"\n Adding custom labels to existing NER...")

    for label in custom_labels:
        ner.add_label(label)

    print(f"   Total labels now: {len(ner.labels)}")

    # Prepare training examples
    print(f"\n Preparing training examples...")
    valid_examples = []
    skipped = 0

    for text, annotations in quality_data:
        entities = annotations.get("entities", [])
        example = validate_example(nlp, text, entities)
        if example:
            valid_examples.append(example)
        else:
            skipped += 1

    print(f"    Valid examples: {len(valid_examples)}")
    print(f"    Skipped: {skipped}")

    if not valid_examples:
        print(" No valid training examples. Check your data format.")
        return

    # Fine-tune the model (fewer iterations since we have a good base)
    print(f"\n Starting hybrid training with {len(valid_examples)} examples...")

    # Get pipes to disable (keep only NER active)
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
    print(f"    Disabling pipes: {other_pipes}")

    # Apply class weights by duplicating examples
    weighted_examples = apply_class_weights_to_examples(valid_examples, class_weights)

    # Training loop - fewer iterations since we're fine-tuning
    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.resume_training()

        # Reduced iterations for fine-tuning
        n_iter = 30

        for iteration in range(n_iter):
            print(f"\n   Iteration {iteration + 1}/{n_iter}")

            # Initialize losses for this iteration
            losses = {}

            # Shuffle examples
            random.shuffle(weighted_examples)  # Use weighted examples

            # Process in batches
            batch_size = 8
            batches = [weighted_examples[i:i + batch_size]  # Use weighted examples
                       for i in range(0, len(weighted_examples), batch_size)]

            successful_batches = 0

            for batch in batches:
                try:
                    # Use standard update
                    nlp.update(batch, drop=0.2, losses=losses, sgd=optimizer)
                    successful_batches += 1
                except Exception as e:
                    print(f"        Batch failed: {str(e)[:50]}...")

            print(f"       Successful batches: {successful_batches}/{len(batches)}")

            # Print losses every few iterations
            if iteration % 3 == 0 or iteration == n_iter - 1:
                if losses:
                    print(f"       Loss: {losses.get('ner', 'N/A'):.4f}")

    print("\n Hybrid training completed!")

    # Test the hybrid model
    print("\n Testing hybrid model:")
    test_sentences = [
        "John Smith is a Senior Software Engineer at Google with 5 years experience.",
        "Jane graduated from MIT with a Computer Science degree in 2020.",
        "Skills: Python, JavaScript, React, AWS, Docker, Kubernetes.",
        "Contact: john.doe@email.com | Phone: (555) 123-4567 | Boston, MA",
        "John Smith is a Senior Software Engineer at Google with Python and JavaScript skills.",
        "Jane Doe graduated from MIT with a Computer Science degree and knows Python, Java, and React.",
        "Skills: Python, JavaScript, React, AWS, Docker, Kubernetes, machine learning.",
        "Contact: john.doe@email.com | Phone: (555) 123-4567 | Location: Boston, MA",
        "Worked as a Software Developer at Microsoft from 2020 to 2023 building cloud applications.",

        # Healthcare
        "Maria Garcia, RN, BSN, has 8 years of experience in patient care at Alamosa Community Hospital.",
        "Seeking a registered nurse with a valid certification in pediatric advanced life support.",

        # Finance
        "David Chen is a Certified Public Accountant (CPA) specializing in forensic accounting.",
        "Financial Analyst proficient in financial modeling, Excel, and QuickBooks, graduated in 2021.",

        # Marketing
        "Emily White, a Marketing Manager at HubSpot, increased lead generation using Salesforce and SEO.",
        "Contact Emily at emily.w@email.com or (555) 888-9999 for opportunities in Denver, CO.",

        # Education & Administration
        "Michael Brown holds a Master of Education from University of Colorado and has been teaching since August 2015.",
        "Administrative assistant skilled in office management and executive support.",

        # Skilled Trades
        "Licensed Journeyman Electrician with expertise in commercial wiring and project management."
    ]

    for sentence in test_sentences:
        doc = nlp(sentence)
        print(f"\n    '{sentence}'")
        if doc.ents:
            for ent in doc.ents:
                entity_type = "CUSTOM" if ent.label_ in custom_labels else "PRETRAINED"
                print(f"       '{ent.text}' → {ent.label_} ({entity_type})")
        else:
            print("       No entities found")

    # Save the hybrid model
    output_dir = Path("output_hybrid")
    try:
        nlp.to_disk(output_dir)
        print(f"\n Hybrid model saved to: {output_dir}/")

        # Save metadata
        metadata = {
            "model_type": "hybrid_pretrained_custom",
            "base_model": model_name,
            "custom_labels": list(custom_labels),
            "training_examples": len(valid_examples),
            "training_iterations": n_iter,
            "total_labels": len(ner.labels)
        }

        with open(output_dir / "training_info.json", "w") as f:
            json.dump(metadata, f, indent=2)

        print(f" Training metadata saved")

    except Exception as e:
        print(f" Failed to save model: {e}")
        return

if __name__ == "__main__":
    main()