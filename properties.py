"""
Núcleo Inmobiliaria — Catálogo de propiedades y comerciales.

Fuente de datos: Supabase (tabla `properties` + `comerciales`)
Fallback:        Lista local PROPERTIES_FALLBACK (dev offline)

Uso:
  python properties.py          → imprime catálogo activo
  python properties.py --sync   → recarga desde Supabase
"""

from __future__ import annotations

import json
import os
import sys
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL   = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY   = os.getenv("SUPABASE_KEY", "")
BUSINESS_SLUG  = os.getenv("BUSINESS_SLUG", "nucleo")


# ── Fallback local (dev sin conexión) ─────────────────────────────────────────

PROPERTIES_FALLBACK: list[dict] = [
    {"ref": "NUC-V01", "tipo": "piso",   "operacion": "venta",
     "titulo": "Piso en Calle LLauradors",     "zona": "El Campello, Alicante",
     "precio_texto": "210.000 €", "m2": 77,  "habitaciones": 3, "banos": 2,
     "descripcion_corta": "Piso reformado, 3 hab, 2 baños, ascensor y garaje incluido.",
     "extras": ["Ascensor", "Balcón", "Garaje incluido", "Reformado"],
     "comercial_slug": "carlos"},
    {"ref": "NUC-V02", "tipo": "atico",  "operacion": "venta",
     "titulo": "Piso en Carrer Sant Pere",     "zona": "El Campello, Alicante",
     "precio_texto": "499.000 €", "m2": 150, "habitaciones": 4, "banos": 3,
     "descripcion_corta": "Ático dúplex 150m², dos terrazas y vistas al mar.",
     "extras": ["Ascensor", "Terraza", "Ático dúplex", "Vistas al mar"],
     "comercial_slug": "carlos"},
    {"ref": "NUC-V03", "tipo": "chalet", "operacion": "venta",
     "titulo": "Casa en Avenida de la Creu",   "zona": "El Campello, Alicante",
     "precio_texto": "299.000 €", "m2": 120, "habitaciones": 4, "banos": 2,
     "descripcion_corta": "Chalet adosado reformado, 4 dorm, garaje y patio.",
     "extras": ["Terraza", "Garaje", "Reformado", "Patio"],
     "comercial_slug": "carlos"},
    {"ref": "NUC-V04", "tipo": "piso",   "operacion": "venta",
     "titulo": "Piso en el Centro",            "zona": "El Campello, Alicante",
     "precio_texto": "245.000 €", "m2": 143, "habitaciones": 3, "banos": 2,
     "descripcion_corta": "Piso 143m² céntrico, garaje, trastero y A/C por conductos.",
     "extras": ["Ascensor", "Balcón", "Garaje", "Trastero"],
     "comercial_slug": "carlos"},
    {"ref": "NUC-V05", "tipo": "piso",   "operacion": "venta",
     "titulo": "Piso en Avenida Ausias March", "zona": "El Campello, Alicante",
     "precio_texto": "289.000 €", "m2": 96,  "habitaciones": 3, "banos": 2,
     "descripcion_corta": "Piso con vistas al mar, urb. con piscina, gimnasio y SPA.",
     "extras": ["Piscina comunitaria", "Gimnasio", "SPA", "Garaje", "Vistas al mar"],
     "comercial_slug": "carlos"},
    {"ref": "NUC-V06", "tipo": "piso",   "operacion": "venta",
     "titulo": "Piso de 1 Dormitorio a estrenar!", "zona": "El Campello, Alicante",
     "precio_texto": "158.000 €", "m2": 75,  "habitaciones": 1, "banos": 1,
     "descripcion_corta": "Piso a estrenar, última planta con terraza privada +30m².",
     "extras": ["Ascensor", "Terraza privada +30m²", "A estrenar", "Última planta"],
     "comercial_slug": "carlos"},
]

AGENTS_FALLBACK: dict[str, dict] = {
    "carlos":  {"nombre": "Carlos",  "telefono": "+34623343056"},
    "loreto":  {"nombre": "Loreto",  "telefono": "+34633103334"},
    "antonio": {"nombre": "Antonio", "telefono": "+34633103334"},
    "fran":    {"nombre": "Fran",    "telefono": "+34633103334"},
    "pablo":   {"nombre": "Pablo",   "telefono": "+34633103334"},
}


# ── Carga desde Supabase ───────────────────────────────────────────────────────

def _fetch_from_supabase() -> tuple[list[dict], dict[str, dict]]:
    from supabase import create_client
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    biz = (
        client.table("businesses")
        .select("id")
        .eq("slug", BUSINESS_SLUG)
        .single()
        .execute()
    )
    business_id = biz.data["id"]

    props = (
        client.table("properties")
        .select("*")
        .eq("business_id", business_id)
        .eq("activo", True)
        .order("precio")
        .execute()
    ).data

    agents_rows = (
        client.table("comerciales")
        .select("*")
        .eq("business_id", business_id)
        .eq("activo", True)
        .execute()
    ).data

    agents = {
        a["slug"]: {
            "nombre": a["nombre"],
            "telefono": a.get("telefono", ""),
            "email": a.get("email", ""),
        }
        for a in agents_rows
    }
    return props, agents


@lru_cache(maxsize=1)
def _load_catalog() -> tuple[list[dict], dict[str, dict]]:
    """Carga el catálogo una vez por proceso. Usa Supabase o fallback local."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[properties] Sin Supabase — fallback local", file=sys.stderr)
        return PROPERTIES_FALLBACK, AGENTS_FALLBACK
    try:
        props, agents = _fetch_from_supabase()
        print(f"[properties] {len(props)} propiedades desde Supabase ✓", file=sys.stderr)
        return props, agents
    except Exception as exc:
        print(f"[properties] Error Supabase ({exc}) — fallback local", file=sys.stderr)
        return PROPERTIES_FALLBACK, AGENTS_FALLBACK


def invalidate_cache() -> None:
    """Fuerza recarga en la próxima llamada (útil tras actualizar propiedades)."""
    _load_catalog.cache_clear()


# ── API pública ────────────────────────────────────────────────────────────────

def get_properties() -> list[dict]:
    props, _ = _load_catalog()
    return props


def get_agents() -> dict[str, dict]:
    _, agents = _load_catalog()
    return agents


def get_properties_summary() -> str:
    """
    Bloque de texto para el system prompt de Lucía.
    Compacto para no inflar el contexto del LLM.
    """
    props = get_properties()
    if not props:
        return "No hay propiedades disponibles. El equipo contactará al cliente."

    lines = []
    for p in props:
        op = "ALQUILER" if p.get("operacion") == "alquiler" else "VENTA"
        extras_raw = p.get("extras") or []
        if isinstance(extras_raw, str):
            try:
                extras_raw = json.loads(extras_raw)
            except Exception:
                extras_raw = []
        extras = ", ".join(extras_raw[:4]) if extras_raw else "—"
        desc = p.get("descripcion_corta") or ""
        lines.append(
            f"[{p['ref']}] {op} · {p.get('titulo','')} · {p.get('zona','')} · "
            f"{p.get('m2','')}m² · {p.get('habitaciones','')} hab · {p.get('banos','')} baños · "
            f"Precio: {p.get('precio_texto','')} · Extras: {extras}"
            + (f" | {desc}" if desc else "")
        )
    return "\n".join(lines)


def find_property(ref: str) -> dict | None:
    ref_clean = ref.strip().upper()
    for p in get_properties():
        if str(p.get("ref", "")).upper() == ref_clean:
            return p
    return None


def get_agent_for_property(ref: str) -> dict | None:
    prop = find_property(ref)
    if not prop:
        return None
    return get_agents().get(prop.get("comercial_slug", ""))


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--sync" in sys.argv:
        invalidate_cache()
        print("Recargando desde Supabase...\n")

    props = get_properties()
    agents = get_agents()

    print("=== Catálogo activo ===")
    print(get_properties_summary())
    print(f"\nTotal: {len(props)} propiedades")
    for op in ("alquiler", "venta"):
        n = sum(1 for p in props if p.get("operacion") == op)
        if n:
            print(f"  {op}: {n}")

    print("\n=== Comerciales ===")
    for slug, agent in agents.items():
        assigned = [p["ref"] for p in props if p.get("comercial_slug") == slug]
        print(f"  {agent['nombre']} ({slug}): {', '.join(assigned) or '—'}")
