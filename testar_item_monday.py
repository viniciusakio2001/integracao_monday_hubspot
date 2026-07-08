import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_TOKEN")
MONDAY_API_URL = "https://api.monday.com/v2"

ITEM_ID = 12244254265

headers = {
    "Authorization": MONDAY_TOKEN,
    "Content-Type": "application/json"
}

def executar_query(query, variables=None):
    response = requests.post(
        MONDAY_API_URL,
        headers=headers,
        json={
            "query": query,
            "variables": variables or {}
        }
    )

    print("Status:", response.status_code)
    print(json.dumps(response.json(), indent=4, ensure_ascii=False))

query1 = """
query ($item_id: [ID!]) {
  items(ids: $item_id) {
    id
    name
    column_values {
      id
      text
      value
      column {
        title
      }
    }
    updates {
      id
      body
    }
    assets {
      id
      name
      public_url
    }
  }
}
"""

query2 = """
query ($item_id: [ID!]) {
  items(ids: $item_id) {
    id
    name

    column_values {
      id
      text
      value
      column {
        title
      }
    }

    updates {
      id
      body
      created_at
    }

    assets {
      id
      name
      public_url
    }

    subitems {
      id
      name
      column_values {
        id
        text
        value
        column {
          title
        }
      }
    }
  }
}
"""

query3 = """
query {
  docs(ids: [43207761]) {
    id
    name
    blocks {
      id
      type
      content
    }
  }
}
"""
executar_query(
    query3,
    {
        "item_id": [ITEM_ID]
    }
)


