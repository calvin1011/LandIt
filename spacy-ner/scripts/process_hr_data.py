import pandas as pd
import json
import random

def create_training_data_from_hr_analytics(input_file, output_file, num_examples=500):
    """Converts the HR Analytics CSV into spaCy training data."""
    df = pd.read_csv(input_file)

    # Drop rows with missing values in key columns
    df.dropna(subset=['education_level', 'major_discipline', 'experience', 'company_type'], inplace=True)

    training_data = []

    # Take a random sample to keep the data balanced
    if len(df) > num_examples:
        df = df.sample(n=num_examples, random_state=42)

    for _, row in df.iterrows():
        text_parts = []
        entities = []

        # Education
        if pd.notna(row['education_level']) and pd.notna(row['major_discipline']):
            education = str(row['education_level'])
            major = str(row['major_discipline'])
            sentence = f"Education: {education} in {major}."

            start_offset = len(text_parts)
            entities.append((start_offset + len("Education: "), start_offset + len("Education: ") + len(education), 'DEGREE'))
            entities.append((start_offset + len(f"Education: {education} in "), start_offset + len(f"Education: {education} in ") + len(major), 'EDUCATION'))
            text_parts.append(sentence)

        # Experience
        if pd.notna(row['experience']):
            experience = str(row['experience'])
            sentence = f"Has {experience} years of experience."

            start_offset = len("".join(text_parts)) + len(text_parts) # account for spaces
            entities.append((start_offset + len("Has "), start_offset + len("Has ") + len(experience), 'EXPERIENCE'))
            text_parts.append(sentence)

        # Company
        if pd.notna(row['company_type']) and pd.notna(row['company_size']):
            company_type = str(row['company_type'])
            company_size = str(row['company_size'])
            sentence = f"Worked at a {company_type} company with {company_size} employees."

            start_offset = len("".join(text_parts)) + len(text_parts) # account for spaces
            entities.append((start_offset + len("Worked at a "), start_offset + len("Worked at a ") + len(company_type), 'COMPANY'))
            text_parts.append(sentence)

        # Combine into a single text block
        full_text = " ".join(text_parts)

        if full_text and entities:
            training_data.append([full_text, {'entities': entities}])

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, indent=2)

    print(f"Successfully created {len(training_data)} examples from HR Analytics data.")

if __name__ == "__main__":
    # Make sure 'aug_train.csv' is in the same directory as this script
    input_csv_path = "aug_train.csv"
    # This will save the output file to the main spacy-ner directory
    output_json_path = "../train_data_hr_analytics.json"

    create_training_data_from_hr_analytics(input_csv_path, output_json_path)