import unicodedata

import requests
from config import MONDAY_ACCOUNT_SLUG, MONDAY_TOKEN

MONDAY_URL = "https://api.monday.com/v2"


def executar_query(query, variables=None):
    headers = {
        "Authorization": MONDAY_TOKEN,
        "Content-Type": "application/json"
    }

    response = requests.post(
        MONDAY_URL,
        json={"query": query, "variables": variables or {}},
        headers=headers,
    )
    response.raise_for_status()

    data = response.json()
    if data.get("errors"):
        raise RuntimeError(data["errors"])

    return data["data"]


def buscar_item(item_id):
    query = """
    query ($item_id: [ID!]) {
      items(ids: $item_id) {
        id
        name
        board {
          id
        }
        column_values {
          id
          text
          value
          type
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
      }
    }
    """

    data = executar_query(query, {"item_id": [str(item_id)]})
    items = data.get("items") or []
    return items[0] if items else None


def atualizar_status(item, status):
    coluna_status = buscar_coluna(item, ["status", "situacao"])
    if not coluna_status:
        raise ValueError("Coluna de status nao encontrada no item do Monday")

    mutation = """
    mutation ($board_id: ID!, $item_id: ID!, $column_id: String!, $value: String!) {
      change_simple_column_value(
        board_id: $board_id,
        item_id: $item_id,
        column_id: $column_id,
        value: $value
      ) {
        id
      }
    }
    """

    board_id = str(item["board"]["id"])
    item_id = str(item["id"])
    return executar_query(
        mutation,
        {
            "board_id": board_id,
            "item_id": item_id,
            "column_id": coluna_status["id"],
            "value": status,
        },
    )


def colunas_por_titulo(item):
    return {
        normalizar_texto(coluna["column"]["title"]): coluna
        for coluna in item.get("column_values", [])
        if coluna.get("column")
    }


def buscar_coluna(item, titulos):
    colunas = colunas_por_titulo(item)
    for titulo in titulos:
        coluna = colunas.get(normalizar_texto(titulo))
        if coluna:
            return coluna
    return None


def texto_coluna(item, titulos, default=""):
    coluna = buscar_coluna(item, titulos)
    if not coluna:
        return default
    return coluna.get("text") or default


def texto_coluna_flexivel(item, titulos, default=""):
    coluna = buscar_coluna(item, titulos)
    if coluna:
        return coluna.get("text") or default

    titulos_normalizados = [normalizar_texto(titulo) for titulo in titulos]
    for coluna in item.get("column_values", []):
        titulo_coluna = normalizar_texto(coluna.get("column", {}).get("title"))
        for titulo in titulos_normalizados:
            if titulo and (titulo in titulo_coluna or titulo_coluna in titulo):
                return coluna.get("text") or default

    return default


def numero_coluna(item, titulos):
    valor = texto_coluna(item, titulos)
    if not valor:
        return 0.0

    valor = valor.replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        return 0.0


def link_item(item):
    board_id = item.get("board", {}).get("id")
    item_id = item.get("id")
    if board_id and item_id:
        return f"https://{MONDAY_ACCOUNT_SLUG}.monday.com/boards/{board_id}/pulses/{item_id}"

    return ""


def links_anexos(item):
    links = []
    for asset in item.get("assets", []):
        public_url = asset.get("public_url")
        if public_url:
            name = asset.get("name") or public_url
            links.append(f"{name}: {public_url}")
    return links


def ultima_descricao(item):
    descricao = texto_coluna(item, ["descricao", "description"])
    if descricao:
        return descricao

    updates = item.get("updates", [])
    if updates:
        return updates[0].get("body") or ""

    return ""


def normalizar_texto(texto):
    texto = texto or ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    return texto.strip().lower()
