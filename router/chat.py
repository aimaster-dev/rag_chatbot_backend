from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from service.chatbot_service import generate_response
from service.pinecone_service import search_documents
from dotenv import load_dotenv
from models import User, History, Collection
from datetime import datetime
import os

load_dotenv()

class ChatRequest(BaseModel):
    query: str
    collection_ids: list[int]

router = APIRouter(prefix="/chat")

@router.post("/query")
async def chat_with_bot(request: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = request.query
    collection_ids = request.collection_ids
    if 0 in collection_ids:
        collections = db.query(Collection).filter(Collection.user_id == current_user.id).all()
        collection_ids = []
        for collection in collections:
            collection_ids.append(collection.id)
        print(collection_ids)
    documents = await search_documents(CollectionList = collection_ids, query=query)
    response = ""
    candidate_paragraphs = []
    if len(documents) == 0:
        response = os.getenv("DEFAULT_ANSWER")
    else:
        for doc in documents:
            candidate_paragraphs.append({"collection_id": doc["collection_id"], "document_id": doc["document_id"], "paragraph": doc["match"]["metadata"]["text"]})
        response = await generate_response(query, documents)

    chat_history = History(
        user_id = current_user.id,
        query = query,
        collection_ids = collection_ids,
        bot_response = response
    )
    db.add(chat_history)
    db.commit()
    return {"user": query, "answer": response, "source_data": candidate_paragraphs}


@router.get("/history")
def chat_with_bot(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    history = db.query(History).filter(History.user_id == current_user.id).all()
    return [
        {
            "query": record.query,
            "collections": [collection_id for collection_id in record.collection_ids],
            "bot_response": record.bot_response,
            "created_at": record.created_at
        }
        for record in history
    ]