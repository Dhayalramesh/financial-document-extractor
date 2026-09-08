"""Simple evaluation harness — compares extraction output against a
labeled ground-truth set. Field-level accuracy = your resume number.
"""

import json
from pathlib import Path
from app.pdf_parser import extract_text_from_pdf
from app.extractor import extract_earnings_data


def run_eval(labeled_samples_path: str = "sample_docs/labels.json"):
    """labels.json format:
    [
      {"pdf_path": "sample_docs/company1.pdf", "expected": {"ticker": "TCS", "eps": "...", ...}}
    ]
    """
    labels_file = Path(labeled_samples_path)
    if not labels_file.exists():
        print(f"No labels file found at {labeled_samples_path} — skipping eval.")
        return

    samples = json.loads(labels_file.read_text())
    total_fields = 0
    correct_fields = 0

    for sample in samples:
        pdf_path = Path(sample["pdf_path"])
        expected = sample["expected"]

        file_bytes = pdf_path.read_bytes()
        text = extract_text_from_pdf(file_bytes)
        result = extract_earnings_data(text, pdf_path.name)
        extracted_dict = result.extracted.model_dump()

        for field, expected_value in expected.items():
            total_fields += 1
            actual_value = extracted_dict.get(field)
            if str(actual_value).strip().lower() == str(expected_value).strip().lower():
                correct_fields += 1
            else:
                print(f"[{pdf_path.name}] {field}: expected={expected_value!r} got={actual_value!r}")

    accuracy = (correct_fields / total_fields * 100) if total_fields else 0
    print(f"\nField-level accuracy: {accuracy:.1f}% ({correct_fields}/{total_fields})")
    return accuracy


if __name__ == "__main__":
    run_eval()