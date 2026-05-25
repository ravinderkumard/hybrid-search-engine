import json

with open("data/evaluation_dataset.json", "r") as f:
    evaluation_data = json.load(f)

print(evaluation_data[0])