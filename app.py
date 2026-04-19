"""
Nucleo — Voice Agent + WhatsApp + Web  v2.1
Puerto: 5065 (TSC) / 8010 (local dev)

Endpoints:
  GET  /                    → index.html (web)
  GET  /leaflet.css         → asset
  GET  /leaflet.js          → asset
  GET  /health              → status JSON
  GET  /api/properties      → catalogo pisos
  GET  /api/agents          → comerciales
  POST /create-web-call     → Retell access token (boton "Hablar con Lucia")
  POST /webhook             → Retell AI events
  POST /whatsapp/inbound    → WhatsApp inbound desde gateway Baileys
  GET  /leads               → ver leads guardados (interno)
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from leads_storage import (
    save_lead,
    save_to_sheets,
    send_email_notification,
    send_to_crm_webhook,
)
from properties import get_agents, get_properties, get_properties_summary

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="Nucleo — Voice + WhatsApp + Web", version="2.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

BASE_DIR              = Path(__file__).resolve().parent
SECRET_TOKEN          = os.getenv("SECRET_TOKEN", "")
AGENT_TRANSFER_NUMBER = os.getenv("AGENT_TRANSFER_NUMBER", "+34663103334")
VOICE_TRANSFER_NUMBER = os.getenv("VOICE_TRANSFER_NUMBER", "+34919934651")
RETELL_API_KEY        = os.getenv("RETELL_API_KEY", "")
RETELL_AGENT_ID       = os.getenv("RETELL_AGENT_ID", "")
PORT                  = int(os.getenv("PORT", "8010"))


# ---------------------------------------------------------------------------
# Web pages + static assets
# ---------------------------------------------------------------------------
@app.post("/search-properties")
async def search_properties(request: Request):
    try:
        payload = await request.json()

        area = str(payload.get("area", "")).strip().lower()
        bedrooms = str(payload.get("bedrooms", "")).strip()
        operation = str(payload.get("operation", "")).strip().lower()
        budget = str(payload.get("budget", "")).strip()

        props = get_properties()
        results = []

        def parse_price(price_text: str) -> int:
            digits = "".join(ch for ch in str(price_text) if ch.isdigit())
            return int(digits) if digits else 0

        for prop in props:
            zona = str(prop.get("zona", "")).lower()
            titulo = str(prop.get("titulo", "")).lower()
            descripcion = str(prop.get("descripcion_corta", "")).lower()
            operacion = str(prop.get("operacion", "")).lower()
            habs = str(prop.get("habitaciones", ""))
            precio_num = parse_price(prop.get("precio_texto", ""))

            if area and area not in zona and area not in titulo and area not in descripcion:
                continue

            if bedrooms and bedrooms != habs:
                continue

            if operation and operation != operacion:
                continue

            if budget:
                budget_num = parse_price(budget)
                if budget_num and precio_num and precio_num > budget_num:
                    continue

            results.append({
                "ref": prop.get("ref"),
                "titulo": prop.get("titulo"),
                "zona": prop.get("zona"),
                "operacion": prop.get("operacion"),
                "precio_texto": prop.get("precio_texto"),
                "m2": prop.get("m2"),
                "habitaciones": prop.get("habitaciones"),
                "banos": prop.get("banos"),
                "descripcion_corta": prop.get("descripcion_corta"),
                "extras": prop.get("extras", []),
            })

        return {
            "success": True,
            "count": len(results),
            "results": results[:10],
        }

    except Exception as e:
        log.exception("search-properties error")
        return {
            "success": False,
            "error": str(e),
            "count": 0,
            "results": [],
        }

@app.get("/")
def index():
    """Sirve la pagina principal de Nucleo."""
    html_file = BASE_DIR / "index.html"
    if not html_file.exists():
        raise HTTPException(status_code=503, detail="index.html no generado. Ejecuta: python build_page.py")
    return FileResponse(str(html_file), media_type="text/html")


@app.get("/leaflet.css")
def leaflet_css():
    return FileResponse(str(BASE_DIR / "leaflet.css"), media_type="text/css")


@app.get("/leaflet.js")
def leaflet_js():
    return FileResponse(str(BASE_DIR / "leaflet.js"), media_type="application/javascript")


@app.get("/retell-sdk.js")
def retell_sdk():
    return FileResponse(str(BASE_DIR / "retell-sdk.js"), media_type="application/javascript")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "agent": "Lucia — Nucleo Inmobiliaria",
        "time": datetime.now().isoformat(),
        "properties": len(get_properties()),
    }


# ---------------------------------------------------------------------------
# API publica — propiedades (consumida por widgets / CRM externos)
# ---------------------------------------------------------------------------

@app.get("/api/properties")
def api_properties():
    props = get_properties()
    return {"properties": props, "total": len(props)}


@app.get("/api/agents")
def api_agents():
    return {"agents": get_agents()}


# ---------------------------------------------------------------------------
# Retell — crear llamada web (boton "Hablar con Lucia")
# ---------------------------------------------------------------------------

@app.post("/create-web-call")
async def create_web_call():
    if not RETELL_API_KEY or not RETELL_AGENT_ID:
        raise HTTPException(
            status_code=503,
            detail="RETELL_API_KEY o RETELL_AGENT_ID no configurados",
        )
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                "https://api.retellai.com/v2/create-web-call",
                headers={
                    "Authorization": f"Bearer {RETELL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={"agent_id": RETELL_AGENT_ID},
            )
        if r.status_code >= 400:
            log.error("Retell create-web-call failed: %s — %s", r.status_code, r.text[:300])
            raise HTTPException(status_code=502, detail="Retell error")
        return r.json()
    except httpx.HTTPError as exc:
        log.error("Retell HTTP error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))


# ---------------------------------------------------------------------------
# WhatsApp inbound (desde gateway.js via Baileys)
# El gateway envia la respuesta al cliente — este endpoint NO manda nada.
# ---------------------------------------------------------------------------

class WAInbound(BaseModel):
    sender:     str
    senderId:   Optional[str] = None
    body:       str
    pushName:   Optional[str] = None
    phoneE164:  Optional[str] = None
    senderType: Optional[str] = "phone"
    rawJid:     Optional[str] = None
    channel:    str = "whatsapp"
    tenant:     Optional[str] = "nucleo"


@app.post("/whatsapp/inbound")
async def whatsapp_inbound(msg: WAInbound):
    from anthropic import Anthropic

    body      = msg.body.strip()
    sender_id = (msg.senderId or msg.sender).replace("@s.whatsapp.net", "")
    push_name = msg.pushName or "Cliente"
    props_ctx = get_properties_summary()

    log.info("WA in ***%s (%s): %s", sender_id[-4:], push_name, body[:80])

    system_prompt = (
        "Eres Lucia, asistente virtual de Nucleo Inmobiliaria en El Campello, Alicante.\n"
        "Respondes por WhatsApp: tono cercano, respuestas cortas (max 3 parrafos), sin markdown.\n"
        "Si el cliente muestra interes en una propiedad, pide su nombre y telefono para la visita.\n"
        "Si pide hablar con una persona, indica que un agente le llamara en breve.\n"
        "Nunca inventes precios ni datos que no esten en tu base de conocimiento.\n\n"
        f"PROPIEDADES EN VENTA — EL CAMPELLO:\n{props_ctx}"
    )

    try:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        resp   = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            system=system_prompt,
            messages=[{"role": "user", "content": f"{push_name}: {body}"}],
        )
        reply = resp.content[0].text.strip()
    except Exception as exc:
        log.error("LLM error: %s", exc)
        reply = (
            "Hola! Soy Lucia de Nucleo Inmobiliaria. "
            "Tenemos un problema tecnico. El equipo te contactara enseguida."
        )

    save_lead({
        "client_name": push_name,
        "phone":       msg.phoneE164 or sender_id,
        "interest":    body[:200],
        "notes":       f"WA: {reply[:200]}",
        "source":      "whatsapp",
        "type":        "wa_message",
    })

    log.info("WA reply ***%s: %s", sender_id[-4:], reply[:80])
    return {"status": "replied", "reply": reply}


# ---------------------------------------------------------------------------
# Retell AI webhook (llamadas de voz)
# ---------------------------------------------------------------------------

@app.post("/webhook")
async def retell_webhook(request: Request):
    if SECRET_TOKEN:
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {SECRET_TOKEN}":
            raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = body.get("event", "")
    log.info("Retell event: %s", event)

    if event == "call_started":
        log.info("Llamada iniciada: %s", body.get("call", {}).get("call_id", "?"))
        return JSONResponse({"status": "ok"})

    if event == "tool_call_invocation":
        return await _handle_tool_call(body)

    if event in ("call_ended", "call_analyzed"):
        return await _handle_call_ended(body)

    log.warning("Evento desconocido: %s", event)
    return JSONResponse({"status": "ok"})


async def _handle_tool_call(body: dict) -> JSONResponse:
    tool_call    = body.get("tool_call", {})
    tool_call_id = tool_call.get("tool_call_id", "")
    name         = tool_call.get("name", "")
    args         = tool_call.get("arguments", {})

    if isinstance(args, str):
        try:
            args = json.loads(args)
        except Exception:
            args = {}

    log.info("Tool call: %s | args: %s", name, args)

    if name in ("book_appointment", "book_appointment_v2"):
        result = _handle_book_appointment(args)
    elif name in ("send_lead_to_crm", "send_lead_to_crm_v2"):
        result = _handle_send_lead(args, body.get("call", {}))
    elif name == "transfer_to_human":
        result = _handle_transfer()
    else:
        result = f"Funcion '{name}' no reconocida."

    return JSONResponse({"tool_call_id": tool_call_id, "result": result})


def _handle_book_appointment(args: dict) -> str:
    client_name    = args.get("client_name", "Cliente")
    phone          = args.get("phone", "—")
    preferred_time = args.get("preferred_time", "—")
    property_id    = args.get("property_id", "—")

    lead = {
        "client_name":  client_name,
        "phone":        phone,
        "appointment":  preferred_time,
        "property_ref": property_id,
        "interest":     f"Visita — {property_id}",
        "notes":        f"Cita para {preferred_time}",
        "source":       "voice_call",
        "type":         "appointment",
    }
    save_lead(lead)
    send_email_notification(lead)
    save_to_sheets(lead)
    send_to_crm_webhook(lead)

    return (
        f"Cita registrada para {client_name}. "
        f"El equipo confirmara la visita al {phone} para {preferred_time}."
    )


def _handle_send_lead(args: dict, call_info: dict) -> str:
    client_name = args.get("client_name", "Cliente")
    phone       = args.get("phone", "—")
    interest    = args.get("interest", "—")
    notes       = args.get("notes", "")

    lead = {
        "client_name": client_name,
        "phone":       phone,
        "interest":    interest,
        "notes":       notes,
        "call_id":     call_info.get("call_id", ""),
        "source":      "voice_call",
        "type":        "lead",
    }
    save_lead(lead)
    send_email_notification(lead)
    save_to_sheets(lead)
    send_to_crm_webhook(lead)

    return f"Datos de {client_name} registrados. El equipo de Nucleo le llamara pronto."


def _handle_transfer() -> str:
    log.info("Transfer to human: %s", VOICE_TRANSFER_NUMBER)
    return "Voy a transferirle con uno de nuestros agentes. Un momento por favor."


async def _handle_call_ended(body: dict) -> JSONResponse:
    call       = body.get("call", {})
    call_id    = call.get("call_id", "?")
    transcript = call.get("transcript", "")
    duration   = call.get("duration_ms", 0) // 1000
    analysis   = call.get("call_analysis", {})

    log.info("Llamada finalizada: %s | %ds", call_id, duration)

    lead_summary = {
        "call_id":          call_id,
        "duration_seconds": duration,
        "transcript":       transcript[:500],
        "client_name":      analysis.get("client_name", "Desconocido"),
        "phone":            analysis.get("phone", "—"),
        "interest":         analysis.get("call_summary", "—"),
        "notes":            analysis.get("call_summary", ""),
        "source":           "voice_call_ended",
        "type":             "call_summary",
    }
    save_lead(lead_summary)
    send_email_notification(lead_summary, transcript)

    return JSONResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# Leads (interno)
# ---------------------------------------------------------------------------

@app.get("/leads")
def get_leads(token: str = ""):
    if SECRET_TOKEN and token != SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Token requerido")
    from leads_storage import _load_leads
    leads = _load_leads()
    return {"total": len(leads), "leads": leads[-50:]}


# ---------------------------------------------------------------------------
# Boot
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=False)
