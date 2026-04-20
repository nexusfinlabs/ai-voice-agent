"""
properties.py — Catálogo Nucleo Inmobiliaria
─────────────────────────────────────────────
Fuente primaria: Supabase tabla properties (si disponible).
Fallback local: PROPERTIES_FALLBACK con coordenadas reales El Campello.
"""
import os
from typing import Any

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
BUSINESS_SLUG = os.getenv("BUSINESS_SLUG", "nucleo")

AGENT_WA = os.getenv("AGENT_TRANSFER_NUMBER", "+34663103334")


# ── Fallback local (dev sin conexion) ─────────────────────────────────────────

PROPERTIES_FALLBACK: list[dict] = [
    {"ref": "NUC-V01", "tipo": "piso",   "operacion": "venta",
     "titulo": "Piso en Calle LLauradors",     "zona": "El Campello, Alicante",
     "precio_texto": "210.000 €", "m2": 77,  "habitaciones": 3, "banos": 2,
     "descripcion_corta": "Piso reformado, 3 hab, 2 baños, ascensor y garaje incluido.",
     "extras": ["Ascensor", "Balcón", "Garaje incluido", "Reformado"],
     "comercial_slug": "loreto",
     "lat": 38.42614, "lng": -0.39461,
     "fotos": [
       "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800&q=80",
       "https://images.unsplash.com/photo-1560448204-603b3fc33ddc?w=800&q=80",
       "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800&q=80",
     ]},
    {"ref": "NUC-V02", "tipo": "atico",  "operacion": "venta",
     "titulo": "Piso en Carrer Sant Pere",     "zona": "El Campello, Alicante",
     "precio_texto": "499.000 €", "m2": 150, "habitaciones": 4, "banos": 3,
     "descripcion_corta": "Ático dúplex 150m², dos terrazas y vistas al mar.",
     "extras": ["Ascensor", "Terraza", "Ático dúplex", "Vistas al mar"],
     "comercial_slug": "antonio",
     "lat": 38.42883, "lng": -0.39245,
     "fotos": [
       "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&q=80",
       "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&q=80",
       "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800&q=80",
     ]},
    {"ref": "NUC-V03", "tipo": "chalet", "operacion": "venta",
     "titulo": "Casa en Avenida de la Creu",   "zona": "El Campello, Alicante",
     "precio_texto": "299.000 €", "m2": 120, "habitaciones": 4, "banos": 2,
     "descripcion_corta": "Chalet adosado reformado, 4 dorm, garaje y patio.",
     "extras": ["Terraza", "Garaje", "Reformado", "Patio"],
     "comercial_slug": "fran",
     "lat": 38.42445, "lng": -0.40012,
     "fotos": [
       "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800&q=80",
       "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=800&q=80",
       "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&q=80",
     ]},
    {"ref": "NUC-V04", "tipo": "piso",   "operacion": "venta",
     "titulo": "Piso en el Centro",            "zona": "El Campello, Alicante",
     "precio_texto": "245.000 €", "m2": 143, "habitaciones": 3, "banos": 2,
     "descripcion_corta": "Piso 143m² céntrico, garaje, trastero y A/C por conductos.",
     "extras": ["Ascensor", "Balcón", "Garaje", "Trastero"],
     "comercial_slug": "loreto",
     "lat": 38.42760, "lng": -0.39587,
     "fotos": [
       "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=800&q=80",
       "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800&q=80",
       "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800&q=80",
     ]},
    {"ref": "NUC-V05", "tipo": "piso",   "operacion": "venta",
     "titulo": "Piso en Avenida Ausias March", "zona": "El Campello, Alicante",
     "precio_texto": "289.000 €", "m2": 96,  "habitaciones": 3, "banos": 2,
     "descripcion_corta": "Piso con vistas al mar, urb. con piscina, gimnasio y SPA.",
     "extras": ["Piscina comunitaria", "Gimnasio", "SPA", "Garaje", "Vistas al mar"],
     "comercial_slug": "antonio",
     "lat": 38.43105, "lng": -0.39892,
     "fotos": [
       "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800&q=80",
       "https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?w=800&q=80",
       "https://images.unsplash.com/photo-1560185007-cde436f6a4d0?w=800&q=80",
     ]},
    {"ref": "NUC-V06", "tipo": "piso",   "operacion": "venta",
     "titulo": "Piso de 1 Dormitorio a estrenar!", "zona": "El Campello, Alicante",
     "precio_texto": "158.000 €", "m2": 75,  "habitaciones": 1, "banos": 1,
     "descripcion_corta": "Piso a estrenar, última planta con terraza privada +30m².",
     "extras": ["Ascensor", "Terraza privada +30m²", "A estrenar", "Última planta"],
     "comercial_slug": "pablo",
     "lat": 38.42520, "lng": -0.39105,
     "fotos": [
       "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800&q=80&sig=6",
       "https://images.unsplash.com/photo-1598928506311-c55ded91a20c?w=800&q=80",
       "https://images.unsplash.com/photo-1501183638710-841dd1904471?w=800&q=80",
     ]},
]

AGENTS_FALLBACK: dict[str, dict] = {
    "carlos":  {"nombre": "Carlos",  "telefono": "+34623343056"},
    "loreto":  {"nombre": "Loreto",  "telefono": AGENT_WA},
    "antonio": {"nombre": "Antonio", "telefono": AGENT_WA},
    "fran":    {"nombre": "Fran",    "telefono": AGENT_WA},
    "pablo":   {"nombre": "Pablo",   "telefono": AGENT_WA},
}


def _supabase_client():
    if not (SUPABASE_URL and SUPABASE_KEY):
        return None
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"[properties] Error Supabase ({e}) — fallback local")
        return None


def load_properties() -> tuple[list[dict], dict[str, dict]]:
    """Devuelve (propiedades, agentes). Intenta Supabase; si falla, fallback."""
    client = _supabase_client()
    if client is None:
        return PROPERTIES_FALLBACK, _enriquecer_agentes(AGENTS_FALLBACK, PROPERTIES_FALLBACK)

    try:
        # Propiedades del tenant actual
        resp = (
            client.table("properties")
            .select("*")
            .eq("business_slug", BUSINESS_SLUG)
            .execute()
        )
        props = resp.data or []
        if not props:
            print("[properties] Supabase sin filas — usando fallback")
            return PROPERTIES_FALLBACK, _enriquecer_agentes(AGENTS_FALLBACK, PROPERTIES_FALLBACK)

        # Agentes
        ag_resp = (
            client.table("agents")
            .select("*")
            .eq("business_slug", BUSINESS_SLUG)
            .execute()
        )
        ag_rows = ag_resp.data or []
        agentes = {
            a["slug"]: {"nombre": a["nombre"], "telefono": a.get("telefono", "")}
            for a in ag_rows
        }
        if not agentes:
            agentes = AGENTS_FALLBACK
        return props, _enriquecer_agentes(agentes, props)
    except Exception as e:
        print(f"[properties] Error leyendo Supabase ({e}) — fallback")
        return PROPERTIES_FALLBACK, _enriquecer_agentes(AGENTS_FALLBACK, PROPERTIES_FALLBACK)


def _enriquecer_agentes(agentes: dict, props: list[dict]) -> dict:
    """Añade campo 'assigned' (refs) a cada agente."""
    out = {}
    for slug, a in agentes.items():
        assigned = [p["ref"] for p in props if p.get("comercial_slug") == slug]
        out[slug] = {
            "nombre": a["nombre"],
            "telefono": a.get("telefono", ""),
            "assigned": assigned,
        }
    return out


def search_properties(**filters: Any) -> list[dict]:
    """Búsqueda simple en memoria para la function-call del agente Retell."""
    props, _ = load_properties()
    ops = filters.get("operacion")
    tipo = filters.get("tipo")
    max_precio = filters.get("precio_max")
    habs_min = filters.get("habitaciones_min")

    def _precio_num(s: str) -> int:
        return int("".join(c for c in s if c.isdigit()) or 0)

    out = []
    for p in props:
        if ops and p.get("operacion") != ops:
            continue
        if tipo and p.get("tipo") != tipo:
            continue
        if max_precio and _precio_num(p.get("precio_texto", "")) > max_precio:
            continue
        if habs_min and p.get("habitaciones", 0) < habs_min:
            continue
        out.append(p)
    return out




# ── Alias retrocompatibles ────────────────────────────────────────────────────
def get_properties() -> list[dict]:
    """Alias retrocompatible: devuelve solo la lista de propiedades."""
    props, _ = load_properties()
    return props


def get_agents() -> dict[str, dict]:
    """Alias retrocompatible: devuelve solo los agentes enriquecidos."""
    _, agentes = load_properties()
    return agentes


def get_properties_summary() -> str:
    """Resumen en texto plano del catalogo para inyectar en el prompt del LLM Retell.
    Formato: una linea por propiedad con los campos relevantes para la voz.
    """
    props, _ = load_properties()
    if not props:
        return "(No hay propiedades disponibles actualmente)"
    lines = []
    for p in props:
        extras = ", ".join(p.get("extras", [])) or "—"
        lines.append(
            f'[{p["ref"]}] {p["titulo"]} ({p["zona"]}) · '
            f'{p["precio_texto"]} · {p.get("habitaciones","?")} hab · '
            f'{p.get("banos","?")} ban · {p.get("m2","?")}m² · '
            f'Extras: {extras} · '
            f'Contacto: {p.get("comercial_slug","?")}'
        )
    return "\n".join(lines)


if __name__ == "__main__":
    props, agentes = load_properties()
    print(f"  {len(props)} propiedades | {len(agentes)} agentes")
    for p in props:
        print(f"  [{p['ref']}] {p['titulo']} - {p['precio_texto']}  ({p.get('lat')},{p.get('lng')})")
    for slug, agent in agentes.items():
        assigned = agent.get("assigned", [])
        print(f"  {agent['nombre']} ({slug}): {', '.join(assigned) or '—'}")
