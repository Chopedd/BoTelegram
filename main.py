import os
import requests
import json
import re
import time
from ScrapperPartidos import scraping_personalizado
import ScrapperEquipos
from WinaMax import extraer_rapido
import Telegram

# ==============================================================================
# 0. CONFIGURACIÓN Y DEBUG
# ==============================================================================

MODELO_LLAMA = "llama3.1:8b-instruct-q4_0"
STAKE_BASE = 10.0  
DEBUG_MODE = True 

def logger(mensaje, tipo="INFO"):
    if DEBUG_MODE:
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{tipo}] {mensaje}")

def enviar_a_llama(prompt, system_msg="Eres un procesador de datos técnicos."):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": MODELO_LLAMA,
        "system": system_msg,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "num_thread": 4, "num_ctx": 2048}
    }
    try:
        logger(f"Enviando prompt a Llama...")
        response = requests.post(url, json=payload, timeout=660)
        res_text = response.json().get("response", "").strip()
        return res_text
    except Exception as e:
        logger(f"Error Llama: {e}", "ERROR")
        return ""

# ==============================================================================
# VARIABLES DE ESTADO GLOBALES
# ==============================================================================
config_usuario = {
    "dia_offset": None,
    "solo_proximos": None,
    "comandos_listos": 0 
}

mensajebase = None
if __name__ == "__main__":
    logger("🚀 SISTEMA INICIADO - MENÚ COMPLETO")
    
    while True:
        res_tg = Telegram.recibir_mensaje()
        if not res_tg:
            time.sleep(1)
            continue
        
        mensaje_texto, chat_id, msg_id, es_callback = res_tg
        mensaje = mensaje_texto.lower().strip()

        # Limpieza de comandos escritos
        if not es_callback:
            try: Telegram.borrar_mensaje(chat_id, msg_id)
            except: pass

        # Inicialización del mensaje base si es la primera vez
        if mensajebase is None:
            mensajebase = Telegram.enviar_mensaje_botones(
                chat_id,
                "🤖 <b>Analista IA Fútbol</b>\nSelecciona una opción para comenzar:",
                { "🔥 INICIAR TODO": "/dia", "OTROS": "/otros"}
            )

        # --- GESTIÓN DE COMANDOS ---
        if "/start" in mensaje:
            # Reiniciamos estado al dar start
            config_usuario = {"dia_offset": 0, "solo_proximos": False, "comandos_listos": 0}
            Telegram.editar_mensaje_botones(
                chat_id, mensajebase,
                "🤖 <b>Analista IA Fútbol</b>\nSelecciona una opción para comenzar:", 
                { "🔥 INICIAR TODO": "/dia", "OTROS": "/otros"}
            )

        elif "/otros" in mensaje:
            Telegram.editar_mensaje_botones(chat_id, mensajebase, "🔧 <b>Otras opciones:</b>", {"Guía": "/help","Ver Partidos": "/partidos", "Config. Día": "/dia", "Volver": "/start"})

        elif "/help" in mensaje:
            Telegram.editar_mensaje_botones(chat_id, mensajebase, "<b>Guía:</b>\n/dia - Configura fecha\n/iniciar - Proceso automático\n/exit - Salir", {"Volver": "/start"})

        elif "/partidos" in mensaje:
            ph = scraping_personalizado(config_usuario["dia_offset"])
            formato = "\n".join([f"• {l} vs {v} ({h if h else 'Hora N/A'})" for l, v, h in zip(*ph)])
            Telegram.editar_mensaje_botones(chat_id, mensajebase, f"<b>Partidos detectados:</b>\n{formato}", {"Volver": "/start"})

        elif "/dia" in mensaje:
            if "hoy" in mensaje:
                config_usuario["dia_offset"] = 0
                config_usuario["comandos_listos"] = 1
                Telegram.editar_mensaje_botones(chat_id, mensajebase, "📅 <b>Día: HOY</b>\n¿Filtrar próximos?", {"Sí": "/proximos true", "No": "/proximos false"})
            elif "manana" in mensaje or "mañana" in mensaje:
                config_usuario["dia_offset"] = 1
                config_usuario["comandos_listos"] = 1
                Telegram.editar_mensaje_botones(chat_id, mensajebase, "📅 <b>Día: MAÑANA</b>\n¿Filtrar próximos?", {"Sí": "/proximos true", "No": "/proximos false"})
            else:
                Telegram.editar_mensaje_botones(chat_id, mensajebase, "📅 <b>Selecciona el día:</b>", {"Hoy": "/dia hoy", "Mañana": "/dia manana"})

        elif "/proximos" in mensaje:
            config_usuario["solo_proximos"] = "true" in mensaje
            config_usuario["comandos_listos"] = 2
            Telegram.editar_mensaje_botones(chat_id, mensajebase, "⏳ <b>Filtro configurado.</b>\n¿Lanzamos el análisis?", {"🚀 INICIAR AHORA": "/iniciar"})

        elif "/exit" in mensaje:
            Telegram.editar_progreso(chat_id, mensajebase, "Cerrando... Usa /start para volver.")
            mensajebase = None # Reset para que se cree uno nuevo en el siguiente start


        elif "/iniciar" in mensaje:
            Telegram.editar_progreso(chat_id, mensajebase, "🚀 <b>Iniciando análisis...</b>\nObteniendo partidos y cuotas...")
            # 4. DISPARADOR DE ANÁLISIS
            if config_usuario["comandos_listos"] >= 2:
                locales, visitantes, horas = scraping_personalizado(config_usuario["dia_offset"])
                
                if not locales:
                    Telegram.editar_progreso(chat_id, mensajebase, "❌ No se encontraron partidos.")
                else:
                    db_partidos = [{"txt": f"{l} vs {v}", "iso": h if h else "9999"} for l, v, h in zip(locales, visitantes, horas)]
                    db_partidos.sort(key=lambda x: x['iso'])
                    pool = db_partidos[:10] if config_usuario["solo_proximos"] else db_partidos[:40]

                    prompt_sel = f"[TASK: SELECT_5]\nDATA: {', '.join([p['txt'] for p in pool[:25]])}"
                    res_sel = enviar_a_llama(prompt_sel, "DATA_EXTRACTOR")
                    
                    candidatos = []
                    for linea in res_sel.split('\n'):
                        if " vs " in linea.lower():
                            nombre = re.sub(r'^[\d\s\.\-\*]+', '', linea).strip()
                            for p in pool:
                                if nombre.lower() in p['txt'].lower():
                                    candidatos.append(p)
                                    break
                    
                    candidatos = candidatos[:5] if candidatos else pool[:5]
                    reporte_base = ""
                    estados = [0] * len(candidatos) 

                    for i, p_obj in enumerate(candidatos):
                        texto_dinamico = "🚀 <b>La IA está procesando los picks...</b>\n\n"
                        for idx, c in enumerate(candidatos):
                            icono = "✅" if estados[idx] == 1 else "⏳"
                            texto_dinamico += f"• {c['txt']} {icono}\n"
                        
                        Telegram.editar_progreso(chat_id, mensajebase, texto_dinamico)

                        partido = p_obj['txt']
                        local, visitante = partido.split(' vs ')
                        cuotas = extraer_rapido(local, visitante)
                        
                        if cuotas:
                            # --- 1. DATOS DEL LOCAL (CASA + RACHA GLOBAL) ---
                            hist_l = ScrapperEquipos.obtener_ultimos_resultados(local)
                            nombre_real_l = hist_l.get('equipo_buscado', local)
                            resultados_l = hist_l.get('ultimos_resultados', [])

                            # A. Eficiencia en Casa (los que jugó como local)
                            partidos_casa = [r for r in resultados_l if nombre_real_l.lower() in r.get('local', '').lower()][:10]
                            wins_casa = sum(1 for r in partidos_casa if (g := re.findall(r'\d+', r.get('texto_plano', ''))) 
                                            and len(g) >= 2 and int(g[0]) >= int(g[1]))
                            efi_casa_l = (wins_casa / len(partidos_casa) * 100) if partidos_casa else 0

                            # B. Racha Global (Últimos 5 partidos totales)
                            ultimos_5_l = resultados_l[:5]
                            wins_racha_l = 0
                            for r in ultimos_5_l:
                                g = re.findall(r'\d+', r.get('texto_plano', ''))
                                if len(g) >= 2:
                                    # Si era local y ganó/empató O si era visitante y ganó
                                    if (nombre_real_l.lower() in r['local'].lower() and int(g[0]) >= int(g[1])) or \
                                    (nombre_real_l.lower() in r['visitante'].lower() and int(g[1]) > int(g[0])):
                                        wins_racha_l += 1
                            racha_global_l = (wins_racha_l / 5 * 100) if ultimos_5_l else 0

                            # --- 2. DATOS DEL VISITANTE (FUERA + RACHA GLOBAL) ---
                            hist_v = ScrapperEquipos.obtener_ultimos_resultados(visitante)
                            nombre_real_v = hist_v.get('equipo_buscado', visitante)
                            resultados_v = hist_v.get('ultimos_resultados', [])

                            # A. Eficiencia Fuera (los que jugó como visitante)
                            partidos_fuera = [r for r in resultados_v if nombre_real_v.lower() in r.get('visitante', '').lower()][:10]
                            wins_fuera = sum(1 for r in partidos_fuera if (g := re.findall(r'\d+', r.get('texto_plano', ''))) 
                                            and len(g) >= 2 and int(g[1]) > int(g[0]))
                            efi_fuera_v = (wins_fuera / len(partidos_fuera) * 100) if partidos_fuera else 0

                            # B. Racha Global (Últimos 5 partidos totales)
                            ultimos_5_v = resultados_v[:5]
                            wins_racha_v = 0
                            for r in ultimos_5_v:
                                g = re.findall(r'\d+', r.get('texto_plano', ''))
                                if len(g) >= 2:
                                    # Victoria pura del visitante sin importar dónde
                                    if (nombre_real_v.lower() in r['visitante'].lower() and int(g[1]) > int(g[0])) or \
                                    (nombre_real_v.lower() in r['local'].lower() and int(g[0]) > int(g[1])):
                                        wins_racha_v += 1
                            racha_global_v = (wins_racha_v / 5 * 100) if ultimos_5_v else 0

                            # --- 3. CÁLCULO DE CONFIANZA FINAL (MIX AL 50/50) ---
                            # Promediamos su fuerza específica (casa/fuera) con su racha actual (últimos 5)
                            fuerza_l = (efi_casa_l + racha_global_l) / 2
                            fuerza_v = (efi_fuera_v + racha_global_v) / 2

                            total_fuerza = fuerza_l + fuerza_v
                            if total_fuerza > 0:
                                conf_l_final = round((fuerza_l / total_fuerza) * 100)
                                conf_v_final = 100 - conf_l_final
                            else:
                                conf_l_final, conf_v_final = 51, 49

                            # --- 4. REPORTE PARA LA IA ---
                            reporte_base += (
                                f"✅ PARTIDO: {partido}\n"
                                f"   🏠 LOCAL: Casa {efi_casa_l}% | Racha Gral {racha_global_l}%\n"
                                f"   🚀 VISITANTE: Fuera {efi_fuera_v}% | Racha Gral {racha_global_v}%\n"
                                f"   🔥 CONFIANZA TOTAL: {local} {conf_l_final}% | {visitante} {conf_v_final}%\n"
                                f"   💰 CUOTAS 1X2: 1: {cuotas['1x2'][0]} | X: {cuotas['1x2'][1]} | 2: {cuotas['1x2'][2]}\n"
                                f"-------------------------------\n")
                        
                        estados[i] = 1
                        time.sleep(0.2)

                    Telegram.editar_progreso(chat_id, mensajebase, "✅ <b>¡Procesado!</b>\nGenerando reporte final...")
                    
                    prompt_final = f"""
    [TASK: ANALISTA_ESTRATÉGICO_FÚTBOL]
    DATA_INPUT:
    {reporte_base}

    INSTRUCTIONS:
    1. Revisa la 'CONFIANZA TOTAL' generada por el cálculo (Casa/Fuera + Racha).
    2. APLICA ESTA LÓGICA DE SELECCIÓN:
    - CONFIANZA > 80%: "VICTORIA SIMPLE" (Es un favorito absoluto en racha).
    - CONFIANZA 65% - 80%: "VICTORIA SIMPLE" (Si la cuota es > 2.00) o "DOBLE OPORTUNIDAD" (Si buscas asegurar).
    - CONFIANZA 50% - 64%: "DOBLE OPORTUNIDAD" (Partido igualado, proteger con empate).
    - CONFIANZA < 50%: "RIESGO ALTO / NO APOSTAR".

    3. ETIQUETAS ESPECIALES:
    - Si 'Racha Gral' es 100% en el favorito, añade el emoji 🔥.
    - Si la 'Cuota Sugerida' es > 2.00 y la Confianza es > 80%, añade [💎 VALOR DETECTADO].

    FORMATO:
    ✅ **[LOCAL] vs [VISITANTE]**
    🎯 **PRONÓSTICO:** [Resultado]
    📈 **CONFIANZA:** [Valor L]% (Local) | [Valor V]% (Visitante)
    💰 **CUOTA SUGERIDA:** [Valor de la cuota]
    ---
    """
                    informe_final = enviar_a_llama(prompt_final, "TIPSTER_PROFESIONAL")
                    Telegram.editar_mensaje_botones(
                    chat_id, mensajebase, 
                    f"🏆 <b>REPORTE FINAL IA</b>\n\n{informe_final}",
                    {"🔄 Nueva búsqueda": "/start"}
                    )

                config_usuario = {"dia_offset": None, "solo_proximos": None, "comandos_listos": 0}