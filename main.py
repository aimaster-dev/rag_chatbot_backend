from fastapi import FastAPI
from database import Base, engine
from auth import auth_router
from router import collections, chat
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost", 
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specify which origins are allowed to make requests
    allow_credentials=True,  # Allow sending cookies (for authentication)
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(auth_router)
app.include_router(collections.router)
app.include_router(chat.router)