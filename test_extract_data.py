import os
import json

def extract_jsonl_chunk(
    input_file: str,
    output_file: str,
    extract_size_mb: float = 100,
    start_line: int = 0,
    validate_json: bool = True,
):
    """
    Extract ~100 MB of records from a large JSONL file.
    Always writes complete lines — no JSON object is ever cut mid-way.

    Args:
        input_file:      Path to the source .jsonl file
        output_file:     Path to save the extracted chunk
        extract_size_mb: Target size to extract in MB (default: 100)
        start_line:      Skip this many lines before starting (default: 0)
        validate_json:   If True, skip and warn on invalid JSON lines
    """
    MB = 1024 * 1024
    max_bytes = int(extract_size_mb * MB)

    file_size = os.path.getsize(input_file)
    print(f"Source file size : {file_size / MB:,.1f} MB")
    print(f"Target extract   : {extract_size_mb} MB")
    print(f"Starting at line : {start_line}")
    print(f"Output file      : {output_file}")
    print("-" * 45)

    written_bytes = 0
    written_lines = 0
    skipped_lines = 0
    invalid_lines = 0

    with open(input_file, "r", encoding="utf-8") as src, \
         open(output_file, "w", encoding="utf-8") as dst:

        for current_line_num, raw_line in enumerate(src):

            # Skip lines before start_line
            if current_line_num < start_line:
                skipped_lines += 1
                continue

            # Stop once we've hit our size target
            if written_bytes >= max_bytes:
                break

            line = raw_line.rstrip("\n")
            if not line:
                continue  # skip blank lines

            # Optionally validate each line is real JSON
            if validate_json:
                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    invalid_lines += 1
                    print(f"  [WARN] Invalid JSON at line {current_line_num + 1} — skipped")
                    continue

            encoded = (line + "\n").encode("utf-8")
            written_bytes += len(encoded)
            dst.write(line + "\n")
            written_lines += 1

    print(f"Lines written    : {written_lines:,}")
    print(f"Lines skipped    : {skipped_lines:,}")
    if invalid_lines:
        print(f"Invalid lines    : {invalid_lines:,}")
    print(f"Output size      : {written_bytes / MB:.2f} MB")
    print(f"Done! Saved to '{output_file}'")


# ── Example usage ──────────────────────────────────────────────────────────────
if __name__ == "__main__":

    # --- Extract first 100 MB (from the beginning) ---
    extract_jsonl_chunk(
        input_file      = "/Users/ravinderkumar/Downloads/arxiv.json",        # ← your 5 GB JSONL file
        output_file     = "extracted_100mb.json",
        extract_size_mb = 10,
        start_line      = 0,                       # start from the first line
        validate_json   = True,                    # set False to skip validation (faster)
    )

    # --- Extract a DIFFERENT 100 MB slice (e.g. skip first 50,000 lines) ---
    # extract_jsonl_chunk(
    #     input_file      = "big_data.jsonl",
    #     output_file     = "extracted_slice2.jsonl",
    #     extract_size_mb = 100,
    #     start_line      = 50000,
    # )