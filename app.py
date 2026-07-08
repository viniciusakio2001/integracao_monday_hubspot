from fastapi import FastAPI, Request
from routes.monday import public_router, router as monday_router
from services.sync_service import processar_webhook_hubspot

app = FastAPI()

app.include_router(monday_router)
app.include_router(public_router)

@app.get("/")
def health_check():
    return {"status": "api online"}

@app.get("/hubspot-monday")
def health_check():
    return {"status": "api online"}


@app.post("/hubspot-monday")
async def webhook_hubspot_monday(request: Request):
    body = await request.json()
    return processar_webhook_hubspot(body)
