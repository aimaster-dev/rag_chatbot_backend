from fastapi import FastAPI
from database import Base, engine
from auth import auth_router
from router import collections

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth_router)
app.include_router(collections.router)