from fastapi import FastAPI
from app.api.routes import upload, workflow

app = FastAPI()

app.include_router(upload.router)
app.include_router(workflow.router)
