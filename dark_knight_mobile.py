import streamlit as st
import google.generativeai as genai
# --- FINALE KORREKTUR: GoogleSearch wird NICHT importiert ---
from google.generativeai.types import Tool, GenerationConfig, HarmCategory, HarmBlockThreshold
import os
import json
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch as SerpApiSearch
from PIL import Image
import io
from datetime import datetime

# 1. KONFIGURATION
st.set_page_config(page_title="Dark Child (Janus)", page_icon="🦇", layout="centered")

# --- SICHERHEITSSCHLEUSE ---
def check_password():
    if "APP_PASSWORD" not in st.secrets: return True
    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]: st.session_state["password_correct"] = True; del st.session_state["password"]
        else: st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.markdown("### 🔒 ZUGANGSKONTROLLE"); st.text_input("CODE", type="password", on_change=password_entered, key="password"); return False
    elif not st.session_state["password_correct"]:
        st.markdown("### 🔒 ZUGANGSKONTROLLE"); st.text_input("CODE", type="password", on_change=password_entered, key="password"); st.error("ZUGRIFF VERWEIGERT."); return False
    else: return True

if not check_password(): st.stop()

# 2. API-SETUP
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    SERPAPI_API_KEY = st.secrets["SERPAPI_API_KEY"]
    genai.configure(api_key=API_KEY)
except (KeyError, AttributeError) as e:
    st.error(f"API KEY FEHLT in st.secrets oder Konfiguration fehlgeschlagen: {e}")
    st.stop()

# 3. MOBILE CSS
st.markdown("""<style>.stApp { background-color: #000000; color: #E0E0E0; } .mobile-title { font-family: 'Courier New', monospace; font-size: 1.5rem; text-align: center; color: #888; } .mobile-output { background-color: #0a0a0a; padding: 15px; border-radius: 8px; border-left: 3px solid #007BFF; } .verdict-safe { color: #00ff41; } .verdict-warn { color: #ffd700; } .verdict-danger { color: #ff3333; } header, footer, #MainMenu { visibility: hidden; }</style>""", unsafe_allow_html=True)

# --- FUNKTIONEN: SCAN-MODUS ---
def run_tactical_scan(query_text, count_val, style_val, gain_val):
    try:
        sys_prompt = f"DU BIST 'DARK KNIGHT CHILD'. EINE MOBILE TAKTISCHE KI-EINHEIT. NUTZE GOOGLE SEARCH FÜR AKTUELLE DATEN. Formatiere als Markdown-Liste. Liefere exakt {count_val} Punkte. MODUS: {style_val}."
        # --- FINALE KORREKTUR: Tool-Aktivierung via leerem Objekt ---
        model = genai.GenerativeModel('gemini-pro', system_instruction=sys_prompt, tools=[Tool(google_search={})])
        temp = 0.7 if style_val != "AMARONE" else 1.1
        response = model.generate_content(query_text, generation_config=GenerationConfig(temperature=temp * (gain_val/100)))
        return response.text
    except Exception as e: return f"OFFLINE: {e}"

# --- FUNKTIONEN: VERIFIKATIONS-MODUS ---
def fetch_url_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}; response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser'); [s.extract() for s in soup(['script', 'style'])]
        return " ".join(t.strip() for t in soup.get_text().split())
    except Exception as e: return f"Fehler beim Abrufen der URL: {e}"

def search_google(query):
    try:
        params = {"api_key": SERPAPI_API_KEY, "engine": "google", "q": query}
        search = SerpApiSearch(params); results = search.get_dict()
        return "\n".join([res.get('snippet', '') for res in results.get('organic_results', [])])
    except Exception as e: return f"Google-Suche fehlgeschlagen: {e}"

def run_forensic_verification(input_data, input_type):
    system_prompt = f"DU BIST 'DARK KNIGHT CHILD' IM FORENSIK-MODUS. OUTPUT FORMAT (NUR JSON): {{ \"fake_suspicion\": \"Gering|Mittel|Hoch|Kritisch\", \"verdict\": \"...\", \"evidence_chain\": [\"...\"] }}"
    model = genai.GenerativeModel('gemini-pro', system_instruction=system_prompt)
    full_prompt = ""
    try:
        if input_type in ["text", "url"]:
            text = fetch_url_content(input_data) if input_type == "url" else input_data
            claims_model = genai.GenerativeModel('gemini-pro')
            claims_response = claims_model.generate_content(f"Extrahiere die 3 wichtigsten, überprüfbaren Behauptungen aus diesem Text. TEXT: {text[:2000]}")
            claims = claims_response.text
            evidence = ""
            for claim in claims.split('\n'):
                if len(claim) > 10: evidence += f"BEHAUPTUNG: '{claim}'\nSUCHERGEBNISSE:\n{search_google(claim)}\n---\n"
            full_prompt = f"SUBSTANZ (TEXT):\n{text[:2000]}\n\nBEWEISMATERIAL (SUCHERGEBNISSE):\n{evidence}"
        elif input_type == "image":
            image = Image.open(io.BytesIO(input_data.getvalue()))
            full_prompt = [image, "Führe eine forensische Analyse dieses Bildes durch."]

        response = model.generate_content(full_prompt, generation_config=GenerationConfig(response_mime_type="application/json"))
        return json.loads(response.text)
    except Exception as e:
        st.error(f"FORENSIK-FEHLER IM KERN: {e}")
        return {"error": str(e), "fake_suspicion": "KRITISCH", "verdict": "Systemfehler während der Analyse.", "evidence_chain": [str(e)]}

def display_forensic_dossier(dossier):
    suspicion = dossier.get('fake_suspicion', 'Unbekannt').lower()
    if suspicion == 'gering': v_class = "verdict-safe"
    elif suspicion == 'mittel': v_class = "verdict-warn"
    else: v_class = "verdict-danger"
    evidence_html = "".join(f"<li>{item}</li>" for item in dossier.get('evidence_chain', []))
    st.markdown(f"""<div class='mobile-output'><p><b>FAKE-VERDACHT:</b> <span class='{v_class}'>{dossier.get('fake_suspicion', 'N/A')}</span></p><p><b>URTEIL:</b> {dossier.get('verdict', 'N/A')}</p><hr><p><b>BEWEISKETTE:</b></p><ul>{evidence_html}</ul></div>""", unsafe_allow_html=True)

# 4. INTERFACE
st.markdown('<div class="mobile-title">DARK CHILD</div>', unsafe_allow_html=True)
st.caption("Protokoll Janus: Taktische Aufklärung & Forensische Verifikation")
mode = st.radio("Operationsmodus:", ["📡 Taktischer Scan", "🛡️ Forensische Verifikation"], horizontal=True)
if "last_output" not in st.session_state: st.session_state.last_output = None

if mode == "📡 Taktischer Scan":
    with st.expander("⚙️ TAKTIK & QUANTITÄT"):
        msg_count = st.slider("Anzahl", 1, 10, 3); gain = st.slider("Tiefe", 0, 100, 90); style = st.select_slider("Stil", options=["TROCKEN", "FORENSISCH", "AMARONE"], value="FORENSISCH")
    query = st.text_area("SIGNAL", height=80, placeholder="Leer lassen für Auto-Scan...")
    if st.button("SENDEN / REFRESH"):
        active_query = query if query else "SCAN: BREAKING NEWS (GLOBAL & TECH) - UPDATE"
        with st.spinner("Uplink..."): st.session_state.last_output = {"type": "scan", "content": run_tactical_scan(active_query, msg_count, style, gain)}
else:
    sub_mode_text, sub_mode_url, sub_mode_img = st.tabs(["TEXT", "URL", "BILD"])
    with sub_mode_text:
        text_input = st.text_area("Text:", height=150)
        if st.button("VERIFIZIEREN (TEXT)"):
            if text_input:
                with st.spinner("Kreuzverhör..."): st.session_state.last_output = {"type": "verification", "content": run_forensic_verification(text_input, "text")}
    with sub_mode_url:
        url_input = st.text_input("URL:")
        if st.button("VERIFIZIEREN (URL)"):
            if url_input:
                with st.spinner("Extraktion & Kreuzverhör..."): st.session_state.last_output = {"type": "verification", "content": run_forensic_verification(url_input, "url")}
    with sub_mode_img:
        img_input = st.file_uploader("Bild:", type=["jpg", "jpeg", "png"])
        if st.button("VERIFIZIEREN (BILD)"):
            if img_input:
                with st.spinner("Pixel-Analyse..."): st.session_state.last_output = {"type": "verification", "content": run_forensic_verification(img_input, "image")}

# 6. ANZEIGE
st.markdown("---")
if st.session_state.last_output:
    if st.session_state.last_output["type"] == "scan":
        st.markdown(f'<div class="mobile-output">{st.session_state.last_output["content"]}</div>', unsafe_allow_html=True)
    elif st.session_state.last_output["type"] == "verification":
        display_forensic_dossier(st.session_state.last_output["content"])