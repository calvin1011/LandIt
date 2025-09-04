#!/usr/bin/env python3
"""
Resume Processing Diagnostic Tool
Run this to test your resume processing pipeline and identify issues
"""

import requests
import json
import time
from pathlib import Path

# Test data - mix of clean and messy resume text
TEST_CASES = [
    {
        "name": "Clean Resume",
        "text": "John Smith is a Senior Software Engineer at Google with 5 years of experience. He graduated from MIT with a Computer Science degree in 2020. Skills include Python, JavaScript, React, and AWS. Contact: john.smith@gmail.com or (555) 123-4567.",
        "expected_entities": ["John Smith", "Senior Software Engineer", "Google", "5 years", "MIT", "Computer Science",
                              "2020", "Python", "JavaScript", "React", "AWS", "john.smith@gmail.com", "(555) 123-4567"]
    },
    {
        "name": "Messy OCR Resume",
        "text": "JaneWilson DataScientist@Microsoft|Education:StanfordUniversity2019|Skills:Python,R,SQL,MachineLearning|Email:jane.wilson@hotmail.com|Phone:555.987.6543|Experience:5years",
        "expected_entities": ["Jane Wilson", "Data Scientist", "Microsoft", "Stanford University", "2019", "Python",
                              "R", "SQL", "Machine Learning", "jane.wilson@hotmail.com", "555.987.6543", "5 years"]
    },
    {
        "name": "Real-world Messy Resume",
        "text": """MichaelBrown
SeniorProductManager
EXPERIENCE
ProductManager|Apple|2020-2023
Ledacross-functionalteamof15engineers
LaunchednewiOSfeatureswith>1Musers
Increasedretentionby23%throughdataanalysis
EDUCATION
MBA|HarvardBusinessSchool|2020
BS ComputerScience|Berkeley|2018
SKILLS
ProductStrategy,DataAnalysis,A/BTesting,SQL,Python
CONTACT
michael.brown@icloud.com|(650)555-0123""",
        "expected_entities": ["Michael Brown", "Senior Product Manager", "Product Manager", "Apple", "2020-2023", "iOS",
                              "MBA", "Harvard Business School", "2020", "BS Computer Science", "Berkeley", "2018",
                              "Product Strategy", "Data Analysis", "A/B Testing", "SQL", "Python",
                              "michael.brown@icloud.com", "(650)555-0123"]
    }
]

API_BASE_URL = "http://127.0.0.1:8000"


def test_api_connection():
    """Test if the spaCy API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ spaCy API is running")
            print(f"   Version: {response.json().get('version', 'unknown')}")
            print(f"   Labels: {len(response.json().get('model_labels', []))}")
            return True
        else:
            print(f"❌ spaCy API returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to spaCy API: {e}")
        print("   Make sure your FastAPI server is running on port 8000")
        return False


def test_model_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("🔍 Model Health Check:")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Model loaded: {health_data.get('model_loaded')}")
            print(f"   Labels count: {health_data.get('labels_count')}")
            return health_data.get('model_loaded', False)
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_single_case(test_case):
    """Test a single resume case"""
    print(f"\n{'=' * 60}")
    print(f"Testing: {test_case['name']}")
    print(f"{'=' * 60}")

    # Show input text
    text = test_case['text']
    print(f"Input text ({len(text)} chars):")
    print(f"  {text[:100]}{'...' if len(text) > 100 else ''}")

    try:
        # Test the main parse endpoint
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/parse-resume",
            json={"text": text},
            timeout=30
        )
        processing_time = time.time() - start_time

        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

        result = response.json()
        entities = result.get('entities', [])
        stats = result.get('processing_stats', {})

        print(f"\n📊 Processing Results:")
        print(f"   Processing time: {processing_time:.2f}s")
        print(f"   Raw entities found: {stats.get('total_entities_found', 'unknown')}")
        print(f"   After filtering: {len(entities)}")
        print(f"   Filter ratio: {stats.get('filter_ratio', 'unknown')}")
        print(f"   Average confidence: {stats.get('average_confidence', 'unknown')}")

        # Show extracted entities by type
        entities_by_type = {}
        for entity in entities:
            label = entity['label']
            if label not in entities_by_type:
                entities_by_type[label] = []
            entities_by_type[label].append(entity)

        print(f"\n🎯 Extracted Entities ({len(entities)} total):")
        for label, label_entities in sorted(entities_by_type.items()):
            print(f"   {label}: {len(label_entities)} entities")
            for entity in label_entities[:3]:  # Show first 3 of each type
                confidence = entity.get('confidence', 0) * 100
                print(f"     • '{entity['text']}' ({confidence:.0f}%)")
            if len(label_entities) > 3:
                print(f"     ... and {len(label_entities) - 3} more")

        # Compare with expected entities (basic check)
        expected = test_case.get('expected_entities', [])
        if expected:
            extracted_texts = [e['text'].lower() for e in entities]
            found_count = 0
            missing = []

            for expected_entity in expected:
                if any(expected_entity.lower() in extracted.lower() or
                       extracted.lower() in expected_entity.lower()
                       for extracted in extracted_texts):
                    found_count += 1
                else:
                    missing.append(expected_entity)

            coverage = (found_count / len(expected)) * 100 if expected else 0
            print(f"\n📈 Coverage Analysis:")
            print(f"   Expected entities: {len(expected)}")
            print(f"   Found: {found_count}")
            print(f"   Coverage: {coverage:.1f}%")

            if missing:
                print(f"   Missing: {missing[:5]}")  # Show first 5 missing
                if len(missing) > 5:
                    print(f"   ... and {len(missing) - 5} more")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_raw_model_output(text):
    """Test the raw model output endpoint"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/test-model",
            json={"text": text},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\n🔧 Raw Model Output:")
            print(f"   Text preview: {result.get('text_preview', 'N/A')}")
            print(f"   Raw entities: {len(result.get('raw_entities', []))}")

            # Show entity breakdown
            raw_entities = result.get('raw_entities', [])
            if raw_entities:
                entity_types = {}
                for entity in raw_entities:
                    label = entity['label']
                    if label not in entity_types:
                        entity_types[label] = []
                    entity_types[label].append(entity)

                for label, entities in entity_types.items():
                    avg_conf = sum(e.get('confidence', 0) for e in entities) / len(entities)
                    print(f"   {label}: {len(entities)} entities (avg conf: {avg_conf:.2f})")

            return True
        else:
            print(f"❌ Raw model test failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Raw model test error: {e}")
        return False


def run_comprehensive_test():
    """Run all diagnostic tests"""
    print("🚀 Resume Processing Diagnostic Tool")
    print("=" * 60)

    # Test API connection
    if not test_api_connection():
        print("\n❌ Cannot proceed - API is not accessible")
        return

    # Test model health
    if not test_model_health():
        print("\n⚠️ Model health check failed - results may be unreliable")

    # Run test cases
    passed = 0
    total = len(TEST_CASES)

    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n📋 Test Case {i}/{total}")
        if test_single_case(test_case):
            passed += 1

            # Test raw model output for first case
            if i == 1:
                test_raw_model_output(test_case['text'])

    # Summary
    print(f"\n{'=' * 60}")
    print(f"📊 TEST SUMMARY")
    print(f"{'=' * 60}")
    print(f"Passed: {passed}/{total}")
    print(f"Success rate: {(passed / total) * 100:.1f}%")

    if passed == total:
        print("✅ All tests passed! Your resume processing pipeline is working well.")
    elif passed > 0:
        print("⚠️ Some tests passed. Check the failed cases for issues.")
        print("\n🔍 Common issues and solutions:")
        print("• Low entity counts: Check text preprocessing")
        print("• Missing expected entities: Review training data")
        print("• Low confidence scores: Model may need more training")
        print("• API errors: Check spaCy model loading")
    else:
        print("❌ All tests failed. Check your setup:")
        print("• Is the spaCy API running?")
        print("• Is your model properly loaded?")
        print("• Are there errors in the API logs?")


def test_custom_text():
    """Allow testing custom resume text"""
    print("\n" + "=" * 60)
    print("🔬 CUSTOM TEXT TESTING")
    print("=" * 60)
    print("Paste your resume text below (press Enter twice to finish):")

    lines = []
    empty_count = 0

    while empty_count < 2:
        try:
            line = input()
            if line.strip() == "":
                empty_count += 1
            else:
                empty_count = 0
            lines.append(line)
        except KeyboardInterrupt:
            break

    custom_text = "\n".join(lines).strip()

    if custom_text:
        custom_case = {
            "name": "Custom Resume Text",
            "text": custom_text,
            "expected_entities": []  # No expectations for custom text
        }
        test_single_case(custom_case)
        test_raw_model_output(custom_text)
    else:
        print("No text provided.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--custom":
        test_custom_text()
    else:
        run_comprehensive_test()

        # Ask if user wants to test custom text
        try:
            response = input("\n❓ Would you like to test custom resume text? (y/n): ")
            if response.lower().startswith('y'):
                test_custom_text()
        except KeyboardInterrupt:
            print("\nGoodbye!")