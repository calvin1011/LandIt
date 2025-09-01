import pandas as pd
import spacy
import json
import os
from pathlib import Path
import re

def clean_resume_text(text):
    """Clean and preprocess resume text"""
    if pd.isna(text) or text == '':
        return None

    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', str(text))

    # Remove common OCR artifacts
    text = text.replace('|', 'I')
    text = text.replace('0', 'O')  # Only in specific contexts

    # Basic cleaning
    text = text.strip()

    # Filter out very short or very long resumes
    if len(text) < 100 or len(text) > 10000:
        return None

    return text


def prelabel_resume(nlp_model, resume_text):
    """Use existing spaCy model to predict entities in resume text"""
    try:
        doc = nlp_model(resume_text)

        entities = []
        for ent in doc.ents:
            # Basic quality filtering
            entity_text = ent.text.strip()

            # Skip very short entities (except for specific types)
            if len(entity_text) < 2 and ent.label_ not in ['GPA']:
                continue

            # Skip entities that are just punctuation or numbers
            if entity_text in ['', '.', ',', ';', ':', '-', '(', ')', '[', ']']:
                continue

            entities.append((ent.start_char, ent.end_char, ent.label_))

        return entities
    except Exception as e:
        print(f"Error processing resume: {e}")
        return []


def validate_entities(resume_text, entities, job_category=None):
    """Basic validation of predicted entities"""
    validated_entities = []

    for start, end, label in entities:
        # Check if indices are valid
        if start >= end or end > len(resume_text):
            continue

        entity_text = resume_text[start:end]

        # Basic validation rules
        if len(entity_text.strip()) == 0:
            continue

        # Category-based validation (if job category is available)
        if job_category and validate_entity_for_category(entity_text, label, job_category):
            validated_entities.append((start, end, label))
        elif not job_category:
            validated_entities.append((start, end, label))

    return validated_entities


def validate_entity_for_category(entity_text, label, category):
    """Validate if entity makes sense for the job category"""
    # Simple validation - you can expand this
    tech_categories = ['Data Science', 'Web Development', 'Java Developer',
                       'Python Developer', 'DevOps Engineer', 'Database']

    if category in tech_categories:
        # Tech roles should have tech skills
        if label == 'SKILL' and any(tech in entity_text.lower() for tech in
                                    ['python', 'java', 'javascript', 'sql', 'aws', 'docker']):
            return True

    # Default: accept all entities (conservative approach)
    return True


def main():
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    csv_path = project_root / "data" / "kaggle" / "raw" / "UpdatedResumeDataSet.csv"
    model_path = script_dir.parent / "output"
    output_path = project_root / "data" / "kaggle" / "processed" / "kaggle_prelabeled.json"

    print(f"Loading CSV from: {csv_path}")
    print(f"Loading model from: {model_path}")
    print(f"Output will be saved to: {output_path}")

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load your trained spaCy model
    try:
        nlp = spacy.load(str(model_path))
        print("✅ Successfully loaded your trained spaCy model")
    except Exception as e:
        print(f"❌ Error loading spaCy model: {e}")
        print("Make sure your model is trained and saved in spacy-ner/output/")
        return

    # Load the Kaggle dataset
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ Successfully loaded CSV with {len(df)} rows")
        print(f"Columns: {list(df.columns)}")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return

    # Inspect the data structure
    print(f"\nFirst few column names: {list(df.columns)[:5]}")
    if len(df) > 0:
        print(f"Sample data types: {df.dtypes.head()}")

    # Try to identify the resume text column (common names)
    resume_column = None
    category_column = None

    possible_resume_cols = ['Resume', 'Resume_str', 'resume_text', 'text', 'content']
    possible_category_cols = ['Category', 'Job_Category', 'category', 'job_category']

    for col in df.columns:
        if col in possible_resume_cols or 'resume' in col.lower():
            resume_column = col
            break

    for col in df.columns:
        if col in possible_category_cols or 'category' in col.lower():
            category_column = col
            break

    if not resume_column:
        print("❌ Could not find resume text column. Available columns:")
        for i, col in enumerate(df.columns):
            print(f"  {i}: {col}")
        choice = input("Enter the number of the column containing resume text: ")
        try:
            resume_column = df.columns[int(choice)]
        except:
            print("Invalid choice. Exiting.")
            return

    print(f"Using '{resume_column}' as resume text column")
    if category_column:
        print(f"Using '{category_column}' as category column")

    # Process the resumes
    training_data = []
    successful_count = 0
    failed_count = 0

    print(f"\n🔄 Processing {len(df)} resumes...")

    for index, row in df.iterrows():
        if index % 100 == 0:
            print(f"Processed {index}/{len(df)} resumes...")

        # Get resume text
        resume_text = row[resume_column]
        category = row[category_column] if category_column else None

        # Clean the text
        cleaned_text = clean_resume_text(resume_text)
        if not cleaned_text:
            failed_count += 1
            continue

        # Get entity predictions from your model
        entities = prelabel_resume(nlp, cleaned_text)

        # Validate entities
        validated_entities = validate_entities(cleaned_text, entities, category)

        # Only keep examples with reasonable number of entities
        if 5 <= len(validated_entities) <= 100:  # Reasonable range
            training_example = (cleaned_text, {"entities": validated_entities})
            training_data.append(training_example)
            successful_count += 1
        else:
            failed_count += 1

    print(f"\n✅ Processing complete!")
    print(f"Successfully processed: {successful_count} resumes")
    print(f"Failed/filtered out: {failed_count} resumes")

    if successful_count == 0:
        print("❌ No training data generated. Check your data and model.")
        return

    # Save the pre-labeled training data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved pre-labeled training data to: {output_path}")

    # Print some statistics
    entity_counts = {}
    for text, annotations in training_data:
        for start, end, label in annotations['entities']:
            entity_counts[label] = entity_counts.get(label, 0) + 1

    print(f"\n📊 Entity distribution in pre-labeled data:")
    for label, count in sorted(entity_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {label}: {count}")

    # Show a few examples
    print(f"\n🔍 Sample pre-labeled examples:")
    for i in range(min(3, len(training_data))):
        text, annotations = training_data[i]
        print(f"\nExample {i + 1}:")
        print(f"Text (first 100 chars): {text[:100]}...")
        print(f"Entities found: {len(annotations['entities'])}")
        for start, end, label in annotations['entities'][:5]:  # Show first 5 entities
            entity_text = text[start:end]
            print(f"  {label}: '{entity_text}'")


if __name__ == "__main__":
    main()