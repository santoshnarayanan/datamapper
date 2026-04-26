from fastapi import FastAPI
from app.api.routes import upload, workflow, dataprepare, mapping

app = FastAPI()


app.include_router(upload.router)
app.include_router(workflow.router)
app.include_router(dataprepare.router)

app.include_router(mapping.router)
