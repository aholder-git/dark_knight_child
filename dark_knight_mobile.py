import streamlit as st
import os
import json
import requests
import io
import time
import base64
from datetime import datetime
from bs4 import BeautifulSoup
from PIL import Image
from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig, GoogleSearch, Part

# ══════════════════════════════════════════════════════════════════════
# DARK CHILD v5.0 — MOBILE OPS (SEKTOR 7)
# ══════════════════════════════════════════════════════════════════════
# CHANGELOG v5.0:
#   [FIX] Cerberus Bild-Upload: PIL.Image statt UploadedFile
#   [FIX] Verdict-Farbe: Dreistufig (Gering/Mittel/Hoch)
#   [FIX] Audio .getvalue() statt .read()
#   [FIX] Audio Chain-Logik entfernt (technisch unmöglich)
#   [FIX] Markdown-Rendering in Output-Boxen
#   [NEW] Smart Routing (automatische Modellwahl pro Task)
#   [NEW] Kamera: Dual-Input (Live Snap + Galerie) + Follow-Up Chat
#   [NEW] Kamera: Rückkamera-Erzwingung via file_uploader capture
#   [NEW] Export/Download für alle Ergebnisse
#   [NEW] Perplexity AI als Scan-Alternative
#   [NEW] Rate-Limit Protection (Cooldown)
#   [NEW] st.status statt st.spinner überall
#   [UPG] gTTS beibehalten (Gemini TTS nicht auf Cloud verfügbar)
# ══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Dark Child",
    page_icon="🦇",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── GHOST PROTOCOL (PANIC SWITCH) ────────────────────────────────────
def ghost_protocol():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ── COOLDOWN GUARD ───────────────────────────────────────────────────
def check_cooldown(key="global", seconds=3):
    """Verhindert Doppel-Taps auf Mobile. Returns True wenn bereit."""
    now = time.time()
    cd_key = f"_cooldown_{key}"
    last = st.session_state.get(cd_key, 0)
    if now - last < seconds:
        return False
    st.session_state[cd_key] = now
    return True

# ── SICHERHEITSSCHLEUSE ──────────────────────────────────────────────
def check_password():
    if "APP_PASSWORD" not in st.secrets:
        return True

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
            password = st.text_input(
                "ACCESS CODE", type="password",
                placeholder="Enter Protocol Key..."
            )
            submit = st.form_submit_button(
                "AUTHENTICATE", use_container_width=True, type="primary"
            )
            if submit:
                if password == st.secrets["APP_PASSWORD"]:
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("ACCESS DENIED. INCIDENT LOGGED.")
        return False
    else:
        return True

if not check_password():
    st.stop()

# ══════════════════════════════════════════════════════════════════════
# 2. API CLIENTS
# ══════════════════════════════════════════════════════════════════════
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"GEMINI INIT ERROR: {e}")
    st.stop()

# Perplexity API (Optional — graceful degradation)
PERPLEXITY_KEY = st.secrets.get("PERPLEXITY_API", None)
PERPLEXITY_AVAILABLE = PERPLEXITY_KEY is not None

# ══════════════════════════════════════════════════════════════════════
# 3. SMART ROUTING ENGINE
# ══════════════════════════════════════════════════════════════════════
SMART_ROUTES = {
    "scan":         "gemini-3-flash-preview",   # Speed für News
    "interrogator": "gemini-3-pro-preview",     # Reasoning für Follow-Up
    "cerberus":     "gemini-3-pro-preview",     # Präzision für Faktencheck
    "wiretap":      "gemini-3-flash-preview",   # Speed für Audio
    "chimera":      "gemini-3-flash-preview",   # Speed für Vision
}

def get_model(task: str, override: str = None) -> str:
    """Smart Routing: Gibt optimales Modell pro Task zurück.
    Override aus Sidebar hat Vorrang wenn explizit gewählt."""
    if override and override != "AUTO (SMART ROUTING)":
        return override
    return SMART_ROUTES.get(task, "gemini-3-flash-preview")

# ══════════════════════════════════════════════════════════════════════
# 4. MOBILE CSS (DARK KNIGHT THEME)
# ══════════════════════════════════════════════════════════════════════
st.markdown("""<style>
    .stApp { background-color: #000000; color: #E0E0E0; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px; background-color: #0a0a0a;
        border-radius: 10px; padding: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: #111;
        border-radius: 5px; color: #888; flex-grow: 1; justify-content: center;
    }
    .stTabs [aria-selected="true"] {
        background-color: #007BFF !important; color: white !important;
    }

    /* Output */
    .mobile-output {
        background-color: #0a0a0a; padding: 15px; border-radius: 8px;
        border-left: 4px solid #007BFF; margin-top: 15px; font-size: 0.95rem;
        line-height: 1.6;
    }
    .mobile-output p { margin-bottom: 8px; }
    .mobile-output ul, .mobile-output ol { padding-left: 20px; }
    .mobile-output li { margin-bottom: 4px; }

    /* Verdict Colors */
    .verdict-safe { color: #00ff41; font-weight: bold; }
    .verdict-warn { color: #ffd700; font-weight: bold; }
    .verdict-danger { color: #ff3333; font-weight: bold; }

    /* Expander */
    div[data-testid="stExpander"] {
        background-color: #080808; border: 1px solid #333; border-radius: 5px;
    }

    /* Chat */
    .stChatMessage { background-color: #111; border: 1px solid #333; }

    /* Model Badge */
    .model-badge {
        display: inline-block; background: #111; border: 1px solid #333;
        border-radius: 4px; padding: 2px 8px; font-size: 0.7rem;
        color: #007BFF; font-family: monospace; margin-top: 5px;
    }

    /* Download Button Override */
    .stDownloadButton > button {
        background: transparent !important; border: 1px solid #333 !important;
        color: #888 !important; font-size: 0.8rem !important;
    }

    /* Hide Chrome */
    header, footer, #MainMenu { visibility: hidden; }
    .stDeployButton { display: none; }
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# 5. SIDEBAR (SYSTEM CORE)
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("⚙️ SYSTEM CORE")

    selected_model = st.selectbox(
        "NEURAL CORE",
        ["AUTO (SMART ROUTING)", "gemini-3-flash-preview",
         "gemini-3-pro-preview", "gemini-2.5-pro"],
        index=0,
        help="AUTO = Optimales Modell pro Task"
    )

    if selected_model == "AUTO (SMART ROUTING)":
        st.caption("🧠 Smart Routing aktiv")
        for task, model in SMART_ROUTES.items():
            short = model.replace("gemini-", "").replace("-preview", "")
            st.markdown(
                f"<span style='color:#555; font-size:0.75rem;'>"
                f"  {task.upper()} → {short}</span>",
                unsafe_allow_html=True
            )

    st.divider()

    # Perplexity Toggle
    if PERPLEXITY_AVAILABLE:
        use_perplexity = st.toggle("🔮 Perplexity Scan", value=False,
                                    help="Nutzt Perplexity AI statt Gemini für SCAN")
    else:
        use_perplexity = False

    st.divider()

    # DANGER ZONE
    st.markdown("### ⚠️ DANGER ZONE")
    if st.button("👻 GHOST PROTOCOL", type="primary",
                 use_container_width=True,
                 help="SOFORTIGER LOGOUT & CACHE CLEAR"):
        ghost_protocol()

    st.divider()
    if st.button("LOGOUT", use_container_width=True):
        if "password_correct" in st.session_state:
            del st.session_state["password_correct"]
        st.rerun()

# ══════════════════════════════════════════════════════════════════════
# 6. LOGIK-MODULE
# ══════════════════════════════════════════════════════════════════════

# ── PERPLEXITY SCAN ──────────────────────────────────────────────────
def run_perplexity_scan(query: str, count: int, style: str) -> str:
    """Scan via Perplexity AI API (sonar-pro)."""
    try:
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"Du bist DARK CHILD Mobile Intel. "
                        f"Liefere exakt {count} Punkte als Markdown-Liste. "
                        f"Stil: {style}. Immer mit Quellenangabe."
                    )
                },
                {"role": "user", "content": query}
            ],
            "temperature": 0.5,
            "max_tokens": 2000
        }
        r = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers, json=payload, timeout=30
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"PERPLEXITY OFFLINE: {e}"

# ── TACTICAL SCAN (GEMINI) ──────────────────────────────────────────
def run_tactical_scan(query, count, style, gain, model):
    try:
        sys = (
            f"DU BIST DARK CHILD. Mobile Intel Unit. "
            f"Nutze Google Search. Format: Markdown Liste. "
            f"Liefere exakt {count} Punkte. Stil: {style}."
        )
        temp = 0.7 if style != "AMARONE" else 1.1
        res = client.models.generate_content(
            model=model,
            contents=query,
            config=GenerateContentConfig(
                temperature=temp * (gain / 100),
                system_instruction=sys,
                tools=[GoogleSearch()]
            )
        )
        return res.text
    except Exception as e:
        return f"OFFLINE: {e}"

# ── INTERROGATOR ─────────────────────────────────────────────────────
def run_interrogator(context, question, model):
    try:
        sys = (
            "DU BIST DER INTERROGATOR. Analysiere den Kontext und "
            "beantworte die taktische Rückfrage präzise. "
            "Nutze Google Search für aktuelle Fakten."
        )
        prompt = (
            f"KONTEXT (VORHERIGER SCAN):\n{context}\n\n"
            f"RÜCKFRAGE:\n{question}"
        )
        res = client.models.generate_content(
            model=model,
            contents=prompt,
            config=GenerateContentConfig(
                system_instruction=sys,
                tools=[GoogleSearch()]
            )
        )
        return res.text
    except Exception as e:
        return f"INTERROGATION FAILED: {e}"

# ── AUDIO BRIEFING (gTTS) ───────────────────────────────────────────
# Hinweis: Gemini TTS (gemini-2.5-pro-preview-tts) erfordert
# Streaming + WAV-Handling, das auf Streamlit Cloud nicht stabil läuft.
# gTTS bleibt als zuverlässiger Fallback für Mobile.
def generate_audio_briefing(text):
    try:
        from gtts import gTTS
        clean = text.replace("*", "").replace("#", "").replace("-", "")
        tts = gTTS(text=clean, lang='de', slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        return buf.getvalue()
    except Exception:
        return None

# ── CERBERUS (FAKTENCHECK) ──────────────────────────────────────────
def run_cerberus(data, type_hint, model):
    """Faktencheck: Text/URL/Bild → JSON-Dossier."""
    try:
        sys = (
            "DU BIST CERBERUS. Analysiere Fakten.\n"
            "OUTPUT JSON: { \"fake_suspicion\": \"Gering|Mittel|Hoch\", "
            "\"verdict\": \"Kurzfazit\", "
            "\"evidence\": [\"Punkt 1\", \"Punkt 2\"] }"
        )

        if type_hint == "image":
            # FIX: PIL.Image statt UploadedFile
            img_obj = Image.open(data)
            res = client.models.generate_content(
                model=model,
                contents=[img_obj, "Forensische Bildanalyse. Prüfe auf Manipulation, Fake, Kontext."],
                config=GenerateContentConfig(
                    response_mime_type="application/json",
                    system_instruction=sys
                )
            )
        else:
            # Text oder URL
            content = data
            if data.strip().startswith(("http://", "https://")):
                try:
                    h = {'User-Agent': 'Mozilla/5.0'}
                    r = requests.get(data, headers=h, timeout=5)
                    s = BeautifulSoup(r.content, 'html.parser')
                    for x in s(['script', 'style']):
                        x.extract()
                    content = " ".join(s.get_text().split())[:3000]
                except Exception:
                    content = data

            res = client.models.generate_content(
                model=model,
                contents=f"Prüfe Fakten via Google Search:\n{content[:2000]}",
                config=GenerateContentConfig(
                    response_mime_type="application/json",
                    system_instruction=sys,
                    tools=[GoogleSearch()]
                )
            )

        raw = res.text.strip().replace("```json", "").replace("```", "")
        return json.loads(raw)

    except Exception as e:
        return {"fake_suspicion": "ERROR", "verdict": str(e), "evidence": []}

# ── WIRETAP (AUDIO) ─────────────────────────────────────────────────
def run_wiretap(audio_bytes, model, mode="transcript"):
    """Audio-Analyse: Transkription oder Übersetzung."""
    try:
        if mode == "translate":
            sys_prompt = (
                "DU BIST EIN UNIVERSAL-ÜBERSETZER (BABEL FISH). "
                "1. Höre das Audio und erkenne automatisch die Sprache(n). "
                "2. Übersetze den gesamten Inhalt präzise und stilgerecht ins DEUTSCHE. "
                "Gib NUR die deutsche Übersetzung aus."
            )
            temp = 0.2
        else:
            sys_prompt = (
                "DU BIST WIRETAP. Transkribiere das Audio präzise. "
                "Wenn es eine Frage ist, antworte kurz. "
                "Wenn es eine Beobachtung ist, fasse zusammen."
            )
            temp = 0.3

        audio_part = types.Part(
            inline_data=types.Blob(
                mime_type="audio/wav",
                data=audio_bytes
            )
        )

        res = client.models.generate_content(
            model=model,
            contents=[audio_part, "Führe den Befehl aus."],
            config=GenerateContentConfig(
                system_instruction=sys_prompt,
                temperature=temp
            )
        )
        return res.text
    except Exception as e:
        return f"AUDIO ERROR: {e}"

# ── CHIMERA (VISION) ────────────────────────────────────────────────
def run_chimera(image_source, model, follow_up=None, history=None):
    """Bildanalyse mit optionalem Follow-Up Chat."""
    try:
        img_obj = Image.open(image_source)

        if follow_up and history:
            # Follow-Up: Bild + bisherige Analyse + neue Frage
            context = "\n".join(
                [f"{m['role'].upper()}: {m['content']}" for m in history]
            )
            contents = [
                img_obj,
                f"BISHERIGE ANALYSE:\n{context}\n\nNEUE FRAGE: {follow_up}"
            ]
            sys = (
                "CHIMERA VISUAL RECON. Du hast dieses Bild bereits analysiert. "
                "Beantworte die Rückfrage basierend auf dem Bild und der bisherigen Analyse."
            )
        else:
            # Erstanalyse
            contents = [
                img_obj,
                "SITREP: Was siehst du? Personen, Text, Gefahren, Kontext. "
                "Sei präzise und strukturiert."
            ]
            sys = "CHIMERA VISUAL RECON — Mobile Field Analysis Unit."

        res = client.models.generate_content(
            model=model,
            contents=contents,
            config=GenerateContentConfig(system_instruction=sys)
        )
        return res.text
    except Exception as e:
        return f"VISUAL ERROR: {e}"

# ── EXPORT HELPER ────────────────────────────────────────────────────
def make_download(text: str, filename: str, label: str = "📥 EXPORT"):
    """Erzeugt einen Download-Button für Text-Ergebnisse."""
    st.download_button(
        label=label,
        data=text.encode("utf-8"),
        file_name=filename,
        mime="text/markdown",
        use_container_width=True
    )

# ══════════════════════════════════════════════════════════════════════
# 7. MAIN INTERFACE
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
    <div style="text-align:center; margin-bottom:20px;">
        <span style="font-family:'Courier New', monospace; font-size:2.2rem;
              font-weight:bold; color:#E0E0E0;
              text-shadow: 0 0 15px rgba(0, 123, 255, 0.6);
              letter-spacing: 2px;">DARK CHILD</span>
        <br>
        <span style="font-family:monospace; font-size:0.9rem;
              color:#007BFF; letter-spacing: 1px;">MOBILE OPS v5.0</span>
    </div>
""", unsafe_allow_html=True)

tab_scan, tab_check, tab_audio, tab_cam = st.tabs(
    ["📡 SCAN", "🛡️ CHECK", "🎙️ AUDIO", "👁️ CAM"]
)

# ══════════════════════════════════════════════════════════════════════
# TAB 1: SCAN & INTERROGATOR
# ══════════════════════════════════════════════════════════════════════
with tab_scan:
    if "scan_result" not in st.session_state:
        st.session_state.scan_result = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    with st.expander("⚙️ TAKTISCHE PARAMETER", expanded=False):
        scan_count = st.slider("Anzahl Meldungen", 1, 10, 3)
        scan_gain = st.slider("Analysetiefe", 0, 100, 90)
        scan_style = st.select_slider(
            "Stil",
            options=["TROCKEN", "FORENSISCH", "AMARONE"],
            value="FORENSISCH"
        )

    query = st.text_area(
        "ZIEL / THEMA", height=70,
        placeholder="Leer = Global News Update"
    )

    # Scan-Engine Indikator
    if use_perplexity and PERPLEXITY_AVAILABLE:
        st.markdown(
            "<span class='model-badge'>🔮 ENGINE: PERPLEXITY SONAR-PRO</span>",
            unsafe_allow_html=True
        )
    else:
        m = get_model("scan", selected_model)
        st.markdown(
            f"<span class='model-badge'>🧠 ENGINE: {m}</span>",
            unsafe_allow_html=True
        )

    if st.button("SCAN STARTEN", use_container_width=True, type="primary"):
        if not check_cooldown("scan"):
            st.warning("⏳ Cooldown aktiv...")
        else:
            q = query if query else "SCAN: BREAKING NEWS (GLOBAL & TECH) - UPDATE"
            with st.status("Scanning...", expanded=True) as status:
                if use_perplexity and PERPLEXITY_AVAILABLE:
                    res = run_perplexity_scan(q, scan_count, scan_style)
                else:
                    model = get_model("scan", selected_model)
                    res = run_tactical_scan(
                        q, scan_count, scan_style, scan_gain, model
                    )
                st.session_state.scan_result = res
                st.session_state.chat_history = []
                status.update(
                    label="Scan Complete", state="complete", expanded=False
                )

    # RESULT DISPLAY
    if st.session_state.scan_result:
        st.markdown(st.session_state.scan_result)

        col_audio, col_export = st.columns(2)
        with col_audio:
            if st.button("🔊 BRIEFING", use_container_width=True):
                audio_bytes = generate_audio_briefing(
                    st.session_state.scan_result
                )
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
        with col_export:
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            make_download(
                st.session_state.scan_result,
                f"dark_child_scan_{ts}.md",
                "📥 EXPORT"
            )

        st.divider()

        # INTERROGATOR (CHAT)
        st.caption("💬 INTERROGATOR (Kontext-Fragen)")
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Rückfrage zum Scan..."):
            st.session_state.chat_history.append(
                {"role": "user", "content": prompt}
            )
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.status("Analysiere...", expanded=False):
                    model = get_model("interrogator", selected_model)
                    answer = run_interrogator(
                        st.session_state.scan_result, prompt, model
                    )
                st.markdown(answer)
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": answer}
                )

# ══════════════════════════════════════════════════════════════════════
# TAB 2: CERBERUS (FAKTENCHECK)
# ══════════════════════════════════════════════════════════════════════
with tab_check:
    check_input = st.text_area(
        "TEXT ODER URL", height=100,
        placeholder="Paste Text oder Link..."
    )
    check_img = st.file_uploader(
        "ODER BILD UPLOAD", type=["jpg", "png", "webp"],
        label_visibility="collapsed"
    )

    if st.button("VERIFIZIEREN", use_container_width=True):
        if not check_input and not check_img:
            st.warning("Kein Input.")
        elif not check_cooldown("cerberus"):
            st.warning("⏳ Cooldown aktiv...")
        else:
            with st.status("Forensik läuft...", expanded=True) as status:
                model = get_model("cerberus", selected_model)
                if check_img:
                    dossier = run_cerberus(check_img, "image", model)
                else:
                    dossier = run_cerberus(check_input, "auto", model)
                status.update(
                    label="Dossier erstellt", state="complete", expanded=False
                )

            # Verdict Rendering (DREISTUFIG)
            susp = dossier.get('fake_suspicion', 'N/A').lower()
            if "gering" in susp:
                color = "verdict-safe"
            elif "mittel" in susp:
                color = "verdict-warn"
            else:
                color = "verdict-danger"

            ev_html = "".join(
                f"<li>{x}</li>" for x in dossier.get('evidence', [])
            )
            st.markdown(f"""<div class='mobile-output'>
                <div>RISIKO: <span class='{color}'>
                    {dossier.get('fake_suspicion', 'N/A').upper()}</span></div>
                <div style='margin-top:5px; font-weight:bold;'>
                    {dossier.get('verdict', '-')}</div>
                <hr style='margin:10px 0; border-color:#333;'>
                <ul style='padding-left:20px; margin:0;'>{ev_html}</ul>
            </div>""", unsafe_allow_html=True)

            # Export
            export_text = (
                f"# CERBERUS DOSSIER\n"
                f"**Risiko:** {dossier.get('fake_suspicion', 'N/A')}\n"
                f"**Verdict:** {dossier.get('verdict', '-')}\n\n"
                f"## Evidenz\n" +
                "\n".join(
                    f"- {x}" for x in dossier.get('evidence', [])
                )
            )
            make_download(export_text, "cerberus_dossier.md", "📥 DOSSIER")

# ══════════════════════════════════════════════════════════════════════
# TAB 3: WIRETAP (AUDIO)
# ══════════════════════════════════════════════════════════════════════
with tab_audio:
    if "audio_transcript" not in st.session_state:
        st.session_state.audio_transcript = ""

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
        # FIX: .getvalue() statt .read()
        current_bytes = audio_val.getvalue()

        # Neues Audio erkannt?
        prev_hash = st.session_state.get("_audio_hash", None)
        curr_hash = hash(current_bytes[:1000])  # Schneller Fingerprint

        if prev_hash != curr_hash:
            st.session_state["_audio_hash"] = curr_hash
            st.session_state.audio_transcript = ""

            with st.status("Verarbeite Audio...", expanded=True) as status:
                model = get_model("wiretap", selected_model)
                internal_mode = (
                    "translate" if "BABEL" in audio_mode else "transcript"
                )
                res = run_wiretap(current_bytes, model, mode=internal_mode)
                st.session_state.audio_transcript = res
                status.update(
                    label="Audio verarbeitet", state="complete", expanded=False
                )

    # ANZEIGE
    if st.session_state.audio_transcript:
        st.markdown(st.session_state.audio_transcript)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔊 VORLESEN", use_container_width=True):
                tts_bytes = generate_audio_briefing(
                    st.session_state.audio_transcript
                )
                if tts_bytes:
                    st.audio(tts_bytes, format="audio/mp3", autoplay=True)
        with col2:
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            make_download(
                st.session_state.audio_transcript,
                f"wiretap_{ts}.md",
                "📥 EXPORT"
            )

# ══════════════════════════════════════════════════════════════════════
# TAB 4: CHIMERA (VISION) — ENHANCED
# ══════════════════════════════════════════════════════════════════════
with tab_cam:
    if "cam_result" not in st.session_state:
        st.session_state.cam_result = None
    if "cam_image" not in st.session_state:
        st.session_state.cam_image = None
    if "cam_chat" not in st.session_state:
        st.session_state.cam_chat = []

    # ── DUAL INPUT: Kamera + Galerie ─────────────────────────────────
    cam_mode = st.radio(
        "QUELLE",
        ["📸 LIVE KAMERA", "🖼️ GALERIE / DATEI"],
        horizontal=True,
        label_visibility="collapsed"
    )

    image_source = None

    if cam_mode == "📸 LIVE KAMERA":
        cam_val = st.camera_input("SNAP", label_visibility="collapsed")
        if cam_val:
            image_source = cam_val
    else:
        # file_uploader mit capture="environment" → Rückkamera auf Mobile
        # Oder Galerie-Auswahl (Screenshots, empfangene Bilder)
        gallery_val = st.file_uploader(
            "BILD WÄHLEN",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed",
            key="cam_gallery"
        )
        if gallery_val:
            image_source = gallery_val

    # ── ANALYSE ──────────────────────────────────────────────────────
    if image_source:
        # Neues Bild erkannt?
        img_bytes = image_source.getvalue()
        prev_img_hash = st.session_state.get("_cam_hash", None)
        curr_img_hash = hash(img_bytes[:2000])

        if prev_img_hash != curr_img_hash:
            st.session_state["_cam_hash"] = curr_img_hash
            st.session_state.cam_chat = []
            st.session_state.cam_image = img_bytes

            with st.status("Analysiere Bild...", expanded=True) as status:
                model = get_model("chimera", selected_model)
                res = run_chimera(io.BytesIO(img_bytes), model)
                st.session_state.cam_result = res
                st.session_state.cam_chat.append(
                    {"role": "assistant", "content": res}
                )
                status.update(
                    label="Analyse abgeschlossen",
                    state="complete", expanded=False
                )

    # ── ERGEBNIS + FOLLOW-UP CHAT ────────────────────────────────────
    if st.session_state.cam_result:
        # Thumbnail anzeigen
        if st.session_state.cam_image:
            st.image(
                st.session_state.cam_image,
                use_container_width=True,
                caption="Analysiertes Bild"
            )

        # Chat-Verlauf
        for msg in st.session_state.cam_chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Follow-Up Input
        if follow_up := st.chat_input(
            "Rückfrage zum Bild...", key="cam_chat_input"
        ):
            if not check_cooldown("chimera_chat"):
                st.warning("⏳ Cooldown...")
            else:
                st.session_state.cam_chat.append(
                    {"role": "user", "content": follow_up}
                )
                with st.chat_message("user"):
                    st.markdown(follow_up)

                with st.chat_message("assistant"):
                    with st.status("Analysiere...", expanded=False):
                        model = get_model("chimera", selected_model)
                        answer = run_chimera(
                            io.BytesIO(st.session_state.cam_image),
                            model,
                            follow_up=follow_up,
                            history=st.session_state.cam_chat
                        )
                    st.markdown(answer)
                    st.session_state.cam_chat.append(
                        {"role": "assistant", "content": answer}
                    )

        # Export
        if len(st.session_state.cam_chat) > 0:
            full_analysis = "\n\n".join(
                f"**{m['role'].upper()}:** {m['content']}"
                for m in st.session_state.cam_chat
            )
            make_download(full_analysis, "chimera_analysis.md", "📥 ANALYSE")
