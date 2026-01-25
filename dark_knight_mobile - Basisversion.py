import streamlit as st
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
import os

# 1. KONFIGURATION
st.set_page_config(page_title="Dark Child", page_icon="🦇", layout="centered")

# --- SICHERHEITSSCHLEUSE ---
def check_password():
    if "APP_PASSWORD" not in st.secrets:
        return True 
    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.markdown("### 🔒 ZUGANGSKONTROLLE")
        st.text_input("CODE", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("### 🔒 ZUGANGSKONTROLLE")
        st.text_input("CODE", type="password", on_change=password_entered, key="password")
        st.error("ZUGRIFF VERWEIGERT.")
        return False
    else:
        return True

if not check_password():
    st.stop()

# 2. API-SETUP (NEUE LIB)
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("API KEY FEHLT.")
    st.stop()

client = genai.Client(api_key=API_KEY)

# 3. MOBILE CSS
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #E0E0E0; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    .mobile-title {
        font-family: 'Courier New', monospace; font-size: 1.5rem; text-align: center; color: #888;
        letter-spacing: 3px; margin-bottom: 15px; border-bottom: 1px solid #333; padding-bottom: 10px;
    }
    div[data-baseweb="slider"] > div > div > div { background-color: #007BFF !important; }
    div[data-baseweb="slider"] [role="slider"] { background-color: #007BFF !important; border: 2px solid #007BFF !important; }
    .stTextInput input, .stTextArea textarea {
        background-color: #111 !important; color: #FFF !important; border: 1px solid #333 !important; border-radius: 8px;
    }
    .stTextInput input:focus, .stTextArea textarea:focus { border-color: #007BFF !important; }
    .stButton>button {
        background: #007BFF !important; color: white !important; width: 100%; height: 3.5em; border-radius: 8px;
        font-weight: bold; font-size: 1.1rem; border: none; text-transform: uppercase; letter-spacing: 2px;
    }
    .mobile-output {
        background-color: #0a0a0a; padding: 15px; border-radius: 8px;
        border-left: 3px solid #007BFF; font-family: sans-serif; line-height: 1.6; font-size: 0.95rem; margin-top: 20px;
    }
    /* Listen-Styling für bessere Lesbarkeit */
    .mobile-output ul { padding-left: 20px; margin-bottom: 0; }
    .mobile-output li { margin-bottom: 10px; }
    
    header, footer, #MainMenu { visibility: hidden; }
    div[data-testid="stExpander"] { background-color: #0a0a0a; border: 1px solid #333; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# --- FUNKTION: TAKTISCHER SCAN ---
def run_tactical_scan(query_text, count_val, style_val, gain_val):
    try:
        # System Prompt mit strikter Formatierung
        sys_prompt = f"""
        DU BIST 'DARK KNIGHT CHILD'. EINE MOBILE TAKTISCHE KI-EINHEIT.
        
        BEFEHLSPROTOKOLL:
        1. NUTZE GOOGLE SEARCH FÜR AKTUELLE DATEN (HEUTE: {os.popen('date /t').read() if os.name=='nt' else 'HEUTE'}).
        2. FORMATIERUNG: Nutze Markdown-Listen.
        3. WICHTIG: Mache nach jedem Listenpunkt ZWEI Zeilenumbrüche (\\n\\n), damit es auf dem Handy lesbar ist.
        4. LIEFERE EXAKT {count_val} PUNKTE.
        
        MODUS: {style_val}.
        """
        
        final_query = f"{query_text}\n\n[ANWEISUNG: Suche im Internet nach aktuellen Infos. Liste exakt {count_val} Punkte auf.]"
        
        temp = 0.7 if style_val != "AMARONE" else 1.1
        
        # API Call mit Google Search Tool
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=final_query,
            config=GenerateContentConfig(
                temperature=temp * (gain_val/100),
                max_output_tokens=2000,
                system_instruction=sys_prompt,
                tools=[Tool(google_search=GoogleSearch())] # <-- HIER IST DAS INTERNET
            )
        )
        
        # Fallback falls Search nichts liefert
        if not response.text:
            return "Keine Daten empfangen. Satellit offline."
            
        return response.text
        
    except Exception as e:
        return f"OFFLINE: {e}"

# 4. INTERFACE
st.markdown('<div class="mobile-title">DARK CHILD</div>', unsafe_allow_html=True)

with st.expander("⚙️ TAKTIK & QUANTITÄT"):
    msg_count = st.slider("Anzahl (Meldungen)", 1, 10, 3)
    st.markdown("---")
    gain = st.slider("Tiefe", 0, 100, 90)
    style = st.select_slider("Modus", options=["TROCKEN", "FORENSISCH", "AMARONE"], value="FORENSISCH")

query = st.text_area("SIGNAL", height=80, placeholder="Leer lassen für Auto-Scan...")

# 5. LOGIK
if "last_output" not in st.session_state:
    with st.spinner("Initialisiere Radar..."):
        start_query = "SCAN: BREAKING NEWS (GLOBAL & TECH) - WICHTIGSTE ENTWICKLUNGEN DER LETZTEN 24H"
        st.session_state["last_output"] = run_tactical_scan(start_query, msg_count, style, gain)

if st.button("SENDEN / REFRESH"):
    active_query = query if query else "SCAN: BREAKING NEWS (GLOBAL & TECH) - UPDATE"
    with st.spinner("Uplink..."):
        st.session_state["last_output"] = run_tactical_scan(active_query, msg_count, style, gain)

# 6. ANZEIGE
if "last_output" in st.session_state:
    # Wir erzwingen hier nochmal Zeilenumbrüche per Python, falls die KI faul war
    formatted_output = st.session_state["last_output"].replace("* ", "\n\n* ")
    st.markdown(f'<div class="mobile-output">{formatted_output}</div>', unsafe_allow_html=True)

