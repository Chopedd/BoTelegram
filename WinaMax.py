import time
import re
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==============================================================================
# 1. FUNCIONES DE SOPORTE
# ==============================================================================

def super_limpieza(driver):

    """Elimina obstáculos visuales, pop-ups y restaura el scroll en Winamax."""

    scripts = [
        # Cerrar botones X
        """
        const botonesCerrar = document.querySelectorAll('button[class*="close"], [class*="Close"], [aria-label*="close"], [class*="dismiss"]');
        botonesCerrar.forEach(btn => { try { btn.click(); } catch(e) {} });
        """,
        # Eliminar contenedores de publicidad e incentivos
        'document.querySelectorAll(\'div[class*="iVhMEg"], div[class*="IncentivePopup"], div[class*="dtLvIy"], [id*="onetrust"]\').forEach(el => el.remove());',
        # Forzar scroll activo
        "document.body.style.overflow = 'auto'; document.documentElement.style.overflow = 'auto';",
        # Header relativo para que no tape elementos al hacer click
        "document.querySelectorAll('header').forEach(el => el.style.position = 'relative');",
    ]

    for s in scripts:

        try:
            driver.execute_script(s)

        except:
            continue

def limpiar_nombre_equipo(nombre):
    """Limpia el nombre para mejorar la búsqueda en Winamax."""
    ignore = ["real", "fc", "cf", "deportivo", "atlético", "atletico", "club", "stade", "olympique", "de", "sd", "ud", "rb", "sk"]
    palabras = [p for p in nombre.lower().split() if p not in ignore and len(p) > 2]
    # Si queda algo, usamos la palabra más larga (suele ser el nombre distintivo)
    if palabras:
        return max(palabras, key=len)
    return nombre.split()[0].lower()

# ==============================================================================
# 2. NÚCLEO DE EXTRACCIÓN
# ==============================================================================

def limpiar_nombre_equipo(nombre):
    ignore = ["real", "fc", "cf", "deportivo", "atlético", "atletico", "club", "stade", "olympique", "de", "sd", "ud", "rb"]
    palabras = [p for p in nombre.lower().split() if p not in ignore and len(p) > 2]
    return max(palabras, key=len) if palabras else nombre.split()[0].lower()

# ==============================================================================
# 2. NÚCLEO DE EXTRACCIÓN (LÓGICA DE ESCALADA)
# ==============================================================================

import time
import re
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==============================================================================
# 1. FUNCIONES DE SOPORTE
# ==============================================================================

def super_limpieza(driver):
    """Elimina obstáculos visuales, pop-ups y restaura el scroll en Winamax."""
    scripts = [
        """
        const botonesCerrar = document.querySelectorAll('button[class*="close"], [class*="Close"], [aria-label*="close"], [class*="dismiss"]');
        botonesCerrar.forEach(btn => { try { btn.click(); } catch(e) {} });
        """,
        'document.querySelectorAll(\'div[class*="iVhMEg"], div[class*="IncentivePopup"], div[class*="dtLvIy"], [id*="onetrust"]\').forEach(el => el.remove());',
        "document.body.style.overflow = 'auto'; document.documentElement.style.overflow = 'auto';",
        "document.querySelectorAll('header').forEach(el => el.style.position = 'relative');",
    ]
    for s in scripts:
        try: driver.execute_script(s)
        except: continue

def limpiar_nombre_equipo(nombre):
    """Limpia el nombre para mejorar la búsqueda en Winamax."""
    ignore = ["real", "fc", "cf", "deportivo", "atlético", "atletico", "club", "stade", "olympique", "de", "sd", "ud", "rb", "sk"]
    palabras = [p for p in nombre.lower().split() if p not in ignore and len(p) > 2]
    if palabras:
        return max(palabras, key=len)
    return nombre.split()[0].lower()

# ==============================================================================
# 2. NÚCLEO DE EXTRACCIÓN (BURBUJEO + RESALTADO)
# ==============================================================================



    scripts = [
        """
        const botonesCerrar = document.querySelectorAll('button[class*="close"], [class*="Close"], [aria-label*="close"], [class*="dismiss"]');
        botonesCerrar.forEach(btn => { try { btn.click(); } catch(e) {} });
        """,
        'document.querySelectorAll(\'div[class*="iVhMEg"], div[class*="IncentivePopup"], div[class*="dtLvIy"], [id*="onetrust"]\').forEach(el => el.remove());',
        "document.body.style.overflow = 'auto'; document.documentElement.style.overflow = 'auto';",
        "document.querySelectorAll('header').forEach(el => el.style.position = 'relative');",
    ]
    for s in scripts:
        try: driver.execute_script(s)
        except: continue
def extraer_rapido(loc, vis):
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless=new") # Descomenta si no quieres ver el navegador
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 25)
    
    mercados_reales = []
    resultado_final = None # Variable para almacenar el retorno

    try:
        driver.get("https://www.winamax.es/apuestas-deportivas")
        time.sleep(1)
        super_limpieza(driver)

        # 1. BUSCADOR
        bus = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='Buscar']")))
        driver.execute_script("arguments[0].click();", bus)
        palabra = limpiar_nombre_equipo(loc)
        bus.send_keys(palabra)
        time.sleep(1)
        
        enlaces = driver.find_elements(By.CSS_SELECTOR, "a[href*='/match/']")
        if not enlaces: 
            print(f"❌ Evento '{loc}' no encontrado en Winamax.")
            return None
            
        driver.get(enlaces[0].get_attribute("href"))
        time.sleep(1)
        super_limpieza(driver)
        
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "odd-button-value")))

        # 2. ESCANEO POR POSICIÓN (SCROLL ACUMULATIVO)
        for paso in range(2):
            if paso > 0:
                driver.execute_script(f"window.scrollTo(0, {paso * 700});")
                time.sleep(1.5)

            script_posicion = """
            let encontrados = [];
            document.querySelectorAll('.bet-group-template, [class*="bet-group"], section').forEach(b => {
                let btns = Array.from(b.querySelectorAll('.odd-button-value'));
                if (btns.length === 3) {
                    let cuotas = btns.slice(0, 3).map(el => el.innerText.replace(',', '.').trim());
                    let nums = cuotas.map(parseFloat);
                    
                    if (nums.every(n => !isNaN(n) && n > 1.01 && n < 50)) {
                        encontrados.push({
                            valores: cuotas,
                            promedio: nums.reduce((a, b) => a + b, 0) / 3,
                            y: b.getBoundingClientRect().top + window.scrollY
                        });
                    }
                }
            });
            return encontrados;
            """
            nuevos = driver.execute_script(script_posicion)
            for n in nuevos:
                if n["valores"] not in [m["valores"] for m in mercados_reales]:
                    mercados_reales.append(n)

        # 3. ASIGNACIÓN POR ORDEN DE APARICIÓN
        mercados_reales.sort(key=lambda x: x["y"])

        if len(mercados_reales) < 1:
            print("❌ No se detectaron bloques de cuotas.")
            return None

        # El primero de arriba SIEMPRE es el 1X2
        cuotas_1x2 = mercados_reales[0]["valores"]

        # Buscamos el de menor promedio para la Doble Oportunidad
        otros_mercados = [m for m in mercados_reales if m["valores"] != cuotas_1x2]
        otros_mercados.sort(key=lambda x: x["promedio"])
        
        cuotas_doble = otros_mercados[0]["valores"] if otros_mercados else ["N/A", "N/A", "N/A"]

        # 4. PREPARACIÓN DEL DICCIONARIO PARA RETORNO
        resultado_final = {
            "evento": f"{loc} vs {vis}",
            "1x2": cuotas_1x2,
            "doble": cuotas_doble
        }
        

    except Exception as e: 
        print(f"❌ Error en extraer_rapido: {e}")
        resultado_final = None
    finally: 
        driver.quit()
        return resultado_final

