import streamlit as st
import os
import json
import requests
import io
from datetime import datetime
from bs4 import BeautifulSoup
from PIL import Image
from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig, GoogleSearch, Part
from gtts import gTTS

# 1. KONFIGURATION & SETUP
st.set_page_config(page_title="Dark Child", page_icon="🦇", layout="centered", initial_sidebar_state="collapsed")

# --- GHOST PROTOCOL (PANIC SWITCH) ---
def ghost_protocol():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- SICHERHEITSSCHLEUSE (BIOMETRIC READY) ---
def check_password():
    if "APP_PASSWORD" not in st.secrets: return True

    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
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
    /* Chat Styling */
    .stChatMessage { background-color: #111; border: 1px solid #333; }
    /* Hide Elements */
    header, footer, #MainMenu { visibility: hidden; }
    .stDeployButton { display:none; }
</style>""", unsafe_allow_html=True)

# 4. SIDEBAR CONFIG (SYSTEM CORE & GHOST)
with st.sidebar:
    st.header("⚙️ SYSTEM CORE")
    # STRICT JAN 2026 COMPLIANCE
    selected_model = st.selectbox(
        "NEURAL CORE",
        ["gemini-3-flash-preview", "gemini-3-pro-preview", "gemini-2.5-pro"],
        index=0,
        help="Gen 3 Architecture Only"
    )
    st.divider()

    # GHOST BUTTON
    st.markdown("### ⚠️ DANGER ZONE")
    if st.button("👻 GHOST PROTOCOL", type="primary", use_container_width=True, help="SOFORTIGER LOGOUT & CACHE CLEAR"):
        ghost_protocol()

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

def run_interrogator(context, question, model):
    try:
        sys = "DU BIST DER INTERROGATOR. Analysiere den Kontext und beantworte die taktische Rückfrage präzise."
        prompt = f"KONTEXT (VORHERIGER SCAN):\n{context}\n\nRÜCKFRAGE:\n{question}"
        res = client.models.generate_content(
            model=model, contents=prompt,
            config=GenerateContentConfig(system_instruction=sys, tools=[GoogleSearch()])
        )
        return res.text
    except Exception as e: return f"INTERROGATION FAILED: {e}"

def generate_audio_briefing(text):
    try:
        # Clean markdown for TTS
        clean_text = text.replace("*", "").replace("#", "").replace("-", "")[:1000] # Limit length
        tts = gTTS(text=clean_text, lang='de', slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        return buf.getvalue()
    except Exception as e: return None

def run_cerberus(data, type_hint, model):
    try:
        content = data
        if type_hint == "auto":
            if data.strip().startswith(("http://", "https://")):
                try:
                    h = {'User-Agent': 'Mozilla/5.0'}
                    r = requests.get(data, headers=h, timeout=5)
                    s = BeautifulSoup(r.content, 'html.parser')
                    [x.extract() for x in s(['script', 'style'])]
                    content = " ".join(s.get_text().split())[:3000]
                except: content = data
            else:
                content = data

        sys = """DU BIST CERBERUS. Analysiere Fakten.
        OUTPUT JSON: { "fake_suspicion": "Gering|Mittel|Hoch", "verdict": "Kurzfazit", "evidence": ["Punkt 1", "Punkt 2"] }"""

        prompt = f"Prüfe Fakten via Google Search:\n{content[:2000]}" if type_hint != "image" else [data, "Forensische Analyse."]

        res = client.models.generate_content(
            model=model, contents=prompt,
            config=GenerateContentConfig(response_mime_type="application/json", system_instruction=sys, tools=[GoogleSearch()] if type_hint != "image" else None)
        )
        return json.loads(res.text.strip().replace("```json", "").replace("```", ""))
    except Exception as e: return {"fake_suspicion": "ERROR", "verdict": str(e), "evidence": []}

def run_wiretap(audio, model, mode="transcript"):
    try:
        # SYSTEM PROMPT SWITCH
        if mode == "translate":
            sys_prompt = "DU BIST EIN UNIVERSAL-ÜBERSETZER (BABEL FISH). Deine Aufgabe: 1. Höre das Audio und erkenne automatisch die Sprache(n). 2. Übersetze den gesamten Inhalt präzise und stilgerecht ins DEUTSCHE. Gib NUR die deutsche Übersetzung aus."
        else:
            sys_prompt = "DU BIST WIRETAP. Transkribiere das Audio präzise. Wenn es eine Frage ist, antworte kurz. Wenn es eine Beobachtung ist, fasse zusammen (Militärischer Stil)."

        # Explizite Konstruktion des Audio-Parts via Blob
        audio_part = types.Part(
            inline_data=types.Blob(
                mime_type="audio/wav",
                data=audio
            )
        )

        res = client.models.generate_content(
            model=model,
            contents=[audio_part, "Führe den Befehl aus."],
            config=GenerateContentConfig(system_instruction=sys_prompt)
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
st.markdown("""
    <div style="text-align:center; margin-bottom:20px;">
        <span style="font-family:'Courier New', monospace; font-size:2.2rem; font-weight:bold; color:#E0E0E0; text-shadow: 0 0 15px rgba(0, 123, 255, 0.6); letter-spacing: 2px;">DARK CHILD</span>
        <br>
        <span style="font-family:monospace; font-size:0.9rem; color:#007BFF; letter-spacing: 1px;">MOBILE OPS v4.4 (BABEL)</span>
    </div>
""", unsafe_allow_html=True)

tab_scan, tab_check, tab_audio, tab_cam = st.tabs(["📡 SCAN", "🛡️ CHECK", "🎙️ AUDIO", "👁️ CAM"])

# --- TAB 1: SCAN & INTERROGATOR ---
with tab_scan:
    # STATE MANAGEMENT FÜR SCAN
    if "scan_result" not in st.session_state: st.session_state.scan_result = None
    if "chat_history" not in st.session_state: st.session_state.chat_history = []

    with st.expander("⚙️ TAKTISCHE PARAMETER", expanded=False):
        scan_count = st.slider("Anzahl Meldungen", 1, 10, 3)
        scan_gain = st.slider("Analysetiefe", 0, 100, 90)
        scan_style = st.select_slider("Stil", options=["TROCKEN", "FORENSISCH", "AMARONE"], value="FORENSISCH")

    query = st.text_area("ZIEL / THEMA", height=70, placeholder="Leer = Global News Update")

    if st.button("SCAN STARTEN", use_container_width=True, type="primary"):
        q = query if query else "SCAN: BREAKING NEWS (GLOBAL & TECH) - UPDATE"
        with st.status("Scanning...", expanded=True) as status:
            res = run_tactical_scan(q, scan_count, scan_style, scan_gain, selected_model)
            st.session_state.scan_result = res
            st.session_state.chat_history = [] # Reset Chat on new scan
            status.update(label="Scan Complete", state="complete", expanded=False)

    # RESULT DISPLAY
    if st.session_state.scan_result:
        st.markdown(f'<div class="mobile-output">{st.session_state.scan_result}</div>', unsafe_allow_html=True)

        # 1. AUDIO BRIEFING
        if st.button("🔊 BRIEFING ABSPIELEN", use_container_width=True):
            audio_bytes = generate_audio_briefing(st.session_state.scan_result)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3", autoplay=True)

        st.divider()

        # 2. INTERROGATOR (CHAT)
        st.caption("💬 INTERROGATOR (Kontext-Fragen)")
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Rückfrage zum Scan..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analysiere..."):
                    answer = run_interrogator(st.session_state.scan_result, prompt, selected_model)
                    st.markdown(answer)
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})

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
    # MODE SWITCH
    audio_mode = st.radio(
        "MODUS",
        ["📝 TRANSKRIPTION / ANALYSE", "🌐 BABEL FISH (AUTO-TRANSLATE)"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.info(f"🎙️ {audio_mode}")
    audio_val = st.audio_input("REC", label_visibility="collapsed")

    if audio_val:
        with st.spinner("Verarbeite Audio-Stream..."):
            # Map UI selection to internal mode
            internal_mode = "translate" if "BABEL" in audio_mode else "transcript"
            res = run_wiretap(audio_val.read(), selected_model, mode=internal_mode)
            st.markdown(f'<div class="mobile-output">{res}</div>', unsafe_allow_html=True)

            # Optional: Vorlesen des Ergebnisses (besonders bei Übersetzung sinnvoll)
            if internal_mode == "translate":
                tts_bytes = generate_audio_briefing(res)
                if tts_bytes:
                    st.audio(tts_bytes, format="audio/mp3")

# --- TAB 4: CHIMERA ---
with tab_cam:
    st.info("👁️ Mache ein Foto zur Analyse.")
    cam_val = st.camera_input("SNAP", label_visibility="collapsed")
    if cam_val:
        with st.spinner("Analysiere Bild..."):
            res = run_chimera(cam_val, selected_model)
            st.markdown(f'<div class="mobile-output">{res}</div>', unsafe_allow_html=True)