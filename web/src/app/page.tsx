"use client";

import { useEffect, useState } from "react";

// ── Types ──────────────────────────────────────────────────────────────────────
interface Property {
  ref:               string;
  tipo:              string;
  operacion:         string;
  titulo:            string;
  calle?:            string;
  zona?:             string;
  precio:            number;
  precio_texto:      string;
  m2:                number;
  habitaciones:      number;
  banos:             number;
  descripcion_corta?: string;
  extras?:           string[] | string;
  url?:              string;
  destacado?:        boolean;
}

// URL de la API — en TSC es /nucleo/api/properties, en dev local es localhost:8010
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://tsc.tail8dce43.ts.net/nucleo";

const WA_NUMBER = "34663103334";

// ── Icons ──────────────────────────────────────────────────────────────────────
const PhoneIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
  </svg>
);

const WhatsAppIcon = () => (
  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.888-.788-1.489-1.761-1.663-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
  </svg>
);

const BedIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 4v16"/><path d="M2 8h18a2 2 0 0 1 2 2v10"/><path d="M2 17h20"/><path d="M6 8v9"/>
  </svg>
);

const BathIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 6 6.5 3.5a1.5 1.5 0 0 0-1-.5C4.683 3 4 3.683 4 4.5V17a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5"/>
    <line x1="10" y1="5" x2="8" y2="7"/><line x1="2" y1="12" x2="22" y2="12"/>
  </svg>
);

const RulerIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21.3 8.7 8.7 21.3c-1 1-2.5 1-3.4 0l-2.6-2.6c-1-1-1-2.5 0-3.4L15.3 2.7c1-1 2.5-1 3.4 0l2.6 2.6c1 1 1 2.5 0 3.4Z"/>
    <path d="m7.5 10.5 2 2"/><path d="m10.5 7.5 2 2"/><path d="m13.5 4.5 2 2"/><path d="m4.5 13.5 2 2"/>
  </svg>
);

// ── Colores por tipo de inmueble ───────────────────────────────────────────────
const TYPE_COLORS: Record<string, string> = {
  piso:   "#E6EDF7",
  atico:  "#FAEEDA",
  chalet: "#FAECE7",
  casa:   "#EAF3DE",
  local:  "#EEEDFE",
  otro:   "#E1F5EE",
};

const TYPE_LABELS: Record<string, string> = {
  piso:   "Piso",
  atico:  "Ático",
  chalet: "Chalet",
  casa:   "Casa",
  local:  "Local",
  otro:   "Inmueble",
};

// ── Property Card ─────────────────────────────────────────────────────────────
function PropertyCard({ prop }: { prop: Property }) {
  const [expanded, setExpanded] = useState(false);

  const extras: string[] = Array.isArray(prop.extras)
    ? prop.extras
    : typeof prop.extras === "string"
    ? (() => { try { return JSON.parse(prop.extras as string); } catch { return []; } })()
    : [];

  const waText = encodeURIComponent(
    `INMO Hola! Me interesa el ${prop.titulo} (${prop.precio_texto}). ¿Podéis darme más info?`
  );
  const bgColor = TYPE_COLORS[prop.tipo] || "#F5F5F5";
  const typeLabel = TYPE_LABELS[prop.tipo] || prop.tipo;

  return (
    <div className="bg-white rounded-2xl overflow-hidden border border-gray-100 hover:border-gray-200 transition-all duration-200 flex flex-col">
      {/* Image placeholder */}
      <div
        className="relative flex items-end p-3"
        style={{ height: 150, background: bgColor }}
      >
        <div className="absolute inset-0 flex items-center justify-center opacity-10">
          <svg viewBox="0 0 24 24" width="60" height="60" fill="none"
            stroke="#1B2A4A" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
            <polyline points="9 22 9 12 15 12 15 22"/>
          </svg>
        </div>
        <div className="flex items-center gap-2 relative z-10">
          <span className="text-xs font-semibold px-3 py-1 rounded-full"
            style={{ background: "rgba(27,42,74,0.85)", color: "#C9A84C" }}>
            {typeLabel}
          </span>
          {prop.destacado && (
            <span className="text-xs font-semibold px-3 py-1 rounded-full bg-amber-400 text-amber-900">
              Destacado
            </span>
          )}
        </div>
        <div className="absolute top-3 right-3">
          <span className="text-sm font-semibold bg-white px-3 py-1 rounded-xl border border-gray-100 text-gray-900">
            {prop.precio_texto}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 flex flex-col flex-1">
        <p className="text-xs text-gray-400 font-medium mb-1 uppercase tracking-wide">
          {prop.zona || "El Campello, Alicante"}
        </p>
        <h3 className="text-sm font-semibold text-gray-900 mb-3 leading-snug">
          {prop.titulo}
        </h3>

        {/* Specs */}
        <div className="flex items-center gap-3 text-xs text-gray-500 mb-3 bg-gray-50 px-3 py-2 rounded-lg">
          <span className="flex items-center gap-1"><RulerIcon />{prop.m2} m²</span>
          <span className="flex items-center gap-1"><BedIcon />{prop.habitaciones} hab.</span>
          <span className="flex items-center gap-1"><BathIcon />{prop.banos} {prop.banos === 1 ? "baño" : "baños"}</span>
        </div>

        {/* Tags */}
        {extras.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {extras.slice(0, 4).map((tag, i) => (
              <span key={i}
                className="text-xs px-2 py-0.5 rounded-full border"
                style={i === 0
                  ? { background: "#FDF8EE", color: "#7A5A1A", borderColor: "#E8D099" }
                  : { background: "#F9F9F9", color: "#666", borderColor: "#E5E5E5" }}>
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Descripcion */}
        {prop.descripcion_corta && (
          <p className={`text-xs text-gray-500 leading-relaxed mb-3 ${expanded ? "" : "line-clamp-2"}`}>
            {prop.descripcion_corta}
          </p>
        )}
        {prop.descripcion_corta && (
          <button onClick={() => setExpanded(!expanded)}
            className="text-xs text-gray-400 hover:text-gray-600 mb-3 text-left">
            {expanded ? "Ver menos" : "Ver más"}
          </button>
        )}

        {/* Actions */}
        <div className="flex gap-2 mt-auto pt-3 border-t border-gray-100">
          <a href={`https://wa.me/${WA_NUMBER}?text=${waText}`}
            target="_blank" rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-2 py-2 rounded-xl text-xs font-semibold text-white transition-all"
            style={{ background: "#25D366" }}>
            <WhatsAppIcon />Preguntar
          </a>
          <a href="tel:+34663103334"
            className="flex items-center justify-center w-10 h-9 rounded-xl border border-gray-200 text-gray-500 hover:bg-gray-50 transition-all">
            <PhoneIcon />
          </a>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function Home() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState<string | null>(null);
  const [filter,     setFilter]     = useState<"todos" | "piso" | "chalet" | "atico" | "casa">("todos");

  useEffect(() => {
    fetch(`${API_BASE}/api/properties`)
      .then((r) => {
        if (!r.ok) throw new Error(`API error ${r.status}`);
        return r.json();
      })
      .then((data) => {
        setProperties(data.properties || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Properties fetch error:", err);
        setError("No se pudieron cargar las propiedades.");
        setLoading(false);
      });
  }, []);

  const filtered = filter === "todos"
    ? properties
    : properties.filter((p) => p.tipo === filter);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
      {/* Navbar */}
      <nav className="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-100 sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center font-bold text-lg"
            style={{ background: "#1B2A4A", color: "#C9A84C" }}>N</div>
          <span className="text-xl font-extrabold tracking-tight text-gray-900">Núcleo</span>
        </div>
        <div className="hidden md:flex gap-6 text-sm font-medium text-gray-400">
          <a href="#" className="hover:text-gray-700 transition-colors">Comprar</a>
          <a href="#" className="hover:text-gray-700 transition-colors">Alquilar</a>
          <a href="#" className="hover:text-gray-700 transition-colors">Vender</a>
        </div>
        <a href={`https://wa.me/${WA_NUMBER}?text=${encodeURIComponent("INMO Hola! Quiero información sobre vuestras propiedades.")}`}
          target="_blank" rel="noopener noreferrer"
          className="px-5 py-2 text-sm font-bold text-white rounded-lg transition-colors"
          style={{ background: "#1B2A4A" }}>
          Contactar
        </a>
      </nav>

      {/* Hero */}
      <section className="px-6 py-14 text-center max-w-3xl mx-auto">
        <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-4 text-gray-900 leading-tight">
          Tu próximo hogar<br/>
          <span style={{ color: "#1B2A4A" }}>en El Campello</span>
        </h1>
        <p className="text-gray-500 text-lg mb-8">
          Asesoramiento personalizado · Financiación gratuita · 25 oficinas en Alicante
        </p>
        <a href={`https://wa.me/${WA_NUMBER}?text=${encodeURIComponent("INMO Hola! Quiero información sobre vuestras propiedades.")}`}
          target="_blank" rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-8 py-3 text-white font-bold rounded-xl text-base transition-all"
          style={{ background: "#25D366" }}>
          <WhatsAppIcon />Hablar con Lucía (IA)
        </a>
      </section>

      {/* Listings */}
      <section className="max-w-6xl mx-auto px-6 pb-20">
        {/* Header + Filters */}
        <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              {loading ? "Cargando..." : `${filtered.length} propiedades`}
            </h2>
            <p className="text-sm text-gray-400">El Campello, Alicante</p>
          </div>
          <div className="flex gap-2 flex-wrap">
            {(["todos", "piso", "atico", "chalet", "casa"] as const).map((f) => (
              <button key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-1.5 text-xs font-semibold rounded-full border transition-all ${
                  filter === f
                    ? "text-amber-800 border-amber-300"
                    : "text-gray-500 border-gray-200 bg-white hover:border-gray-300"
                }`}
                style={filter === f ? { background: "#FDF8EE", borderColor: "#E8D099" } : {}}>
                {f === "todos" ? "Todos" : f === "atico" ? "Áticos" : f.charAt(0).toUpperCase() + f.slice(1) + "s"}
              </button>
            ))}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="text-center py-16 text-gray-400">
            <p className="mb-2">{error}</p>
            <a href={`https://wa.me/${WA_NUMBER}`} target="_blank" rel="noopener noreferrer"
              className="text-sm underline" style={{ color: "#1B2A4A" }}>
              Contactar directamente
            </a>
          </div>
        )}

        {/* Loading skeleton */}
        {loading && !error && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-2xl overflow-hidden border border-gray-100 animate-pulse">
                <div className="h-36 bg-gray-100" />
                <div className="p-4 space-y-3">
                  <div className="h-3 bg-gray-100 rounded w-1/2" />
                  <div className="h-4 bg-gray-100 rounded w-3/4" />
                  <div className="h-3 bg-gray-100 rounded w-full" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Grid */}
        {!loading && !error && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((prop) => (
              <PropertyCard key={prop.ref} prop={prop} />
            ))}
          </div>
        )}

        {/* Empty */}
        {!loading && !error && filtered.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            No hay propiedades en esta categoría actualmente.
          </div>
        )}
      </section>
    </div>
  );
}
