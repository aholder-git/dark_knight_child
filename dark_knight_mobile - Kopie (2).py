import streamlit as st
import google.generativeai as genai
import os

# 1. KONFIGURATION (Mobile Optimized)
st.set_page_config(page_title="Dark Child", page_icon="🦇", layout="centered")

# --- SICHERHEITSSCHLEUSE (LOCKDOWN) ---
def check_password():
    """Verhindert unbefugten Zugriff auf die API-Kosten."""
    
    # Wenn kein Passwort in den Secrets definiert ist (z.B. lokal ohne config), 
    # warnen wir, aber lassen es laufen (oder blockieren, je nach Wunsch).
    # Hier: Wir gehen davon aus, dass es in der Cloud läuft.
    if "APP_PASSWORD" not in st.secrets:
        # Fallback für lokalen Test ohne Secrets (optional)
        return True

    def password_entered():
        """Prüft das eingegebene Passwort."""
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Passwort aus dem Speicher löschen
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Erste Initialisierung: Zeige Eingabefeld
        st.markdown("### 🔒 ZUGANGSKONTROLLE SEKTOR 7")
        st.text_input(
            "CODE EINGEBEN", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Passwort war falsch
        st.markdown("### 🔒 ZUGANGSKONTROLLE SEKTOR 7")
        st.text_input(
            "CODE EINGEBEN", type="password", on_change=password_entered, key="password"
        )
        st.error("ZUGRIFF VERWEIGERT.")
        return False
    else:
        # Passwort korrekt
        return True

if not check_password():
    st.stop()  # HIER IST ENDE FÜR FREMDE
# ----------------------------------------

# 2. API-SETUP (Hybrid)
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    API_KEY = os.environ.get("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)

# 3. MOBILE CSS (ZERO RED POLICY)
st.markdown("""
    <style>
    /* BASIS */
    .stApp { background-color: #000000; color: #E0E0E0; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    
    /* TITEL */
    .mobile-title {
        font-family: 'Courier New', monospace;
        font-size: 1.5rem; text-align: center; color: #888;
        letter-spacing: 3px; margin-bottom: 15px; border-bottom: 1px solid #333;
        padding-bottom: 10px;
    }
    
    /* ZERO RED POLICY: SLIDER (MOBILE FIX) */
    div[data-baseweb="slider"] > div > div > div { background-color: #007BFF !important; }
    div[data-baseweb="slider"] [role="slider"] { background-color: #007BFF !important; border: 2px solid #007BFF !important; }
    
    /* INPUTS */
    .stTextInput input, .stTextArea textarea {
        background-color: #111 !important; color: #FFF !important;
        border: 1px solid #333 !important; border-radius: 8px;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #007BFF !important;
    }
    
    /* BUTTON */
    .stButton>button {
        background: #007BFF !important; color: white !important;
        width: 100%; height: 3.5em; border-radius: 8px;
        font-weight: bold; font-size: 1.1rem; border: none;
        text-transform: uppercase; letter-spacing: 2px;
    }
    
    /* OUTPUT */
    .mobile-output {
        background-color: #0a0a0a; padding: 15px; border-radius: 8px;
        border-left: 3px solid #007BFF; font-family: sans-serif; 
        line-height: 1.5; font-size: 0.95rem; margin-top: 20px;
    }
    
    /* HIDE CLUTTER */
    header, footer, #MainMenu { visibility: hidden; }
    div[data-testid="stExpander"] { background-color: #0a0a0a; border: 1px solid #333; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# 4. INTERFACE
st.markdown('<div class="mobile-title">DARK CHILD</div>', unsafe_allow_html=True)

# Kompakte Einstellungen
with st.expander("⚙️ TAKTIK (GAIN / MODUS)"):
    gain = st.slider("Tiefe", 0, 100, 90)
    style = st.select_slider("Modus", options=["TROCKEN", "FORENSISCH", "AMARONE"], value="FORENSISCH")

# Input
query = st.text_area("SIGNAL", height=120, placeholder="Befehl eingeben...")

# 5. LOGIK
if st.button("SENDEN"):
    if not query:
        st.warning("Leeres Signal.")
    else:
        try:
            # Konstruktion der Identität
            sys_prompt = f"""
            DU BIST 'DARK KNIGHT CHILD'. EINE MOBILE TAKTISCHE KI-EINHEIT VON SEKTOR 7.
            ANTWORTE KURZ, PRÄZISE, OHNE FLOSKELN. FORMATIERE FÜR MOBILE LESBARKEIT.
            MODUS: {style}. KONTEXT: JANUAR 2026.
            """
            
            model = genai.GenerativeModel("gemini-2.5-pro", system_instruction=sys_prompt)
            
            temp = 0.7 if style != "AMARONE" else 1.1
            
            with st.spinner("Uplink..."):
                response = model.generate_content(
                    query, 
                    generation_config={"temperature": temp * (gain/100), "max_output_tokens": 1500}
                )
            
            st.markdown(f'<div class="mobile-output">{response.text}</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"OFFLINE: {e}")