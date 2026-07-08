import os
import requests
from dotenv import load_dotenv

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_TOKEN")
MONDAY_BOARD_ID_PERS= os.getenv("MONDAY_BOARD_ID_PERS")
MONDAY_BOARD_ID_INDICADOR= os.getenv("MONDAY_BOARD_ID_INDICADOR")
MONDAY_BOARD_ID_DEV= os.getenv("MONDAY_BOARD_ID_DEV")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "https://guide-unbroken-salt.ngrok-free.dev")

url = "https://api.monday.com/v2"

headers = {
    "Authorization": MONDAY_TOKEN,
    "Content-Type": "application/json"
}

def criar_webhook(event):
    query = f"""
    mutation {{
      create_webhook(
        board_id: {MONDAY_BOARD_ID_PERS},
        url: "{WEBHOOK_BASE_URL}/webhook/monday",
        event: {event}
      ) {{
        id
        board_id
      }}
    }}
    """

    response = requests.post(url, json={"query": query}, headers=headers)
    print(f"Evento: {event}")
    print(response.status_code)
    print("Resposta: ")
    print(response.text)
    print(response.json())


criar_webhook("create_item")
criar_webhook("change_column_value")
