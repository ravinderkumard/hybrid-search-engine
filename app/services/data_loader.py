import json

def load_documents(path="data/documents.json"):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)