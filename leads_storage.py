"""
Almacenamiento de leads — JSON local + Email HTML + ICS + CRM webhook + Google Sheets.
"""

import json
import logging
import os
import smtplib
import ssl
import uuid
from datetime import datetime, timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

log = logging.getLogger(__name__)

LEADS_FILE = Path(__file__).parent / "leads.json"


# ── JSON local ────────────────────────────────────────────────────────────────

def save_lead(lead: dict) -> None:
    leads = _load_leads()
    lead["created_at"] = datetime.now().isoformat()
    leads.append(lead)
    LEADS_FILE.write_text(json.dumps(leads, ensure_ascii=False, indent=2))
    log.info(f"Lead guardado: {lead.get('client_name')} — {lead.get('phone')}")


def _load_leads() -> list:
    if LEADS_FILE.exists():
        try:
            return json.loads(LEADS_FILE.read_text())
        except Exception:
            return []
    return []


# ── Utilidades email / calendario ─────────────────────────────────────────────

def _smtp_config():
    smtp_server = os.getenv("SMTP_SERVER", "smtp.ionos.es")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    return smtp_server, smtp_port, smtp_user, smtp_password


def _send_email_message(msg: MIMEMultipart, recipients: list[str]) -> None:
    smtp_server, smtp_port, smtp_user, smtp_password = _smtp_config()

    if not all([smtp_user, smtp_password]) or not recipients:
        log.warning("SMTP o destinatarios no configurados — omitiendo email")
        return

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipients, msg.as_string())
        log.info("Email enviado a %s", ", ".join(recipients))
    except Exception as e:
        log.error("Error enviando email: %s", e)


def _parse_preferred_time_to_event(preferred_time: str):
    """
    Parser simple para demo.
    Si no puede interpretar bien, devuelve None y no se genera ICS.
    Casos soportados:
      - YYYY-MM-DD HH:MM
      - YYYY-MM-DDTHH:MM
    Duración por defecto: 45 min
    """
    if not preferred_time:
        return None

    candidates = [
        preferred_time.strip(),
        preferred_time.strip().replace("T", " "),
    ]

    for raw in candidates:
        try:
            start_dt = datetime.strptime(raw, "%Y-%m-%d %H:%M")
            end_dt = start_dt + timedelta(minutes=45)
            return start_dt, end_dt
        except Exception:
            pass

    return None


def _build_ics(lead: dict) -> str | None:
    appointment = lead.get("appointment") or lead.get("preferred_time") or ""
    parsed = _parse_preferred_time_to_event(appointment)
    if not parsed:
        return None

    start_dt, end_dt = parsed
    uid = f"{uuid.uuid4()}@nexusfinlabs.com"
    now_utc = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    start_utc = start_dt.strftime("%Y%m%dT%H%M%S")
    end_utc = end_dt.strftime("%Y%m%dT%H%M%S")

    client_name = lead.get("client_name", "Cliente")
    phone = lead.get("phone", "—")
    property_ref = lead.get("property_ref", "Sin especificar")
    interest = lead.get("interest", "Visita inmobiliaria")
    notes = lead.get("notes", "")

    description = (
        f"Cliente: {client_name}\\n"
        f"Teléfono: {phone}\\n"
        f"Propiedad: {property_ref}\\n"
        f"Interés: {interest}\\n"
        f"Notas: {notes}"
    )

    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//NexusFinLabs//Nucleo Voice Agent//ES
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{now_utc}
DTSTART:{start_utc}
DTEND:{end_utc}
SUMMARY:Visita Núcleo | {client_name} | {property_ref}
DESCRIPTION:{description}
LOCATION:Núcleo Inmobiliaria / Propiedad {property_ref}
STATUS:CONFIRMED
SEQUENCE:0
END:VEVENT
END:VCALENDAR
"""
    return ics


# ── Email al equipo Núcleo ────────────────────────────────────────────────────

def send_email_notification(lead: dict, transcript: str = "") -> None:
    smtp_server, smtp_port, smtp_user, smtp_password = _smtp_config()

    notify_human = (
        os.getenv("NOTIFY_EMAIL_HUMAN")
        or os.getenv("NOTIFY_EMAIL")
        or os.getenv("NOTIFY_EMAIL_1", "")
    )
    notify_ics = os.getenv("NOTIFY_EMAIL_ICS", "")

    if not all([smtp_user, smtp_password]):
        log.warning("SMTP no configurado — omitiendo notificación")
        return

    appointment = lead.get("appointment") or lead.get("preferred_time") or "—"
    interest = lead.get("interest", "—")
    notes = lead.get("notes", "—")
    property_ref = lead.get("property_ref", "—")
    client_name = lead.get("client_name", "Desconocido")
    phone = lead.get("phone", "—")

    # 1) Email bonito a humano
    if notify_human:
        subject = f"[Núcleo] Nuevo lead: {client_name} — {phone}"

        html = f"""
        <html><body style="font-family:Arial,sans-serif;max-width:680px;margin:auto;background:#f7f7fb;padding:24px">
        <div style="background:#111827;padding:24px;border-radius:14px 14px 0 0">
          <h2 style="color:#ffffff;margin:0">Nuevo Lead | Núcleo Inmobiliaria</h2>
          <p style="color:#d1d5db;margin:8px 0 0">Lucía ha capturado una nueva interacción</p>
        </div>

        <div style="background:#ffffff;border:1px solid #e5e7eb;border-top:none;padding:24px;border-radius:0 0 14px 14px">
          <table style="width:100%;border-collapse:collapse;font-size:14px">
            <tr>
              <td style="padding:10px;color:#6b7280;width:32%">Nombre</td>
              <td style="padding:10px;font-weight:700">{client_name}</td>
            </tr>
            <tr style="background:#f9fafb">
              <td style="padding:10px;color:#6b7280">Teléfono</td>
              <td style="padding:10px;font-weight:700">{phone}</td>
            </tr>
            <tr>
              <td style="padding:10px;color:#6b7280">Interés</td>
              <td style="padding:10px">{interest}</td>
            </tr>
            <tr style="background:#f9fafb">
              <td style="padding:10px;color:#6b7280">Propiedad</td>
              <td style="padding:10px">{property_ref}</td>
            </tr>
            <tr>
              <td style="padding:10px;color:#6b7280">Cita solicitada</td>
              <td style="padding:10px;color:#b91c1c;font-weight:700">{appointment}</td>
            </tr>
            <tr style="background:#f9fafb">
              <td style="padding:10px;color:#6b7280">Notas</td>
              <td style="padding:10px">{notes}</td>
            </tr>
          </table>

          {('<hr style="margin:24px 0;border:none;border-top:1px solid #e5e7eb"><h4 style="margin:0 0 10px">Transcripción</h4><pre style="background:#f3f4f6;padding:14px;border-radius:8px;font-size:12px;white-space:pre-wrap">' + transcript[:3000] + '</pre>') if transcript else ''}
        </div>

        <p style="color:#9ca3af;font-size:12px;text-align:center;margin-top:10px">
          NexusFinLabs · {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </p>
        </body></html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = notify_human
        msg.attach(MIMEText(html, "html"))
        _send_email_message(msg, [notify_human])

    # 2) ICS a buzón operativo solo si hay cita interpretable
    if notify_ics:
        ics_content = _build_ics(lead)
        if ics_content:
            subject = f"[ICS] Visita Núcleo: {client_name} | {property_ref}"

            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = smtp_user
            msg["To"] = notify_ics

            body = f"""Se adjunta evento ICS de visita.

Cliente: {client_name}
Teléfono: {phone}
Propiedad: {property_ref}
Cita: {appointment}
"""
            msg.attach(MIMEText(body, "plain", "utf-8"))

            part = MIMEApplication(ics_content.encode("utf-8"), _subtype="ics")
            part.add_header("Content-Disposition", "attachment", filename="visita_nucleo.ics")
            part.add_header("Content-Class", "urn:content-classes:calendarmessage")
            msg.attach(part)

            _send_email_message(msg, [notify_ics])
        else:
            log.info("No se generó ICS: preferred_time no interpretable (%s)", appointment)


# ── CRM Webhook externo ───────────────────────────────────────────────────────

def send_to_crm_webhook(payload: dict) -> None:
    import httpx
    url = os.getenv("WEBHOOK_CRM_URL", "")
    if not url:
        return
    try:
        r = httpx.post(url, json=payload, timeout=10)
        log.info(f"CRM webhook: {r.status_code}")
    except Exception as e:
        log.error(f"Error CRM webhook: {e}")


# ── Google Sheets (opcional) ──────────────────────────────────────────────────

def save_to_sheets(lead: dict) -> None:
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
    tab_name = os.getenv("GOOGLE_SHEETS_TAB_NAME", "nucleo")
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not spreadsheet_id or not creds_path:
        return
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(spreadsheet_id)
        try:
            ws = sh.worksheet(tab_name)
        except Exception:
            ws = sh.add_worksheet(title=tab_name, rows=1000, cols=10)
        if not ws.get_all_values():
            ws.append_row(["Fecha", "Ref", "Nombre", "Teléfono", "Interés", "Propiedad", "Cita", "Tipo", "Notas", "Call ID"])
        ws.append_row([
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            lead.get("property_ref", ""),
            lead.get("client_name", ""),
            lead.get("phone", ""),
            lead.get("interest", ""),
            lead.get("property_ref", ""),
            lead.get("appointment", "") or lead.get("preferred_time", ""),
            lead.get("type", ""),
            lead.get("notes", ""),
            lead.get("call_id", ""),
        ])
        log.info(f"Lead guardado en Google Sheets tab '{tab_name}'")
    except Exception as e:
        log.error(f"Error Google Sheets: {e}")
