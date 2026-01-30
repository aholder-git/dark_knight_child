import streamlit as st
import os
import json
import requests
import io
from datetime import datetime
from bs4 import BeautifulSoup
from PIL import Image
from google import genai
from google.genai.types import GenerateContentConfig, GoogleSearch, Part

# 1. KONFIGURATION & SETUP
st.set_page_config(page_title="Dark Child", page_icon="🦇", layout="centered", initial_sidebar_state="collapsed")

# --- SICHERHEITSSCHLEUSE (BIOMETRIC READY) ---
def check_password():
    if "APP_PASSWORD" not in st.secrets: return True

    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        # Styling für den Login-Screen
        st.markdown("""
            <style>
            .login-header { text-align: center; margin-bottom: 20px; }
            .login-icon { font-size: 3rem; }
            .login-title { font-family: 'Courier New', monospace; font-weight: bold; color: #007BFF; font-size: 1.5rem; }
            .login-sub { color: #666; font-size: 0.8rem; letter-spacing: 2px; }
            </style>
            <div class='login-header'>
                <div class='login-icon'>🛡️</div>
                <div class='login-title'>SEKTOR 7</div>
                <div class='login-sub'>IDENTITY VERIFICATION</div>
            </div>
        """, unsafe_allow_html=True)

        # Formular erzwingt Browser-Passwort-Manager Interaktion
        with st.form("auth_form"):
            password = st.text_input("ACCESS CODE", type="password", placeholder="Enter Protocol Key...")
            submit = st.form_submit_button("AUTHENTICATE", use_container_width=True, type="primary")

            if submit:
                if password == st.secrets["APP_PASSWORD"]:
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("ACCESS DENIED. INCIDENT LOGGED.")
        return False
    else:
        return True

if not check_password(): st.stop()

# 2. API CLIENT (V1.0)
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"INIT ERROR: {e}")
    st.stop()

# 3. MOBILE CSS (OPTIMIERT)
st.markdown("""<style>
    .stApp { background-color: #000000; color: #E0E0E0; }
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 2px; background-color: #0a0a0a; border-radius: 10px; padding: 5px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #111; border-radius: 5px; color: #888; flex-grow: 1; justify-content: center; }
    .stTabs [aria-selected="true"] { background-color: #007BFF !important; color: white !important; }
    /* Output Styling */
    .mobile-output { background-color: #0a0a0a; padding: 15px; border-radius: 8px; border-left: 4px solid #007BFF; margin-top: 15px; font-size: 0.95rem; }
    /* Verdict Colors */
    .verdict-safe { color: #00ff41; font-weight: bold; }
    .verdict-warn { color: #ffd700; font-weight: bold; }
    .verdict-danger { color: #ff3333; font-weight: bold; }
    /* Expander Styling */
    div[data-testid="stExpander"] { background-color: #080808; border: 1px solid #333; border-radius: 5px; }
    /* Hide Elements */
    header, footer, #MainMenu { visibility: hidden; }
    .stDeployButton { display:none; }
</style>""", unsafe_allow_html=True)

# 4. SIDEBAR CONFIG (NUR NOCH SYSTEM CORE)
with st.sidebar:
    st.header("⚙️ SYSTEM CORE")
    selected_model = st.selectbox("MODEL", ["gemini-2.0-flash-exp", "gemini-2.5-pro", "gemini-3-pro-preview"], index=0)
    st.divider()
    if st.button("LOGOUT", use_container_width=True):
        del st.session_state["password_correct"]
        st.rerun()

# 5. LOGIK MODULE
def run_tactical_scan(query, count, style, gain, model):
    try:
        sys = f"DU BIST DARK CHILD. Mobile Intel Unit. Nutze Google Search. Format: Markdown Liste. Liefere exakt {count} Punkte. Stil: {style}."
        temp = 0.7 if style != "AMARONE" else 1.1
        res = client.models.generate_content(
            model=model, contents=query,
            config=GenerateContentConfig(temperature=temp*(gain/100), system_instruction=sys, tools=[GoogleSearch()])
        )
        return res.text
    except Exception as e: return f"OFFLINE: {e}"

def run_cerberus(data, type_hint, model):
    try:
        # Auto-Detect URL vs Text
        content = data
        if type_hint == "auto":
            if data.strip().startswith(("http://", "https://")):
                try:
                    h = {'User-Agent': 'Mozilla/5.0'}
                    r = requests.get(data, headers=h, timeout=5)
                    s = BeautifulSoup(r.content, 'html.parser')
                    [x.extract() for x in s(['script', 'style'])]
                    content = " ".join(s.get_text().split())[:3000]
                except: content = data # Fallback
            else:
                content = data

        # Analysis
        sys = """DU BIST CERBERUS. Analysiere Fakten.
        OUTPUT JSON: { "fake_suspicion": "Gering|Mittel|Hoch", "verdict": "Kurzfazit", "evidence": ["Punkt 1", "Punkt 2"] }"""

        prompt = f"Prüfe Fakten via Google Search:\n{content[:2000]}" if type_hint != "image" else [data, "Forensische Analyse."]

        res = client.models.generate_content(
            model=model, contents=prompt,
            config=GenerateContentConfig(response_mime_type="application/json", system_instruction=sys, tools=[GoogleSearch()] if type_hint != "image" else None)
        )
        return json.loads(res.text.strip().replace("```json", "").replace("```", ""))
    except Exception as e: return {"fake_suspicion": "ERROR", "verdict": str(e), "evidence": []}

def run_wiretap(audio, model):
    try:
        res = client.models.generate_content(
            model=model, contents=[Part.from_bytes(audio, mime_type="audio/wav"), "Transkribiere und fasse zusammen (Militärischer Stil)."],
            config=GenerateContentConfig(system_instruction="WIRETAP AUDIO ANALYSIS")
        )
        return res.text
    except Exception as e: return f"AUDIO ERROR: {e}"

def run_chimera(img, model):
    try:
        img_obj = Image.open(img)
        res = client.models.generate_content(
            model=model, contents=[img_obj, "SITREP: Was siehst du? Personen, Text, Gefahren, Kontext."],
            config=GenerateContentConfig(system_instruction="CHIMERA VISUAL RECON")
        )
        return res.text
    except Exception as e: return f"VISUAL ERROR: {e}"

# 6. MAIN INTERFACE (TABS)
# --- TITEL UPGRADE ---
st.markdown("""
    <div style="text-align:center; margin-bottom:20px;">
        <span style="font-family:'Courier New', monospace; font-size:2.2rem; font-weight:bold; color:#E0E0E0; text-shadow: 0 0 15px rgba(0, 123, 255, 0.6); letter-spacing: 2px;">DARK CHILD</span>
        <br>
        <span style="font-family:monospace; font-size:0.9rem; color:#007BFF; letter-spacing: 1px;">MOBILE OPS v3.5</span>
    </div>
""", unsafe_allow_html=True)

tab_scan, tab_check, tab_audio, tab_cam = st.tabs(["📡 SCAN", "🛡️ CHECK", "🎙️ AUDIO", "👁️ CAM"])

# --- TAB 1: SCAN ---
with tab_scan:
    # PARAMETER WIEDER HIER (IM EXPANDER)
    with st.expander("⚙️ TAKTISCHE PARAMETER (ANZAHL / TIEFE)", expanded=False):
        scan_count = st.slider("Anzahl Meldungen", 1, 10, 3)
        scan_gain = st.slider("Analysetiefe", 0, 100, 90)
        scan_style = st.select_slider("Stil", options=["TROCKEN", "FORENSISCH", "AMARONE"], value="FORENSISCH")

    query = st.text_area("ZIEL / THEMA", height=70, placeholder="Leer = Global News Update")

    if st.button("SCAN STARTEN", use_container_width=True, type="primary"):
        q = query if query else "SCAN: BREAKING NEWS (GLOBAL & TECH) - UPDATE"
        with st.status("Scanning...", expanded=True) as status:
            res = run_tactical_scan(q, scan_count, scan_style, scan_gain, selected_model)
            status.update(label="Scan Complete", state="complete", expanded=False)
            st.markdown(f'<div class="mobile-output">{res}</div>', unsafe_allow_html=True)

# --- TAB 2: CERBERUS ---
with tab_check:
    check_input = st.text_area("TEXT ODER URL", height=100, placeholder="Paste Text oder Link...")
    check_img = st.file_uploader("ODER BILD UPLOAD", type=["jpg", "png"], label_visibility="collapsed")

    if st.button("VERIFIZIEREN", use_container_width=True):
        if not check_input and not check_img:
            st.warning("Kein Input.")
        else:
            with st.status("Forensik läuft...", expanded=True) as status:
                if check_img:
                    dossier = run_cerberus(check_img, "image", selected_model)
                else:
                    dossier = run_cerberus(check_input, "auto", selected_model)
                status.update(label="Dossier erstellt", state="complete", expanded=False)

                # Render Dossier
                susp = dossier.get('fake_suspicion', 'N/A')
                color = "verdict-safe" if "gering" in susp.lower() else "verdict-danger"
                ev_html = "".join(f"<li>{x}</li>" for x in dossier.get('evidence', []))
                st.markdown(f"""<div class='mobile-output'>
                    <div>RISIKO: <span class='{color}'>{susp.upper()}</span></div>
                    <div style='margin-top:5px; font-weight:bold;'>{dossier.get('verdict')}</div>
                    <hr style='margin:10px 0; border-color:#333;'>
                    <ul style='padding-left:20px; margin:0;'>{ev_html}</ul>
                </div>""", unsafe_allow_html=True)

# --- TAB 3: WIRETAP ---
with tab_audio:
    st.info("🎙️ Sprich deine Beobachtung oder Frage.")
    audio_val = st.audio_input("REC", label_visibility="collapsed")
    if audio_val:
        with st.spinner("Analysiere Audio..."):
            res = run_wiretap(audio_val.read(), selected_model)
            st.markdown(f'<div class="mobile-output">{res}</div>', unsafe_allow_html=True)

# --- TAB 4: CHIMERA ---
with tab_cam:
    st.info("👁️ Mache ein Foto zur Analyse.")
    cam_val = st.camera_input("SNAP", label_visibility="collapsed")
    if cam_val:
        with st.spinner("Analysiere Bild..."):
            res = run_chimera(cam_val, selected_model)
            st.markdown(f'<div class="mobile-output">{res}</div>', unsafe_allow_html=True)