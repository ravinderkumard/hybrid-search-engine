import json

INPUT_FILE = "/Users/ravinderkumar/Downloads/arxiv.json"
OUTPUT_FILE = "/Users/ravinderkumar/Downloads/arxiv.jsonl"

decoder = json.JSONDecoder()

buffer = ""

with open(INPUT_FILE, "r", encoding="utf-8") as f, \
     open(OUTPUT_FILE, "w", encoding="utf-8") as out:

    while chunk := f.read(8192):

        buffer += chunk

        while buffer:

            buffer = buffer.lstrip()

            try:
                obj, index = decoder.raw_decode(buffer)

                out.write(
                    json.dumps(obj)
                )

                out.write("\n")

                buffer = buffer[index:]

            except json.JSONDecodeError:
                break

print("Normalization complete")