import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def scraping_personalizado(dia):
    lista_locales, lista_visitantes, lista_horas = [], [], []
    
    url = "https://onefootball.com/es/partidos" if dia == 0 else "https://onefootball.com/es/partidos/tomorrow"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    # --- CONFIGURACIÓN DE FILTROS ---
    ligas_top = [
        "laliga", "premier league", "serie a", "bundesliga", "ligue 1",
        "champions league", "europa league", "copa del rey", "fa cup",
        "eredivisie", "liga profesional argentina", "brasileirão betano",
        "segunda división", "laliga hypermotion", "liga portugal", "mls"
    ]
    
    # Palabras que descartan el partido automáticamente
    exclusiones = ["femenino", "femenil", "women", "u21", "u19", "sub-21", "sub-19", "sub 21", "sub 19"]

    ahora = datetime.now()
    hora_formateada = ahora.strftime("%H:%M")

    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        data = json.loads(script.string)

        containers = data.get('props', {}).get('pageProps', {}).get('containers', [])
        partidos = []
        vistos = set()

        for c in containers:
            # Extraer datos de los componentes de la página
            match_data = c.get('type', {}).get('fullWidth', {}).get('component', {}).get('contentType', {})
            partidos_raw = (match_data.get('matchCardsList', {}) or match_data.get('matchCardsGroup', {})).get('matchCards', [])

            for p in partidos_raw:
                # 1. Obtener y limpiar nombre de la liga
                liga_p = "Internacional"
                for event in p.get('trackingEvents', []):
                    params = event.get('typedServerParameter', {})
                    if 'competition' in params:
                        liga_p = params['competition'].get('value', "Internacional")
                        break

                nombre_liga_clean = liga_p.lower().strip()
                local = p.get('homeTeam', {}).get('name', '')
                visitante = p.get('awayTeam', {}).get('name', '')
                hora = p.get('kickoffTimeFormatted', "--:--")

                # 2. APLICAR FILTROS
                # Filtro A: ¿Está en nuestras ligas top?
                if nombre_liga_clean not in ligas_top:
                    continue
                
                # Filtro B: ¿Es categoría inferior o femenino? (Revisamos liga y nombres de equipos)
                texto_analisis = f"{nombre_liga_clean} {local.lower()} {visitante.lower()}"
                if any(ex in texto_analisis for ex in exclusiones):
                    continue

                # 3. Validar duplicados y hora (solo si es para "hoy")
                if local and visitante:
                    id_partido = f"{local}-{visitante}"
                    
                    # Si es para hoy (dia=0), filtramos los que ya pasaron
                    if dia == 0 and hora <= hora_formateada:
                        continue

                    if id_partido not in vistos:
                        vistos.add(id_partido)
                        partidos.append((hora, local, visitante))

        # --- ORDENAR PARTIDOS POR HORA ---
        partidos_ordenados = sorted(
            partidos,
            key=lambda x: datetime.strptime(x[0], "%H:%M")
        )

        for h, l, v in partidos_ordenados:
            lista_horas.append(h)
            lista_locales.append(l)
            lista_visitantes.append(v)

        return lista_locales, lista_visitantes, lista_horas

    except Exception as e:
        print(f"💥 Error en scraping: {e}")
        return [], [], []

if __name__ == "__main__":
    locales, visitantes, horas = scraping_personalizado(0)
    if not locales:
        print("No hay partidos que cumplan los filtros para hoy.")
    else:
        for l, v, h in zip(locales, visitantes, horas):
            print(f"{h} - {l} vs {v}")