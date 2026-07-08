from config import (
    HUBSPOT_STAGE_ID_AGUARD_DEV,
    HUBSPOT_STAGE_ID_FINALIZADO,
    MONDAY_BOARD_ID_PERSONALIZACAO,
    MONDAY_STATUS_AGUARDANDO_APROVACAO,
    MONDAY_STATUS_EM_LEVANTAMENTO,
    MONDAY_STATUS_HORAS_RECEBIDAS,
)
from services.hubspot_service import (
    atualizar_content,
    atualizar_horas_e_analise,
    buscar_ticket,
    buscar_ticket_por_id_monday,
    criar_ticket,
)
from services.monday_service import atualizar_status, buscar_item, normalizar_texto, texto_coluna


def processar_webhook_monday(body):
    event = body.get("event", {})
    item_id = event.get("pulseId")
    board_id = str(event.get("boardId") or "")
    event_type = event.get("type")

    if not item_id:
        return {"erro": "pulseId nao encontrado"}

    if board_id and board_id != str(MONDAY_BOARD_ID_PERSONALIZACAO):
        return {
            "status": "ignorado",
            "motivo": "board fora do escopo",
            "board_id": board_id,
        }

    item = buscar_item(item_id)
    if not item:
        return {"erro": "item nao encontrado", "monday_item_id": item_id}

    item_board_id = str(item.get("board", {}).get("id") or "")
    if item_board_id != str(MONDAY_BOARD_ID_PERSONALIZACAO):
        return {
            "status": "ignorado",
            "motivo": "item fora do board personalizacao/integracao",
            "board_id": item_board_id,
        }

    if evento_criacao(event_type, event):
        return criar_ticket_hubspot(item)

    status_monday = texto_coluna(item, ["status", "situacao"])
    if normalizar_texto(status_monday) == normalizar_texto(MONDAY_STATUS_HORAS_RECEBIDAS):
        return enviar_horas_para_hubspot(item)

    if event_type == "change_column_value" or event.get("columnId"):
        return atualizar_content_hubspot(item)

    return {
        "status": "ignorado",
        "motivo": "evento do Monday sem acao configurada",
        "monday_item_id": item_id,
        "event_type": event_type,
        "status_monday": status_monday,
    }


def processar_webhook_hubspot(body):
    eventos = body if isinstance(body, list) else [body]
    resultados = []

    for event in eventos:
        property_name = event.get("propertyName")
        property_value = str(event.get("propertyValue") or "")
        ticket_id = event.get("objectId")

        if property_name and property_name != "hs_pipeline_stage":
            resultados.append({"status": "ignorado", "motivo": "propriedade sem acao"})
            continue

        if not ticket_id:
            resultados.append({"erro": "objectId do ticket nao encontrado"})
            continue

        if property_value == str(HUBSPOT_STAGE_ID_AGUARD_DEV):
            resultados.append(
                atualizar_status_monday_por_ticket(
                    ticket_id,
                    MONDAY_STATUS_EM_LEVANTAMENTO,
                    "HubSpot em aguardando DEV",
                )
            )
        elif property_value == str(HUBSPOT_STAGE_ID_FINALIZADO):
            resultados.append(
                atualizar_status_monday_por_ticket(
                    ticket_id,
                    MONDAY_STATUS_AGUARDANDO_APROVACAO,
                    "HubSpot fechado/finalizado",
                )
            )
        else:
            resultados.append(
                {
                    "status": "ignorado",
                    "motivo": "stage do HubSpot sem acao configurada",
                    "hubspot_ticket_id": ticket_id,
                    "stage": property_value,
                }
            )

    return {"resultados": resultados}


def criar_ticket_hubspot(item):
    ticket = criar_ticket(item)

    return {
        "status": "ticket criado",
        "monday_item_id": item["id"],
        "hubspot_ticket_id": ticket.get("id"),
    }


def enviar_horas_para_hubspot(item):
    ticket = buscar_ticket_por_id_monday(item["id"])
    if not ticket:
        return {
            "erro": "ticket HubSpot nao encontrado pelo id_monday",
            "monday_item_id": item["id"],
        }

    ticket_atualizado = atualizar_horas_e_analise(ticket["id"], item)
    return {
        "status": "horas enviadas para HubSpot",
        "monday_item_id": item["id"],
        "hubspot_ticket_id": ticket_atualizado.get("id"),
    }


def atualizar_content_hubspot(item):
    ticket = buscar_ticket_por_id_monday(item["id"])
    if not ticket:
        return {
            "erro": "ticket HubSpot nao encontrado pelo id_monday",
            "monday_item_id": item["id"],
        }

    ticket_atualizado = atualizar_content(ticket["id"], item)
    return {
        "status": "content atualizado no HubSpot",
        "monday_item_id": item["id"],
        "hubspot_ticket_id": ticket_atualizado.get("id"),
    }


def atualizar_status_monday_por_ticket(ticket_id, status_monday, motivo):
    ticket = buscar_ticket(ticket_id)
    id_monday = ticket.get("properties", {}).get("id_monday")
    if not id_monday:
        return {
            "erro": "ticket HubSpot sem propriedade id_monday",
            "hubspot_ticket_id": ticket_id,
        }

    item = buscar_item(id_monday)
    if not item:
        return {
            "erro": "item Monday nao encontrado",
            "hubspot_ticket_id": ticket_id,
            "monday_item_id": id_monday,
        }

    atualizar_status(item, status_monday)
    return {
        "status": "status Monday atualizado",
        "motivo": motivo,
        "hubspot_ticket_id": ticket_id,
        "monday_item_id": id_monday,
        "status_monday": status_monday,
    }


def evento_criacao(event_type, event):
    if event_type in ("create_pulse", "create_item"):
        return True

    return not event.get("columnId") and not event.get("columnType")
