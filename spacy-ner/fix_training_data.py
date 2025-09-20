
import json
import re
from typing import List, Tuple, Dict

def clean_training_data(filename: str) -> List:
    """Clean training data to fix overlapping entities and reduce labels"""

    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cleaned_data = []
    problematic_count = 0

    for text, annotations in data:
        entities = annotations.get("entities", [])

        # Sort entities by start position
        entities.sort(key=lambda x: x[0])

        # Check for and fix overlapping entities
        cleaned_entities = []
        prev_end = -1

        for start, end, label in entities:
            # Skip if this entity overlaps with previous
            if start < prev_end:
                problematic_count += 1
                continue

            # Simplify labels - map to core categories
            simplified_label = simplify_label(label)

            cleaned_entities.append([start, end, simplified_label])
            prev_end = end

        if cleaned_entities:
            cleaned_data.append([text, {"entities": cleaned_entities}])

    print(f"Fixed {problematic_count} overlapping entities")
    print(f"Reduced from {len(data)} to {len(cleaned_data)} clean examples")

    return cleaned_data


def simplify_label(label: str) -> str:
    """Simplify excessive label categories to core resume labels"""
    label = label.upper()

    # Core resume labels to keep
    core_labels = {
        'NAME', 'EMAIL', 'PHONE', 'LOCATION', 'TITLE', 'COMPANY',
        'SKILL', 'EDUCATION', 'DEGREE', 'SCHOOL', 'DATE', 'EXPERIENCE',
        'CERTIFICATION', 'PROJECT', 'ACHIEVEMENT', 'LANGUAGE'
    }

    # Mapping of complex labels to simple ones
    label_mapping = {
        'ACADEMIC_METRIC': 'ACHIEVEMENT',
        'BUSINESS_TYPE': 'COMPANY',
        'CERTIFICATION_LEVEL': 'CERTIFICATION',
        'CITIZENSHIP_STATUS': 'LOCATION',
        'COMPANY_TYPE': 'COMPANY',
        'DURATION': 'DATE',
        'EXPERIENCE_DURATION': 'EXPERIENCE',
        'FIELD': 'SKILL',
        'GRAD_YEAR': 'DATE',
        'INDUSTRY': 'SKILL',
        'LANGUAGE_SKILL': 'LANGUAGE',
        'METHODOLOGY': 'SKILL',
        'PLATFORM': 'SKILL',
        'PROFICIENCY_LEVEL': 'SKILL',
        'PROGRAMMING_LANGUAGE': 'SKILL',
        'SPECIALIZATION': 'SKILL',
        'TECHNICAL_SKILL': 'SKILL',
        'TECHNOLOGY': 'SKILL',
        'TIME_PERIOD': 'DATE',
        'YEAR': 'DATE'
    }

    if label in core_labels:
        return label
    elif label in label_mapping:
        return label_mapping[label]
    else:
        # Default to SKILL for technical terms, OTHER for everything else
        if any(keyword in label for keyword in ['TECH', 'SKILL', 'LANG', 'PROG']):
            return 'SKILL'
        else:
            return 'OTHER'


def save_cleaned_data(cleaned_data: List, output_filename: str):
    """Save cleaned training data"""
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    cleaned = clean_training_data("train_data.json")
    save_cleaned_data(cleaned, "train_data_cleaned.json")
    print("✅ Cleaned training data saved to train_data_cleaned.json")