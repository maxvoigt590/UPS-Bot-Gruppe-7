import streamlit as st
import google.generativeai as genai

# --- 1. SEITEN-SETUP ---
st.set_page_config(page_title="UPS Bot Gr. 7", page_icon="🤖")
st.title("🤖 UPS Expert Bot - Gruppe 7")
st.markdown("### Schritt 5: Standardisieren & Wiederanwenden")

# --- 2. API KEY & DIAGNOSE ---
st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Google API Key:", type="password")

# --- 3. SYSTEM PROMPT (HIER IST DAS UPDATE) ---
SYSTEM_PROMPT = """
Du bist ein Experte für den UPS-Prozess (Uniform Problem Solving) bei Mercedes-Benz.
Du befindest dich in Schritt 5: "Standardize & Reapply".

Deine Aufgabe:
Nimm die gelösten Probleme aus Schritt 4 entgegen und bereite die Standardisierung vor.

WICHTIG FÜR DIE ANALYSE:
Du musst prüfen, ob die Vorarbeit aus Schritt 2 und 3 sauber geleistet wurde. 
Benenne die Methoden in deiner Antwort explizit:

1.  Nenne die Problembeschreibung ausdrücklich "Ergebnis der Problem Investigation (6W-2H)".
2.  Nenne die Ursache ausdrücklich "Ergebnis der Root Cause Analysis (5-Why)".

Strukturiere deine Antwort exakt so:

TEIL 1: QUALITÄTS-CHECK DER VORARBEIT
* **Problem Investigation (6W-2H):** Fasse das Problem kurz zusammen. Ist es präzise beschrieben?
* **Root Cause Analysis (5-Why):** Wurde die wahre Ursache gefunden? (Nenne sie).
* **Lösung & Verifikation:** Ist die Lösung nachhaltig?

TEIL 2: STANDARDISIERUNG (A3 & SOPs)
* Erstelle einen Entwurf für das A3-Summary.
* Welche Dokumente müssen angepasst werden? (Wartungspläne, FMEA, Arbeitsanweisungen).

TEIL 3: REAPPLICATION MATRIX
* **Copy Exact:** Wo kann diese Lösung 1:1 übernommen werden? (Gleiche Maschinen, andere Linien).
* **Copy with Change:** Wo ist das Prinzip übertragbar? (Ähnliche Prozesse, andere Standorte).

Sei präzise, professionell und technisch fundiert.
"""

# --- 4. VERBINDUNG HERSTELLEN ---
if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # HIER IST DER TRICK: Wir schauen nach, was wirklich da ist
        verfuegbare_modelle = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                verfuegbare_modelle.append(m.name)
        
        # Zeige zur Beruhigung in der Seitenleiste an, was wir gefunden haben
        with st.sidebar.expander("Technik-Check (Verfügbare Modelle)"):
            st.write(verfuegbare_modelle)

        # Wir nehmen das Modell, das IMMER funktioniert bei der alten Version
        # Falls 'gemini-pro' nicht da ist, nehmen wir das erste aus der Liste
        modell_name = 'models/gemini-pro'
        if modell_name not in verfuegbare_modelle and verfuegbare_modelle:
            modell_name = verfuegbare_modelle[0]
        
        st.sidebar.success(f"Verbunden mit: {modell_name}")
        
        model = genai.GenerativeModel(modell_name)

        # --- 5. CHAT VERLAUF ---
        if "messages" not in st.session_state:
            st.session_state.messages = []
            # System Prompt senden (unsichtbar)
            st.session_state.chat = model.start_chat(history=[
                {"role": "user", "parts": ["Instruktion: " + SYSTEM_PROMPT]},
                {"role": "model", "parts": ["Verstanden. Ich bin bereit für Schritt 5 unter Berücksichtigung von 6W-2H und 5-Why."]}
            ])

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Beschreibe dein gelöstes Problem..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                response = st.session_state.chat.send_message(prompt)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                with st.chat_message("assistant"):
                    st.markdown(response.text)
            except Exception as e:
                st.error(f"Fehler bei der Antwort: {e}")

    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
        st.info("Tipp: API Key prüfen oder Internetverbindung checken.")
else:
    st.info("⬅️ Bitte gib links deinen API Key ein.")
