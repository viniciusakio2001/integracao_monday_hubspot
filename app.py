from fastapi import FastAPI
from routes.monday import router as monday_router

app = FastAPI()

app.include_router(monday_router)

@app.get("/")
def health_check():
    return {"status": "api online"}