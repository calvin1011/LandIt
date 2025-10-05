import json

def convert_dataturks_to_spacy(input_file, output_file):
    """Converts Dataturks JSON to spaCy training format."""
    training_data = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            text = data['content']
            entities = []
            for annotation in data['annotation']:
                points = annotation['points'][0]
                labels = annotation['label']
                if not isinstance(labels, list):
                    labels = [labels]

                for label in labels:
                    entities.append((points['start'], points['end'] + 1, label.upper()))

            training_data.append([text, {'entities': entities}])

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, indent=2)

    print(f"Successfully converted {len(training_data)} examples.")

if __name__ == "__main__":
    input_path = "Entity Recognition in Resumes.json"
    output_path = "../train_data_dataturks.json" # Saves to the spacy-ner directory
    convert_dataturks_to_spacy(input_path, output_path)