import json

INPUT_FILE = "/Users/ravinderkumar/Downloads/arxiv.json"
OUTPUT_FILE = "arxiv_sample.jsonl"

LIMIT = 100


def write_jsonl(records, output_file):
    with open(output_file, "w", encoding="utf-8") as out:
        for record in records:
            out.write(json.dumps(record) + "\n")


def extract_from_json_array():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    sample = data[:LIMIT]

    write_jsonl(sample, OUTPUT_FILE)

    print(f"Extracted {len(sample)} records")


if __name__ == "__main__":
    extract_from_json_array()