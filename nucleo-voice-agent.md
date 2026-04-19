# 🏠 Agente de Voz IA — Inmobiliaria Núcleo
## Playa de San Juan, Alicante

---

## 1. Descripción del caso de uso

**Núcleo** es una inmobiliaria ubicada en la Playa de San Juan (Alicante). Recibe llamadas de potenciales compradores y arrendatarios que preguntan por pisos disponibles, precios, visitas y disponibilidad.

El agente de voz IA actúa como **recepcionista virtual 24/7** con las siguientes capacidades:

| Función | Descripción |
|---|---|
| 📞 Recibir llamadas entrantes | Responde en nombre de Núcleo con tono profesional y cercano |
| 🏡 Informar sobre propiedades | Responde preguntas sobre pisos: precio, metros, habitaciones, planta, terraza, parking |
| 📅 Agendar visitas | Recoge nombre, teléfono, franja horaria preferida y confirma la cita |
| 🔁 Transferir a humano | Si la consulta es compleja, transfiere la llamada a un agente real |
| 📋 Volcar datos al CRM | Al finalizar la llamada, envía nombre, teléfono, interés y cita via webhook |
| 📩 Notificación interna | Manda resumen de la llamada por email o Slack al equipo de Núcleo |

---

## 2. Arquitectura del sistema

```
Cliente llama al número de Núcleo (+34 XXX XXX XXX)
             │
             ▼
     [Fase demo]               [Fase producción]
  Número Retell/Twilio   ←→   Desvío SIP desde Vodafone/
  (temporal para test)        Orange/Movistar del cliente
             │
             ▼
      ┌─────────────┐
      │  Retell AI  │  ← Orquestador principal
      │  (cerebro)  │
      └──────┬──────┘
             │
     ┌───────┼───────────┐
     ▼       ▼           ▼
  LLM      ElevenLabs   Twilio/Telnyx
 (Claude   (voz IA      (telefonía)
  3.5/4)    realista)
             │
     ┌───────┼──────────────┐
     ▼       ▼              ▼
  Webhook  Google        Transferencia
  → CRM   Calendar/      a agente humano
  / Notion Cal.com       (+34 XXX XXX XXX)
```

---

## 3. APIs y credenciales necesarias

### 3.1 Tabla de credenciales

| Servicio | Variable | Dónde obtenerla | Coste estimado |
|---|---|---|---|
| **Retell AI** | `RETELL_API_KEY` | retellai.com → Settings → API Keys | $10 gratis al inicio |
| **ElevenLabs** | `ELEVENLABS_API_KEY` | elevenlabs.io → Profile → API Key | Free tier (15 min/mes) o Starter $5/mes |
| **Twilio** | `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` | twilio.com → Console | Ya tienes cuenta ✅ |
| **Twilio** | `TWILIO_PHONE_NUMBER` | Comprar número ES en Twilio Console | ~$1–2/mes número español |
| **LLM** | Incluido en Retell | Seleccionas Claude o GPT desde el dashboard | Incluido en el per/min |
| **CRM Webhook** | `WEBHOOK_URL` | Tu CRM (HubSpot, Notion, Airtable, etc.) | Depende del CRM |

### 3.2 Dónde guardar las variables

**Para la demo (local/VPS):**
```bash
# Archivo: /vault/.env  (también en .env del proyecto)

RETELL_API_KEY=key_xxxxxxxxxxxxxxxx
ELEVENLABS_API_KEY=sk_xxxxxxxxxxxxxxxx
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+34XXXXXXXXX
WEBHOOK_CRM_URL=https://tu-crm.com/webhook/nucleo
AGENT_TRANSFER_NUMBER=+34XXXXXXXXX   # Número del agente humano de Núcleo
```

**Para producción (VPS Nexus):**
```bash
# Añadir al /vault/.env del servidor
# Y al sistema de variables de entorno del servicio activo
```

---

## 4. Configuración del agente en Retell AI

### 4.1 Datos del agente

```yaml
Nombre del agente:  "Lucía - Núcleo Inmobiliaria"
Idioma:             Español (España)
Voz (ElevenLabs):  Voz femenina natural, tono cálido y profesional
                   → Recomendada: "Laura" o "Sofía" de ElevenLabs
Latencia objetivo:  < 800ms
LLM:               Claude 3.5 Sonnet (mejor para español y comprensión contextual)
```

### 4.2 System Prompt del agente

```
Eres Lucía, la asistente virtual de Núcleo Inmobiliaria, ubicada en la 
Playa de San Juan, Alicante. Tu misión es atender a los clientes que 
llaman interesados en comprar o alquilar pisos.

PERSONALIDAD:
- Amable, cercana y profesional
- Hablas en español neutro con naturalidad, no en tono robótico
- Eres concisa pero completa. No das información irrelevante
- Si no sabes algo, lo reconoces y ofreces que un agente se ponga en contacto

FLUJO DE LLAMADA:
1. Saluda: "Buenas, Núcleo Inmobiliaria, le atiende Lucía, ¿en qué puedo ayudarle?"
2. Identifica el interés: ¿compra o alquiler? ¿qué tipo de piso busca?
3. Informa sobre las propiedades disponibles (ver lista de pisos más abajo)
4. Si hay interés, recoge: nombre completo, teléfono de contacto, 
   franja horaria para visita
5. Confirma la cita o indica que el equipo le llamará para confirmarla
6. Cierra con amabilidad

REGLAS:
- Nunca inventes precios ni detalles que no estén en tu base de conocimiento
- Si preguntan por algo que no tienes: "Voy a dejar nota para que nuestro 
  equipo le llame con esa información"
- Si piden hablar con una persona: transfiere la llamada al +34 XXX XXX XXX
- Nunca digas que eres una IA a menos que te lo pregunten directamente

BASE DE CONOCIMIENTO DE PISOS:
[PENDIENTE — se añadirán fichas de propiedades en el paso 5]
```

### 4.3 Funciones del agente (Functions/Tools en Retell)

```json
[
  {
    "name": "transfer_to_human",
    "description": "Transfiere la llamada a un agente humano de Núcleo",
    "parameters": {}
  },
  {
    "name": "book_appointment",
    "description": "Registra una cita para visita de piso",
    "parameters": {
      "client_name": "string",
      "phone": "string",
      "property_id": "string",
      "preferred_time": "string"
    }
  },
  {
    "name": "send_lead_to_crm",
    "description": "Envía los datos del lead al CRM vía webhook al finalizar la llamada",
    "parameters": {
      "client_name": "string",
      "phone": "string",
      "interest": "string",
      "notes": "string"
    }
  }
]
```

---

## 5. Fichas de propiedades (pendiente de completar)

> ⏳ **Alberto nos enviará:** fotos, precios, m², habitaciones, planta, 
> parking, terraza y cualquier detalle relevante de cada piso.
> 
> Formato sugerido para cada propiedad:

```markdown
### Piso 01 — Ref. NUC-001
- **Ubicación:** Calle X, Playa de San Juan
- **Precio:** 250.000 € (venta) / 900 €/mes (alquiler)
- **Superficie:** 85 m²
- **Habitaciones:** 3
- **Baños:** 2
- **Planta:** 4ª con ascensor
- **Extras:** Terraza 12 m², parking incluido, piscina comunitaria
- **Disponibilidad:** Inmediata
- **Notas:** Vistas al mar parciales, orientación sur
```

---

## 6. Configuración de telefonía

### FASE 1 — Demo (número Retell/Twilio temporal)

1. En **Twilio Console** → comprar número español (+34 9XX o +34 6XX si disponible)
2. En **Retell Dashboard** → Phone Numbers → Import via SIP trunking
3. Configurar Twilio para enrutar llamadas a Retell:
   - En Twilio: el número apunta al SIP URI de Retell
   - `sip:+34XXXXXXXXX@sip.retellai.com`
4. Asignar el agente "Lucía" al número

**Tiempo estimado: 30–60 minutos**

### FASE 2 — Producción (número real de Núcleo)

```
Opción A — Desvío condicional (recomendada, sin cambiar nada):
  └─ En la centralita/operador de Núcleo:
       Configura desvío "cuando no contestan" o "fuera de horario"
       → al número de Twilio/Retell asignado al agente

Opción B — Desvío total (Retell responde siempre):
  └─ Desvío incondicional del número fijo de Núcleo al número Retell

Opción C — SIP trunk directo (más limpio, requiere operador VoIP):
  └─ Importar número de Núcleo directamente a Retell via SIP
     Compatible con: Zadarma, VoIPstudio, Fonvirtual, Telecor (España)
```

---

## 7. Webhook → CRM (al finalizar cada llamada)

Retell dispara un POST al finalizar la llamada con este payload:

```json
{
  "call_id": "call_abc123",
  "duration_seconds": 187,
  "transcript": "Buenas, Núcleo Inmobiliaria...",
  "custom_data": {
    "client_name": "Carlos Martínez",
    "phone": "+34 666 123 456",
    "interest": "Compra, 3 habitaciones, hasta 300.000€",
    "appointment": "Jueves 24 abril, mañana",
    "property_ref": "NUC-001"
  }
}
```

Destinos posibles para el webhook:
- **HubSpot** → crear contacto + nota de actividad automáticamente
- **Notion / Airtable** → añadir fila a tabla de leads
- **Google Sheets** → registro simple para demo
- **Email** → resumen de llamada al equipo de Núcleo
- **Slack** → notificación en canal #leads

---

## 8. Checklist de activación — paso a paso

```
[ ] 1. Crear cuenta en retellai.com
[ ] 2. Obtener RETELL_API_KEY → guardar en /vault/.env
[ ] 3. Obtener ELEVENLABS_API_KEY → guardar en /vault/.env
[ ] 4. En Twilio: comprar número español → anotar TWILIO_PHONE_NUMBER
[ ] 5. Conectar Twilio ↔ Retell via SIP trunking
[ ] 6. Crear agente "Lucía" en Retell con el system prompt de arriba
[ ] 7. Seleccionar voz ElevenLabs en el agente
[ ] 8. Añadir fichas de propiedades al knowledge base del agente
[ ] 9. Configurar webhook → CRM/Notion/Sheets
[ ] 10. Test: llamar al número desde móvil y verificar flujo completo
[ ] 11. Ajustar prompt según feedback de la demo
[ ] 12. [Fase 2] Configurar desvío desde número real de Núcleo
```

---

## 9. Costes estimados para la demo

| Concepto | Coste |
|---|---|
| Retell AI (crédito inicial) | **$0** (10$ gratis) |
| ElevenLabs (free tier) | **$0** (15 min/mes) |
| Twilio número ES | ~**$2/mes** |
| Twilio minutos de llamada | ~$0.013/min (telefonía) |
| **Total para demo** | **< $5** |
| **Total producción estimada** | ~$50–150/mes según volumen |

---

## 10. Próximos pasos

1. **Alberto envía:** fichas de pisos (precio, m², fotos, características)
2. Añadimos propiedades al knowledge base del agente
3. Grabamos test de llamada completa
4. Presentamos demo a Núcleo
5. Configuramos desvío de su número real (Fase 2)

---

*Documento generado por Alberto Lobo — NexusFinLabs*  
*Versión 1.0 — Abril 2026*
