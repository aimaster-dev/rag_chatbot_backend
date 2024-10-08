from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
import re

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
model = SentenceTransformer('all-MiniLM-L6-v2')

def split_into_paragraph(text):
    return [p.strip() for p in text.split('\n') if p.strip()]

def create_index(collection_id):
    index_name = f"collection-{collection_id}"
    try:
        pc.create_index(
            name = index_name,
            dimension=384,
            metric="cosine",
            spec = ServerlessSpec(
                cloud = "aws",
                region="us-east-1"
            )
        )
        print(f"Created Pinecone index for collection: {collection_id}")
    except Exception  as e:
        print(f"An unexpected error occurred while creating the index for collection {collection_id}: {e}")

def delete_index(collection_id):
    index_name = f"collection-{collection_id}"
    try:
        pc.delete_index(index_name)
        print(f"Collection {collection_id} successfully deleted")
    except Exception as e:
        print(f"An unexpected error occurred while deleting the index for collection {collection_id}: {e}")

def index_document(document):
    paragraphs = split_into_paragraph(document.content)
    embeddings = model.encode(paragraphs)
    index_name = f"collection-{document.collection_id}"
    index = pc.Index(index_name)
    vectors = [{"id": f"paragraph-{i}", "values": embeddings[i].tolist(), "metadata": {"text": paragraphs[i]}} for i in range(len(paragraphs))]
    # print(vectors)
    index.upsert(
        vectors=vectors,
        namespace=f"document-{document.id}"
    )

def update_document(document):
    index_name = f"collection-{document.collection_id}"
    index = pc.Index(index_name)
    index.delete(delete_all=True, namespace=f"document-{document.id}")
    index_document(document)
    print(f"Updated document {document.id} vectors in Pinecone.")

def delete_document(document):
    index_name = f"collection-{document.collection_id}"
    index = pc.Index(index_name)
    index.delete(delete_all=True, namespace=f"document-{document.id}")
    print(f"Document {document.id} vectors in Pinecone is deleted.")

async def search_documents(CollectionList: list, query: str, threshold: float = 0.25 ):
    query_embedding = model.encode(query).tolist()
    # print(query_embedding)
    results = []
    assos_paragraph = []
    for collection_id in CollectionList:
        index_name = f"collection-{collection_id}"
        print(collection_id)
        index = pc.Index(index_name)
        namespaces = list(index.describe_index_stats().get("namespaces", {}).keys())
        for namespace in namespaces:
            print(namespace)
            mid_res = index.query(
                namespace=namespace,
                vector=query_embedding,
                top_k=5,
                include_metadata=True,
            )
            print(mid_res)
            document_id = int(re.findall(r'\d+', namespace)[0])
            results.extend([{"collection_id": collection_id, "document_id": document_id, "match": match} for match in mid_res["matches"] if match["score"] >= threshold])
    # print(results)
    return results