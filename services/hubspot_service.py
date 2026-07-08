import requests
from config import (
    HUBSPOT_PIPELINE_ID_NII,
    HUBSPOT_STAGE_ID_ANALISE,
    HUBSPOT_STAGE_ID_NOVO,
    HUBSPOT_TIPO_SOLICITACAO_PERSONALIZACAO,
    HUBSPOT_TIPO_TICKET_PERSONALIZACAO,
    HUBSPOT_TOKEN,
)
from services.monday_service import (
    link_item,
    links_anexos,
    numero_coluna,
    texto_coluna,
    ultima_descricao,
)

HUBSPOT_TICKETS_URL = "https://api.hubapi.com/crm/v3/objects/tickets"


def headers():
    return {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json",
    }


def criar_ticket(item):
    anexos = links_anexos(item)

    payload = {
        "properties": limpar_propriedades(
            {
                "subject": item["name"],
                "content": montar_descricao(item, anexos),
                "hs_pipeline": HUBSPOT_PIPELINE_ID_NII,
                "hs_pipeline_stage": HUBSPOT_STAGE_ID_NOVO,
                "hs_ticket_priority": texto_coluna(item, ["prioridade", "priority"]),
                "monday_dev": link_item(item),
                "tipo_do_ticket": HUBSPOT_TIPO_TICKET_PERSONALIZACAO,
                "nome_do_cliente": texto_coluna(item, ["nome do cliente", "cliente"]),
                "tipo_de_solicitacao": HUBSPOT_TIPO_SOLICITACAO_PERSONALIZACAO,
                "id_monday": str(item["id"]),
                "anexos": "\n".join(anexos),
            }
        )
    }

    response = requests.post(HUBSPOT_TICKETS_URL, json=payload, headers=headers())
    response.raise_for_status()

    return response.json()


def buscar_ticket(ticket_id):
    properties = ",".join(
        [
            "hs_pipeline_stage",
            "id_monday",
            "subject",
            "quantidade_de_horas",
            "horas_de_desenvolvimento",
            "horas_de_analise",
            "horas_qa",
        ]
    )
    url = f"{HUBSPOT_TICKETS_URL}/{ticket_id}?properties={properties}"
    response = requests.get(url, headers=headers())
    response.raise_for_status()
    return response.json()


def buscar_ticket_por_id_monday(item_id):
    payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "id_monday",
                        "operator": "EQ",
                        "value": str(item_id),
                    }
                ]
            }
        ],
        "properties": ["id_monday", "hs_pipeline_stage", "subject"],
        "limit": 1,
    }

    response = requests.post(
        f"{HUBSPOT_TICKETS_URL}/search",
        json=payload,
        headers=headers(),
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    return results[0] if results else None


def atualizar_ticket(ticket_id, properties):
    payload = {"properties": limpar_propriedades(properties)}
    response = requests.patch(
        f"{HUBSPOT_TICKETS_URL}/{ticket_id}",
        json=payload,
        headers=headers(),
    )
    response.raise_for_status()
    return response.json()


def atualizar_horas_e_analise(ticket_id, item):
    horas_dev = numero_coluna(item, ["horas de desenvolvimento", "horas_de_desenvolvimento"])
    horas_analise = numero_coluna(item, ["horas de analise", "horas_de_analise"])
    horas_qa = numero_coluna(item, ["horas qa", "horas_qa"])
    total = horas_dev + horas_analise + horas_qa

    return atualizar_ticket(
        ticket_id,
        {
            "quantidade_de_horas": total,
            "horas_de_desenvolvimento": horas_dev,
            "horas_de_analise": horas_analise,
            "horas_qa": horas_qa,
            "hs_pipeline_stage": HUBSPOT_STAGE_ID_ANALISE,
        },
    )


def montar_descricao(item, anexos):
    descricao = ultima_descricao(item) or "Sem descricao informada"
    partes = [
        descricao,
        "",
        f"Monday: {link_item(item)}",
    ]

    if anexos:
        partes.extend(["", "Anexos:", *anexos])

    return "\n".join(partes)


def limpar_propriedades(properties):
    return {
        key: str(value)
        for key, value in properties.items()
        if value is not None and value != ""
    }
