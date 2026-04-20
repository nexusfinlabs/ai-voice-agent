"""
build_page.py — Genera index.html leyendo propiedades de Supabase.
Estilo: rojo/blanco Nucleo (#9b111e) - identico al diseno original.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from properties import get_properties, get_agents

WA_NUMBER = "34663103334"
PHONE_TEL = "+34919934651"


def build_js_properties(props):
    items = []
    for p in props:
        ref   = p.get("ref", "")
        op    = "Venta" if p.get("operacion") == "venta" else "Alquiler"
        ag    = p.get("comercial_slug", "carlos")
        title = (p.get("titulo") or "").replace('"', "'")
        zona  = p.get("zona", "El Campello, Alicante")
        calle = (p.get("calle") or "").replace('"', "'")
        pr    = p.get("precio_texto", "")
        m2    = p.get("m2", 0)
        hab   = p.get("habitaciones", 0)
        ban   = p.get("banos", 0)
        planta = (p.get("planta") or "").replace('"', "'")

        extras_raw = p.get("extras") or []
        if isinstance(extras_raw, str):
            try:    extras_raw = json.loads(extras_raw)
            except: extras_raw = []
        extras = extras_raw[:6]

        desc = (p.get("descripcion") or p.get("descripcion_corta") or "").replace('"', "'").replace("\n", " ")
        lat  = p.get("lat") or 38.4356
        lng  = p.get("lng") or -0.4036
        url  = p.get("url") or ""

        # Fotos: usa p["fotos"] si existe, sino fallback generico
        photos = p.get("fotos") or [
            f"https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=700&q=75&v={ref}",
            f"https://images.unsplash.com/photo-1484154218962-a197022b5858?w=700&q=75&v={ref}",
            f"https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=700&q=75&v={ref}",
        ]

        items.append(
            f'{{ref:"{ref}",op:"{op}",ag:"{ag}",t:"{title}",zona:"{zona}",calle:"{calle}",'
            f'pr:"{pr}",m2:{m2},hab:{hab},ban:{ban},pl:"{planta}",'
            f'ex:{json.dumps(extras, ensure_ascii=False)},desc:"{desc}",'
            f'lat:{lat},lng:{lng},url:"{url}",f:{json.dumps(photos)}}}'
        )
    return ",\n".join(items)


def build_js_agents(agents):
    COLORS = {
        "carlos":  "#9b111e",
        "loreto":  "#9b111e",
        "antonio": "#1a3a6b",
        "fran":    "#1a6b3a",
        "pablo":   "#8b5e1a",
    }
    items = []
    for slug, a in agents.items():
        nombre = a.get("nombre", slug.capitalize())
        color  = COLORS.get(slug, "#9b111e")
        items.append(f'"{slug}":{{n:"{nombre}",c:"{color}"}}')
    return "{" + ",".join(items) + "}"


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Nucleo Inmobiliaria — El Campello</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;utf8,<svg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 64 64%27><rect width=%2764%27 height=%2764%27 fill=%27%23ffffff%27/><text x=%2732%27 y=%2746%27 font-family=%27Arial Black,Arial,sans-serif%27 font-size=%2448%27 font-weight=%27900%27 text-anchor=%27middle%27 fill=%27%239b111e%27>N</text></svg>"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,-apple-system,sans-serif;height:100dvh;overflow:hidden;display:flex;flex-direction:column;background:#fff}
nav{display:flex;align-items:center;justify-content:space-between;padding:12px 20px;background:#fff;border-bottom:1px solid #eee;box-shadow:0 1px 4px rgba(0,0,0,.06);flex-shrink:0;z-index:600}
.logo{display:flex;align-items:center;gap:8px}
.lbadge{width:36px;height:36px;background:#9b111e;color:#fff;font-weight:900;font-size:18px;border-radius:8px;display:flex;align-items:center;justify-content:center}
.ltxt{font-weight:900;font-size:18px;letter-spacing:-.5px;color:#111}
.filters{display:flex;gap:4px;background:#f0f0f0;border-radius:10px;padding:4px}
.fb{padding:5px 14px;border-radius:7px;border:none;font-size:13px;font-weight:600;cursor:pointer;background:transparent;color:#555}
.fb.on{background:#9b111e;color:#fff}
#cbtn{display:flex;align-items:center;gap:6px;padding:9px 16px;background:#9b111e;color:#fff;border:none;border-radius:10px;font-size:13px;font-weight:700;cursor:pointer}
#cbtn:hover{background:#7a0e18}
.layout{display:flex;flex:1;min-height:0}
.side{width:400px;flex-shrink:0;overflow-y:auto;background:#f5f5f5;border-right:1px solid #e8e8e8}
.sbin{padding:12px;display:flex;flex-direction:column;gap:10px}
.slbl{font-size:11px;font-weight:700;color:#aaa;letter-spacing:.08em;text-transform:uppercase}
.card{background:#fff;border-radius:14px;overflow:hidden;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.06);transition:all .2s}
.card:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(0,0,0,.1)}
.card.sel{box-shadow:0 0 0 2.5px #9b111e,0 6px 18px rgba(0,0,0,.1);transform:translateY(-2px)}
.ci{position:relative;height:160px;overflow:hidden;background:#ddd}
.ci img{width:100%;height:100%;object-fit:cover;transition:transform .5s;display:block}
.card:hover .ci img,.card.sel .ci img{transform:scale(1.05)}
.ov{position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.4),transparent)}
.bop{position:absolute;top:9px;left:9px;padding:3px 9px;border-radius:5px;font-size:11px;font-weight:700;color:#fff}
.bref{position:absolute;top:9px;right:9px;padding:3px 7px;border-radius:5px;font-size:10px;font-weight:700;color:#fff;background:rgba(0,0,0,.5);font-family:monospace}
.bag{position:absolute;bottom:9px;left:9px;display:flex;align-items:center;gap:5px}
.adot{width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-size:9px;font-weight:900;border:2px solid rgba(255,255,255,.8)}
.anm{font-size:11px;font-weight:600;color:#fff;text-shadow:0 1px 3px rgba(0,0,0,.6)}
.cb{padding:12px}
.cloc{font-size:11px;color:#999;margin-bottom:3px}
.ctit{font-size:13px;font-weight:700;color:#111;margin-bottom:7px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cst{display:flex;gap:12px;font-size:11px;color:#777;background:#f8f8f8;padding:6px 9px;border-radius:7px;margin-bottom:9px}
.cft{display:flex;align-items:center;justify-content:space-between}
.cpr{font-size:15px;font-weight:900}
.cac{display:flex;gap:6px}
.abtn{width:32px;height:32px;border-radius:7px;border:none;display:flex;align-items:center;justify-content:center;cursor:pointer;text-decoration:none;transition:all .2s}
.wa{background:#e8f9ef;color:#25D366}
.wa:hover{background:#25D366;color:#fff}
.ph{background:#fbeaea;color:#9b111e}
.ph:hover{background:#9b111e;color:#fff}
.mapw{flex:1;position:relative}
#map{width:100%;height:100%}
.leg{position:absolute;top:12px;left:12px;background:#fff;border-radius:12px;padding:11px 13px;box-shadow:0 4px 14px rgba(0,0,0,.12);z-index:400}
.lt{font-size:10px;font-weight:700;color:#aaa;text-transform:uppercase;letter-spacing:.08em;margin-bottom:7px}
.lr{display:flex;align-items:center;gap:7px;margin-bottom:4px}
.ld{width:19px;height:19px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-size:9px;font-weight:900}
.ll{font-size:12px;font-weight:600;color:#444;flex:1}
.lc{font-size:10px;color:#aaa}
.det{position:absolute;top:0;right:0;height:100%;width:390px;background:#fff;box-shadow:-4px 0 28px rgba(0,0,0,.12);z-index:450;overflow-y:auto;transform:translateX(100%);transition:transform .28s cubic-bezier(.4,0,.2,1)}
.det.open{transform:translateX(0)}
.dg{position:relative;height:230px;background:#ddd}
.dg img{width:100%;height:100%;object-fit:cover;display:block}
.dgov{position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.45),transparent)}
.xbtn{position:absolute;top:10px;right:10px;width:32px;height:32px;background:rgba(0,0,0,.45);border:none;border-radius:50%;color:#fff;font-size:16px;cursor:pointer;display:flex;align-items:center;justify-content:center}
.xbtn:hover{background:rgba(0,0,0,.7)}
.gnav{position:absolute;top:50%;transform:translateY(-50%);background:rgba(0,0,0,.4);border:none;color:#fff;width:28px;height:28px;border-radius:50%;cursor:pointer;font-size:18px;display:flex;align-items:center;justify-content:center}
.gnav:hover{background:rgba(0,0,0,.7)}
.gp{left:8px}.gn{right:8px}
.gdots{position:absolute;bottom:9px;left:50%;transform:translateX(-50%);display:flex;gap:5px}
.dot{height:5px;border-radius:3px;cursor:pointer;transition:all .2s;background:rgba(255,255,255,.5)}
.dot.on{background:#fff;width:16px}.dot:not(.on){width:5px}
.dbg{position:absolute;bottom:16px;left:10px;display:flex;gap:5px}
.dbody{padding:16px}
.dpr{font-size:21px;font-weight:900}
.dpl{font-size:11px;color:#999;float:right;margin-top:5px}
.dtit{font-size:15px;font-weight:700;clear:both;margin-bottom:3px}
.dloc{font-size:12px;color:#777;margin-bottom:12px}
.dst{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-bottom:12px}
.ds{background:#f7f7f7;border-radius:9px;padding:9px;text-align:center}
.dsv{font-size:14px;font-weight:900;color:#111}
.dsl{font-size:10px;color:#aaa;margin-top:1px}
.sec{font-size:10px;font-weight:700;color:#aaa;text-transform:uppercase;letter-spacing:.08em;margin-bottom:7px}
.ddesc{font-size:13px;color:#555;line-height:1.6;margin-bottom:13px}
.chips{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:13px}
.chip{padding:4px 10px;border-radius:18px;font-size:11px;font-weight:600}
.agc{border-radius:12px;padding:11px;margin-bottom:13px;display:flex;align-items:center;gap:10px}
.agav{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-size:17px;font-weight:900;flex-shrink:0}
.agn{font-weight:700;font-size:14px}
.ags{font-size:11px;color:#999}
.ctarow{display:flex;gap:8px;position:sticky;bottom:0;background:#fff;padding:9px 0 3px}
.ctabtn{flex:1;display:flex;align-items:center;justify-content:center;gap:6px;padding:12px;border-radius:11px;border:none;font-size:13px;font-weight:700;cursor:pointer;text-decoration:none;color:#fff}
.ctabtn:hover{opacity:.88}
.nucleo-marker{background:transparent!important;border:none!important}
.nucleo-marker svg{filter:drop-shadow(0 2px 4px rgba(0,0,0,.3));transition:transform .15s;cursor:pointer}
.nucleo-marker:hover svg{transform:translateY(-3px) scale(1.1)}
.leaflet-control-zoom{border-radius:10px!important;overflow:hidden;border:none!important;box-shadow:0 3px 10px rgba(0,0,0,.15)!important}
.leaflet-control-zoom a{border:none!important;color:#333!important}
.leaflet-control-zoom a:hover{background:#f5f5f5!important;color:#9b111e!important}
@media(max-width:768px){.side{display:none}.det{width:100%}}
</style>
</head>
<body>
<nav>
  <div class="logo"><div class="lbadge">N</div><span class="ltxt">NUCLEO</span></div>
  <div class="filters">
    <button class="fb on" onclick="setF('Todos')">Todos</button>
    <button class="fb" onclick="setF('Venta')">Venta</button>
    <button class="fb" onclick="setF('Alquiler')">Alquiler</button>
  </div>
  <button id="cbtn" onclick="startCall()">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
    <span id="ctxt">Hablar con Inmobiliaria</span>
  </button>
</nav>
<div class="layout">
  <div class="side"><div class="sbin" id="cards"></div></div>
  <div class="mapw">
    <div id="map"></div>
    <div class="leg" id="leg"></div>
    <div class="det" id="det">
      <div class="dg">
        <img id="dimg" src="" alt=""/>
        <div class="dgov"></div>
        <button class="xbtn" onclick="closeD()">&#x2715;</button>
        <button class="gnav gp" onclick="prevP()">&#8249;</button>
        <button class="gnav gn" onclick="nextP()">&#8250;</button>
        <div class="gdots" id="gdots"></div>
        <div class="dbg" id="dbg"></div>
      </div>
      <div class="dbody" id="dbody"></div>
    </div>
  </div>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<script src="https://cdn.jsdelivr.net/npm/retell-client-js-sdk/dist/index.umd.js"></script>
<script>
var WA='<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.888-.788-1.489-1.761-1.663-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>';
var PH='<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>';
var WA_NUM="__WA_NUMBER__";
var PHONE="__PHONE_TEL__";
var AG=__AG_JS__;
var PP=[__PP_JS__];
var filt="Todos",sel=null,photo=0,mp,MK={},inCall=false,rc=null;
function pin(c,b){return'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="42" viewBox="0 0 32 42"><filter id="s'+b+'"><feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="rgba(0,0,0,.3)"/></filter><path d="M16 2C9.37 2 4 7.37 4 14c0 9.63 12 26 12 26S28 23.63 28 14C28 7.37 22.63 2 16 2z" fill="'+c+'" filter="url(#s'+b+')"/><circle cx="16" cy="14" r="7.5" fill="white" opacity=".92"/><text x="16" y="18" text-anchor="middle" font-family="system-ui" font-weight="800" font-size="9" fill="'+c+'">'+b+'</text></svg>';}
function fp(){return filt==="Todos"?PP:PP.filter(function(p){return p.op===filt;});}
function setF(f){filt=f;document.querySelectorAll(".fb").forEach(function(b){b.classList.toggle("on",b.textContent===f);});render();updMk();}
function render(){
  var list=fp();
  var c=document.getElementById("cards");
  c.innerHTML='<p class="slbl">'+list.length+' resultado'+(list.length!==1?'s':'')+'</p>';
  list.forEach(function(p){
    var a=AG[p.ag]||{n:"N",c:"#9b111e"},act=sel===p.ref;
    var waMsg=encodeURIComponent("INMO Hola, me interesa "+p.ref+" "+p.t+" ("+p.pr+"). Podeis darme info?");
    var wa="https://wa.me/"+WA_NUM+"?text="+waMsg;
    var el=document.createElement("div");
    el.className="card"+(act?" sel":"");el.id="c-"+p.ref;
    el.innerHTML='<div class="ci"><img src="'+p.f[0]+'" loading="lazy" alt="" onerror="this.style.display=\'none\'"/><div class="ov"></div>'
      +'<span class="bop" style="background:'+(p.op==="Venta"?"#9b111e":"#1a3a6b")+'">'+p.op+'</span>'
      +'<span class="bref">'+p.ref+'</span>'
      +'<div class="bag"><div class="adot" style="background:'+a.c+'">'+a.n[0]+'</div><span class="anm">'+a.n+'</span></div></div>'
      +'<div class="cb"><p class="cloc">'+p.zona+'</p><p class="ctit">'+p.t+'</p>'
      +'<div class="cst"><span>'+p.hab+' hab</span><span>'+p.ban+' ban</span><span>'+p.m2+'m2</span></div>'
      +'<div class="cft"><span class="cpr" style="color:'+a.c+'">'+p.pr+'</span>'
      +'<div class="cac">'
      +'<a class="abtn wa" href="'+wa+'" target="_blank" rel="noopener" onclick="event.stopPropagation()">'+WA+'</a>'
      +'<a class="abtn ph" href="tel:'+PHONE+'" onclick="event.stopPropagation()">'+PH+'</a>'
      +'</div></div></div>';
    el.addEventListener("click",function(){pick(p);});
    c.appendChild(el);
  });
}
function legend(){
  var d=document.getElementById("leg");
  var rows=Object.entries(AG).map(function(e){
    var k=e[0],a=e[1];
    var n=PP.filter(function(p){return p.ag===k;}).length;
    if(!n)return "";
    return '<div class="lr"><div class="ld" style="background:'+a.c+'">'+a.n[0]+'</div><span class="ll">'+a.n+'</span><span class="lc">'+n+'</span></div>';
  }).filter(Boolean).join("");
  d.innerHTML='<div class="lt">Comerciales</div>'+rows;
}
function initMap(){
  mp=L.map("map",{center:[38.4275,-0.3955],zoom:15,zoomControl:false});
  L.control.zoom({position:"bottomright"}).addTo(mp);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",{attribution:"CARTO",maxZoom:19}).addTo(mp);
  PP.forEach(function(p,i){
    var a=AG[p.ag]||{n:"N",c:"#9b111e"};
    // Si no hay coords, distribuir alrededor de El Campello centro
    var lat=p.lat||(38.4356+(i-3)*0.003);
    var lng=p.lng||(-0.4036+(i-3)*0.004);
    var ic=L.divIcon({html:pin(a.c,a.n[0]),className:"nucleo-marker",iconSize:[32,42],iconAnchor:[16,42]});
    var m=L.marker([lat,lng],{icon:ic}).addTo(mp);
    m.on("click",function(){pick(p);});
    MK[p.ref]=m;
  });
}
function updMk(){
  var refs=new Set(fp().map(function(p){return p.ref;}));
  PP.forEach(function(p){var m=MK[p.ref];if(!m)return;if(refs.has(p.ref)){if(!mp.hasLayer(m))m.addTo(mp);}else{if(mp.hasLayer(m))mp.removeLayer(m);}});
}
function pick(p){sel=p.ref;photo=0;render();var lat=p.lat||38.4356,lng=p.lng||-0.4036;mp.flyTo([lat,lng],15,{animate:true,duration:0.7});openD(p);}
function openD(p){
  var a=AG[p.ag]||{n:"N",c:"#9b111e"};photo=0;
  document.getElementById("dimg").src=p.f[0];
  var dots=p.f.map(function(_,i){return '<div class="dot'+(i===0?' on':'')+'" onclick="setP('+i+')"></div>';}).join("");
  document.getElementById("gdots").innerHTML=dots;
  document.getElementById("dbg").innerHTML='<span class="bop" style="background:'+(p.op==="Venta"?"#9b111e":"#1a3a6b")+'">'+p.op+'</span><span class="bref">'+p.ref+'</span>';
  var waMsg=encodeURIComponent("INMO Hola, me interesa "+p.ref+" "+p.t+" ("+p.pr+"). Podeis darme info?");
  var wa="https://wa.me/"+WA_NUM+"?text="+waMsg;
  var chips=(p.ex||[]).map(function(e){return '<span class="chip" style="background:'+a.c+'1a;color:'+a.c+'">'+e+'</span>';}).join("");
  var verFicha=p.url?'<p class="sec">Ficha completa</p><p style="font-size:12px;margin-bottom:13px"><a href="'+p.url+'" target="_blank" rel="noopener" style="color:#9b111e">inmobiliarianucleo.com &rarr;</a></p>':'';
  document.getElementById("dbody").innerHTML=
    '<div style="display:flex;justify-content:space-between;margin-bottom:3px"><span class="dpr" style="color:'+a.c+'">'+p.pr+'</span><span class="dpl">'+(p.pl||"")+'</span></div>'
    +'<h2 class="dtit">'+p.t+'</h2>'
    +'<p class="dloc">'+p.calle+(p.calle?' &bull; ':'')+p.zona+'</p>'
    +'<div class="dst"><div class="ds"><div class="dsv">'+p.hab+'</div><div class="dsl">Hab.</div></div><div class="ds"><div class="dsv">'+p.ban+'</div><div class="dsl">Banos</div></div><div class="ds"><div class="dsv">'+p.m2+'m2</div><div class="dsl">Sup.</div></div></div>'
    +'<p class="sec">Descripcion</p><p class="ddesc">'+p.desc+'</p>'
    +'<p class="sec">Caracteristicas</p><div class="chips">'+chips+'</div>'
    +verFicha
    +'<p class="sec">Agente responsable</p>'
    +'<div class="agc" style="background:'+a.c+'0e;border:1px solid '+a.c+'28"><div class="agav" style="background:'+a.c+'">'+a.n[0]+'</div><div><div class="agn">'+a.n+'</div><div class="ags">Nucleo Inmobiliaria &bull; El Campello</div></div></div>'
    +'<div class="ctarow">'
    +'<a href="'+wa+'" target="_blank" rel="noopener" class="ctabtn" style="background:#25D366">'+WA+' WhatsApp</a>'
    +'<a href="tel:'+PHONE+'" class="ctabtn" style="background:#9b111e">'+PH+' Llamar</a>'
    +'</div>';
  document.getElementById("det").classList.add("open");
}
function setP(i){var p=PP.find(function(x){return x.ref===sel;});if(!p)return;photo=i;document.getElementById("dimg").src=p.f[i];document.querySelectorAll(".dot").forEach(function(d,j){d.classList.toggle("on",j===i);});}
function prevP(){var p=PP.find(function(x){return x.ref===sel;});if(!p)return;setP((photo-1+p.f.length)%p.f.length);}
function nextP(){var p=PP.find(function(x){return x.ref===sel;});if(!p)return;setP((photo+1)%p.f.length);}
function closeD(){document.getElementById("det").classList.remove("open");sel=null;render();}
async function startCall(){
  var btn=document.getElementById("cbtn"),txt=document.getElementById("ctxt");
  if(inCall){if(rc)rc.stopCall();return;}
  txt.textContent="Conectando...";btn.disabled=true;
  try{
    var res=await fetch("/nucleo/create-web-call",{method:"POST"});
    var data=await res.json();
    if(typeof RetellWebClient==="undefined"){txt.textContent="SDK no disponible";btn.disabled=false;return;}
    rc=new RetellWebClient();
    rc.on("call_started",function(){inCall=true;txt.textContent="Colgar llamada";btn.style.background="#c0392b";btn.disabled=false;});
    rc.on("call_ended",function(){inCall=false;txt.textContent="Hablar con Inmobiliaria";btn.style.background="#9b111e";btn.disabled=false;});
    rc.on("error",function(e){console.error(e);inCall=false;txt.textContent="Error - reintentar";btn.disabled=false;});
    await rc.startCall({accessToken:data.access_token,sampleRate:24000});
  }catch(e){console.error(e);txt.textContent="Error - reintentar";btn.disabled=false;}
}
render();legend();
try{initMap();}catch(e){console.error("Map:",e);}
</script>
</body>
</html>"""


if __name__ == "__main__":
    print("Cargando propiedades de Supabase...")
    props  = get_properties()
    agents = get_agents()
    print(f"  {len(props)} propiedades | {len(agents)} agentes")

    pp_js = build_js_properties(props)
    ag_js = build_js_agents(agents)

    html = (HTML_TEMPLATE
            .replace("__WA_NUMBER__", WA_NUMBER)
            .replace("__PHONE_TEL__", PHONE_TEL)
            .replace("__AG_JS__",     ag_js)
            .replace("__PP_JS__",     pp_js))

    out = os.path.join(os.path.dirname(__file__), "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"index.html generado ({len(html):,} bytes)")
    print(f"WA: {WA_NUMBER} | TEL: {PHONE_TEL}")
    for p in props:
        print(f"  [{p.get('ref')}] {p.get('titulo')} - {p.get('precio_texto')}")
