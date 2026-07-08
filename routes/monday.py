from fastapi import APIRouter, Request
from services.sync_service import processar_webhook_hubspot, processar_webhook_monday

router = APIRouter(prefix="/webhook", tags=["Integracoes"])

@router.post("/monday")
async def webhook_monday(request: Request):
    body = await request.json()

    if "challenge" in body:
        return {"challenge": body["challenge"]}

    return processar_webhook_monday(body)


@router.post("/hubspot")
async def webhook_hubspot(request: Request):
    body = await request.json()
    return processar_webhook_hubspot(body)
