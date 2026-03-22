import requests
from bs4 import BeautifulSoup
import re
import time

def obtener_ultimos_resultados(nombre_equipo):
    # Limpieza rápida para mejorar la búsqueda en API
    busqueda = nombre_equipo.replace("FC ", "").replace("AS ", "").replace("VfB ", "").strip()
    
    search_url = f"https://search-api.onefootball.com/v2/es/search?q={busqueda}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Origin": "https://onefootball.com",
        "Referer": "https://onefootball.com/"
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        data = response.json()
        
        slug = None
        team_name = None

        def buscar_equipo_en_json(obj):
            nonlocal slug, team_name
            if isinstance(obj, dict):
                if 'url' in obj and '/equipo/' in obj['url']:
                    slug = obj['url'].split('/')[-1]
                    team_name = obj.get('title') or obj.get('name')
                    return True
                for v in obj.values():
                    if buscar_equipo_en_json(v): return True
            elif isinstance(obj, list):
                for item in obj:
                    if buscar_equipo_en_json(item): return True
            return False

        buscar_equipo_en_json(data)

        if not slug:
            return {"error": f"No encontrado: {nombre_equipo}", "ultimos_resultados": []}

        url_resultados = f"https://onefootball.com/es/equipo/{slug}/resultados"
        res_web = requests.get(url_resultados, headers=headers, timeout=10)
        soup = BeautifulSoup(res_web.text, 'html.parser')
        
        lista_partidos = []
        # Selectores actualizados de OneFootball
        cards = soup.find_all('article', class_=re.compile(r'SimpleMatchCard_simpleMatchCard'))

        for card in cards[:15]: # Miramos un poco más de 10 para asegurar encontrar casa/fuera
            try:
                teams_tags = card.find_all('span', class_=re.compile(r'Team_simpleMatchCardTeam__name'))
                scores_tags = card.find_all('span', class_=re.compile(r'Team_simpleMatchCardTeam__score'))
                
                teams = [t.get_text().strip() for t in teams_tags]
                scores = [s.get_text().strip() for s in scores_tags]
                
                if len(teams) == 2 and len(scores) == 2:
                    # ROL basado en el nombre oficial encontrado en el JSON
                    rol = "LOCAL" if team_name.lower() in teams[0].lower() else "VISITANTE"
                    
                    lista_partidos.append({
                        "local": teams[0],
                        "visitante": teams[1],
                        "goles_local": scores[0],
                        "goles_visitante": scores[1],
                        "rol": rol,
                        "texto_plano": f"{teams[0]} {scores[0]}-{scores[1]} {teams[1]}"
                    })
            except: continue
        
        return {
            "equipo_buscado": team_name,
            "ultimos_resultados": lista_partidos
        }

    except Exception as e:
        return {"error": str(e), "ultimos_resultados": []}

if __name__ == "__main__":
    # --- CONFIGURACIÓN DE TEST ---
    local_input = "Barcelona"
    visitante_input = "Real Madrid"
    
    print(f"🔍 Analizando: {local_input} vs {visitante_input}...\n")

    # --- 1. PROCESO LOCAL (CASA) ---
    hist_l = obtener_ultimos_resultados(local_input)
    nombre_real_l = hist_l.get('equipo_buscado', local_input)
    
    # Filtramos partidos donde el equipo buscado es el LOCAL
    partidos_casa = [r for r in hist_l.get('ultimos_resultados', []) 
                     if nombre_real_l.lower() in r['local'].lower()][:10]
    
    wins_l = 0
    print(f"🏠 Resultados en casa de {nombre_real_l}:")
    for r in partidos_casa:
        gL, gV = int(r['goles_local']), int(r['goles_visitante'])
        # Consideramos éxito si no pierde (1X)
        if gL >= gV:
            wins_l += 1
            print(f"  ✅ {r['texto_plano']}")
        else:
            print(f"  ❌ {r['texto_plano']}")

    efi_l = (wins_l / len(partidos_casa) * 100) if partidos_casa else 0

    # --- 2. PROCESO VISITANTE (FUERA) ---
    hist_v = obtener_ultimos_resultados(visitante_input)
    nombre_real_v = hist_v.get('equipo_buscado', visitante_input)
    
    # Filtramos partidos donde el equipo buscado es el VISITANTE
    partidos_fuera = [r for r in hist_v.get('ultimos_resultados', []) 
                      if nombre_real_v.lower() in r['visitante'].lower()][:10]
    
    wins_v = 0
    print(f"\n🚀 Resultados fuera de {nombre_real_v}:")
    for r in partidos_fuera:
        gL, gV = int(r['goles_local']), int(r['goles_visitante'])
        # Victoria pura del visitante
        if gV > gL:
            wins_v += 1
            print(f"  ✅ {r['texto_plano']}")
        else:
            print(f"  ❌ {r['texto_plano']}")

    efi_v = (wins_v / len(partidos_fuera) * 100) if partidos_fuera else 0

    # --- 3. CÁLCULO DE CONFIANZA BASE 100% ---
    total = efi_l + efi_v
    if total > 0:
        conf_l = round((efi_l / total) * 100)
        conf_v = 100 - conf_l
    else:
        conf_l, conf_v = 50, 50

    # --- REPORTE FINAL ---
    print("\n" + "="*30)
    print(f"🏆 REPORTE FINAL")
    print(f"EFI {nombre_real_l} (Casa): {efi_l}%")
    print(f"EFI {nombre_real_v} (Fuera): {efi_v}%")
    print(f"🔥 CONFIANZA: {nombre_real_l} {conf_l}% | {nombre_real_v} {conf_v}%")
    print("="*30)