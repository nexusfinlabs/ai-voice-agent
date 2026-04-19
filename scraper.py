import httpx
from bs4 import BeautifulSoup
import json
import os
import time
from pathlib import Path

BASE_URL = "https://www.inmobiliarianucleo.com"
SEARCH_URL = "https://www.inmobiliarianucleo.com/comprar/viviendas/alicante-provincia/alicante/playa-san-juan"
OUTPUT_DIR = Path("data/properties")
IMAGES_DIR = Path("data/images")

# Crear directorios
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

def scrape_properties():
    print(f"── Iniciando scrape de {SEARCH_URL}...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = httpx.get(SEARCH_URL, headers=headers, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error al acceder a la web: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Buscar tarjetas de propiedades
    # Nota: Basado en una estructura común, habrá que ajustar selectores tras ver el HTML
    cards = soup.select(".property-card, [class*='PropertyCard'], .item-grid") 
    print(f"🔍 Encontradas {len(cards)} posibles tarjetas.")

    properties = []

    # Si no encuentra nada con selectores genéricos, imprimimos un poco del HTML para debug
    if not cards:
        print("⚠️ No se encontraron tarjetas con los selectores iniciales. Intentando detectar estructura...")
        # Guardar para debug
        with open("debug_page.html", "w") as f:
            f.write(response.text)
    
    for i, card in enumerate(cards[:10]): # Limitar a 10 para la demo
        try:
            # Estos selectores son hipótesis, se ajustarán en la siguiente iteración
            title_el = card.select_one("h2, .title, [class*='title']")
            price_el = card.select_one(".price, [class*='price']")
            img_el = card.select_one("img")
            link_el = card.select_one("a")

            prop = {
                "id": f"NUC-{i+1:03d}",
                "title": title_el.text.strip() if title_el else "Propiedad sin título",
                "price": price_el.text.strip() if price_el else "Consultar",
                "url": BASE_URL + link_el['href'] if link_el and link_el['href'].startswith("/") else link_el['href'] if link_el else "",
                "image_url": img_el['src'] if img_el else "",
                "local_image": ""
            }

            # Descargar imagen
            if prop["image_url"]:
                img_name = f"{prop['id']}_main.jpg"
                img_path = IMAGES_DIR / img_name
                try:
                    img_data = httpx.get(prop["image_url"], headers=headers).content
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                    prop["local_image"] = str(img_path)
                    print(f"📸 Imagen guardada: {img_name}")
                except:
                    print(f"⚠️ No se pudo descargar imagen para {prop['id']}")

            properties.append(prop)
            print(f"✅ Procesada {prop['id']}: {prop['title']}")
            
        except Exception as e:
            print(f"❌ Error procesando tarjeta {i}: {e}")

    # Guardar resultados
    with open("data/properties.json", "w", encoding="utf-8") as f:
        json.dump(properties, f, indent=4, ensure_ascii=False)
    
    print(f"\n✨ Scrape finalizado. {len(properties)} propiedades guardadas en data/properties.json")

if __name__ == "__main__":
    scrape_properties()
