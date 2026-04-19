"""
Núcleo Voice Agent — Setup en Retell AI
Ejecutar UNA VEZ para crear el agente Lucía en la plataforma Retell.

Uso:
  python retell_setup.py               # crear agente + LLM
  python retell_setup.py --status      # ver agentes y números actuales
  python retell_setup.py --update      # actualizar system prompt del LLM existente
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv
from retell import Retell

from properties import get_properties_summary

load_dotenv()

RETELL_API_KEY = os.getenv("RETELL_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "11labs-Rachel")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://tsc.tail8dce43.ts.net/nucleo/webhook")
VOICE_TRANSFER_NUMBER = os.getenv("VOICE_TRANSFER_NUMBER", "+34919934651")

# IDs persistentes — rellenar después del primer setup
RETELL_LLM_ID = os.getenv("RETELL_LLM_ID", "")
RETELL_AGENT_ID = os.getenv("RETELL_AGENT_ID", "")

SYSTEM_PROMPT = f"""Eres Lucía, la asistente virtual de Núcleo Inmobiliaria, ubicada en la Playa de San Juan, Alicante. Tu misión es atender a los clientes que llaman interesados en comprar o alquilar pisos.

PERSONALIDAD:
- Amable, cercana y profesional
- Hablas en español de España con naturalidad, no en tono robótico
- Eres concisa pero completa. No das información irrelevante
- Si no sabes algo, lo reconoces y ofreces que un agente contacte al cliente

FLUJO DE LLAMADA:
1. Saluda: "Buenas, Núcleo Inmobiliaria, le atiende Lucía, ¿en qué puedo ayudarle?"
2. Identifica el interés: ¿compra o alquiler? ¿qué tipo de piso busca?
3. Informa sobre las propiedades disponibles de la lista de abajo
4. Si hay interés concreto en una propiedad: recoge nombre completo, teléfono, franja horaria preferida y llama a book_appointment
5. Si el cliente solo quiere dejar sus datos: llama a send_lead_to_crm con nombre, teléfono e interés
6. Confirma y cierra con amabilidad

REGLAS:
- Nunca inventes precios ni detalles que no estén en tu base de conocimiento
- Si preguntan por algo que no tienes: "Voy a dejar nota para que nuestro equipo le llame con esa información", luego llama a send_lead_to_crm
- Si piden hablar con una persona: llama a transfer_to_human
- Si te preguntan directamente si eres una IA: sé honesta y di que eres una asistente virtual de Núcleo
- Nunca reveles que usas ninguna tecnología concreta

BASE DE CONOCIMIENTO — PROPIEDADES DISPONIBLES:
{get_properties_summary()}
"""

FUNCTIONS = [
    {
        "name": "book_appointment",
        "description": "Registra una cita para visitar un piso. Usar cuando el cliente quiere concretar una visita.",
        "parameters": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string", "description": "Nombre completo del cliente"},
                "phone": {"type": "string", "description": "Número de teléfono del cliente"},
                "property_id": {"type": "string", "description": "Referencia del piso (ej: NUC-001) o 'sin especificar'"},
                "preferred_time": {"type": "string", "description": "Franja horaria preferida para la visita"},
            },
            "required": ["client_name", "phone", "preferred_time"],
        },
    },
    {
        "name": "send_lead_to_crm",
        "description": "Registra los datos del cliente y su interés cuando no hay cita concreta o al finalizar la llamada.",
        "parameters": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string", "description": "Nombre completo del cliente"},
                "phone": {"type": "string", "description": "Número de teléfono del cliente"},
                "interest": {"type": "string", "description": "Descripción del interés: compra/alquiler, tipo de piso, presupuesto"},
                "notes": {"type": "string", "description": "Notas adicionales de la conversación"},
            },
            "required": ["client_name", "phone", "interest"],
        },
    },
    {
        "name": "transfer_to_human",
        "description": "Transfiere la llamada a un agente humano de Núcleo cuando el cliente lo solicita o la consulta es compleja.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
]


def create_agent(client: Retell) -> None:
    print("\n── Creando LLM en Retell...")
    llm = client.llm.create(
        model="claude-4.6-sonnet",
        general_prompt=SYSTEM_PROMPT,
        general_tools=[
            {"type": "end_call", "name": "end_call"},
            {
                "type": "transfer_call",
                "name": "transfer_to_human",
                "description": "Transfiere la llamada a un agente humano de Núcleo",
                "transfer_destination": {
                    "type": "predefined",
                    "number": VOICE_TRANSFER_NUMBER
                },
                "transfer_option": {
                    "type": "cold_transfer"
                }
            },
        ],
        starting_state="main",
        states=[
            {
                "name": "main",
                "tools": [
                    {
                        "type": "custom",
                        "name": "book_appointment",
                        "description": FUNCTIONS[0]["description"],
                        "parameters": FUNCTIONS[0]["parameters"],
                        "url": WEBHOOK_URL,
                    },
                    {
                        "type": "custom",
                        "name": "send_lead_to_crm",
                        "description": FUNCTIONS[1]["description"],
                        "parameters": FUNCTIONS[1]["parameters"],
                        "url": WEBHOOK_URL,
                    },
                ],
            }
        ],
    )
    print(f"✅ LLM creado: {llm.llm_id}")

    print("\n── Creando agente Lucía...")
    agent = client.agent.create(
        response_engine={"type": "retell-llm", "llm_id": llm.llm_id},
        voice_id=ELEVENLABS_VOICE_ID,
        agent_name="Lucía — Núcleo Inmobiliaria",
        language="es-ES",
        voice_speed=1.0,
        responsiveness=0.9,
        interruption_sensitivity=0.8,
        post_call_analysis_data=[
            {"name": "client_name", "type": "string", "description": "Nombre del cliente"},
            {"name": "phone", "type": "string", "description": "Teléfono del cliente"},
            {"name": "interest", "type": "string", "description": "Interés: compra/alquiler, tipo piso"},
            {"name": "appointment_requested", "type": "boolean", "description": "¿Pidió cita?"},
            {"name": "call_summary", "type": "string", "description": "Resumen breve de la llamada"},
        ],
        webhook_url=WEBHOOK_URL,
    )
    print(f"✅ Agente creado: {agent.agent_id}")

    print("\n📌 Guarda estos IDs en tu .env:")
    print(f"   RETELL_LLM_ID={llm.llm_id}")
    print(f"   RETELL_AGENT_ID={agent.agent_id}")


def update_prompt(client: Retell) -> None:
    if not RETELL_LLM_ID:
        print("❌ RETELL_LLM_ID no configurado en .env")
        sys.exit(1)
    print(f"\n── Actualizando system prompt del LLM {RETELL_LLM_ID}...")
    client.llm.update(RETELL_LLM_ID, general_prompt=SYSTEM_PROMPT)
    print("✅ Prompt actualizado")


def show_status(client: Retell) -> None:
    print("\n── Agentes:")
    agents = client.agent.list()
    for a in agents:
        print(f"  {a.agent_id} — {a.agent_name}")

    print("\n── Números de teléfono:")
    try:
        numbers = client.phone_number.list()
        for n in numbers:
            print(f"  {n.phone_number} → agente: {getattr(n, 'agent_id', '—')}")
    except Exception:
        print("  (sin números importados)")


def main():
    if not RETELL_API_KEY:
        print("❌ RETELL_API_KEY no configurada en .env")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true", help="Ver estado actual")
    parser.add_argument("--update", action="store_true", help="Actualizar system prompt")
    args = parser.parse_args()

    client = Retell(api_key=RETELL_API_KEY)

    if args.status:
        show_status(client)
    elif args.update:
        update_prompt(client)
    else:
        create_agent(client)


if __name__ == "__main__":
    main()
