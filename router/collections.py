from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models import Collection, User, Document
from database import get_db
from auth import get_current_user
from pydantic import BaseModel
from datetime import datetime
from service.pinecone_service import create_index, delete_index, index_document, update_document, delete_document

class CreateCollectionRequest(BaseModel):
    name: str
    description: str = None

class UpdateCollectionRequest(BaseModel):
    collection_id: int
    name: str
    description: str = None

class CreateDocumentRequest(BaseModel):
    title: str
    content:  str

class UpdateDocumentRequest(BaseModel):
    document_id: int
    title: str
    content: str

router = APIRouter(prefix="/collections")

@router.post("/create")
def create_collection(request: CreateCollectionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        collection = Collection(name=request.name, 
                                description = request.description, 
                                user_id=current_user.id
                                )
        db.add(collection)
        db.commit()
        db.refresh(collection)
        create_index(collection.id)
        return collection
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occured: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.post("/update")
def updating_document(request: UpdateCollectionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    collection = db.query(Collection).filter(Collection.id == request.collection_id, Collection.user_id == current_user.id).first()
    if not collection:
        raise HTTPException(status_code=403, detail="Unauthorized access to collection")
    collection.name = request.name
    collection.description = request.description
    db.commit()
    db.refresh(collection)
    return collection

@router.get("/getall")
def get_collections(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        collections = db.query(Collection).filter(Collection.user_id == current_user.id).all()
        collections.reverse()
        return collections
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
    except Exception as e:
        print("#################")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
    
@router.post("/{collection_id}")
def delete_collection(collection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    collection = db.query(Collection).filter(Collection.id == collection_id, Collection.user_id == current_user.id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    db.delete(collection)
    db.commit()
    delete_index(collection_id)
    return {"message": "Collection deleted"}

@router.post("/{collection_id}/documents/create")
def create_document(request: CreateDocumentRequest, collection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    collection = db.query(Collection).filter(Collection.id == collection_id, Collection.user_id == current_user.id).first()
    if not collection:
        raise HTTPException(status_code=403, detail="Unauthorized access to collection")
    blank_doc = db.query(Document).filter(Document.content == "UNTITLED", Document.collection_id == collection_id).all()
    if len(blank_doc) != 0:
        raise HTTPException(status_code=422, detail="The blank document is already existed in this collection.")
    document = Document(title=request.title, content=request.content, collection_id=collection_id)
    db.add(document)
    db.commit()
    db.refresh(document)
    index_document(document)
    return document

@router.post("/{collection_id}/documents/update")
def updating_document(collection_id: int, request: UpdateDocumentRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    collection = db.query(Collection).filter(Collection.id == collection_id, Collection.user_id == current_user.id).first()
    if not collection:
        raise HTTPException(status_code=403, detail="Unauthorized access to collection")
    document = db.query(Document).filter(Document.id == request.document_id, Document.collection_id == collection_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    document.title = request.title
    document.content = request.content
    db.commit()
    db.refresh(document)
    update_document(document)
    return document

@router.get("/{collection_id}/documents/get")
def gettinging_document(collection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    collection = db.query(Collection).filter(Collection.id == collection_id, Collection.user_id == current_user.id).first()
    if not collection:
        raise HTTPException(status_code=403, detail="Unauthorized access to collection")
    documents = db.query(Document).filter(Document.collection_id == collection_id).all()
    documents.reverse()
    return documents

@router.get("/{collection_id}/documents/get/{document_id}")
def gettinging_document(collection_id: int, document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    collection = db.query(Collection).filter(Collection.id == collection_id, Collection.user_id == current_user.id).first()
    if not collection:
        raise HTTPException(status_code=403, detail="Unauthorized access to collection")
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document

@router.post("/{collection_id}/documents/{document_id}/delete")
def deleting_document(collection_id: int, document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    collection = db.query(Collection).filter(Collection.id == collection_id, Collection.user_id == current_user.id).first()
    if not collection:
        raise HTTPException(status_code=403, detail="Unauthorized access to collection")
    document = db.query(Document).filter(Document.id == document_id, Document.collection_id == collection_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    db.delete(document)
    db.commit()
    delete_document(document)
    return document