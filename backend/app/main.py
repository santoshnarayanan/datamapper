from fastapi import FastAPI,HTTPException
from app.api.routes import upload, workflow, dataprepare, mapping
from app.core.global_exception_handler import (
http_exception_handler, generic_exception_handler
)

app = FastAPI()

# register exception handler
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception,generic_exception_handler)

# register routes
app.include_router(upload.router)
app.include_router(workflow.router)
app.include_router(dataprepare.router)

app.include_router(mapping.router)
