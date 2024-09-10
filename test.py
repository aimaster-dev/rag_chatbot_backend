from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def split_into_paragraph(text):
    return [p.strip() for p in text.split('\n') if p.strip()]

def index_document(str):
    paragraphs = split_into_paragraph(str)
    embeddings = model.encode(paragraphs)
    vectors = [(f"{1}-{i}", embeddings[i].tolist(), {"document_id": 1, "paragraph_index": i}) for i in range(len(paragraphs))]
    print(vectors[0])

docstr = "I am a student.\n I am going to work with you."

index_document(docstr)