from app.services.data_loader import load_documents

docs = load_documents()
print(docs[:2])