from fastapi import FastAPI
from app.api.routes import upload

app = FastAPI()

app.include_router(upload.router)
