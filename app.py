import streamlit as st
import google.generativeai as genai
import pypdf
from fpdf import FPDF

# --- 1. SEITEN-SETUP ---
st.set_page_config(page_title="UPS Bot Gr. 7", page_icon="🤖")
st.title("🤖 UPS Expert Bot - Gruppe 7")
st.markdown("### Schritt 5: Standardisieren & Wiederanwenden")
st.markdown("Lade einen Problemlösungs-Report (PDF) hoch oder beschreibe das Problem im Chat.")

# --- 2. API KEY & EINSTELLUNGEN ---
st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Google API Key:", type="password")

# --- 3. FUNKTIONEN (PDF ERSTELLEN) ---
def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Titel
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="UPS Report - Schritt 5", ln=1, align='C')
    pdf.ln(10)
    
    # Inhalt (Zurück zu Standard-Font)
    pdf.set_font("Arial", size=12)
    
    # WICHTIG: FPDF mag keine Emojis und manche Sonderzeichen. 
    # Wir ersetzen Markdown-Sternchen und reinigen den Text.
    clean_text = text.replace("**", "").replace("* ", "- ")
    
    # Umlaute-Fix für FPDF (Latin-1 Encoding)
    # Zeichen, die nicht in Latin-1 sind (z.B. Emojis), werden ignoriert, damit es nicht abstürzt.
    clean_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.multi_cell(0, 10, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. PDF UPLOADER (LESEN) ---
st.sidebar.header("📄 Dokument Upload")
uploaded_file = st.sidebar.file_uploader("Lade hier deinen Bericht hoch:", type="pdf")

pdf_text = ""
if uploaded_file is not None:
    try:
        reader = pypdf.PdfReader(uploaded_file)
        for page in reader.pages:
            pdf_text += page.extract_text()
        st.sidebar.success(f"PDF erfolgreich gelesen! ({len(pdf_text)} Zeichen)")
    except Exception as e:
        st.sidebar.error(f"Fehler beim Lesen des PDFs: {e}")

# --- 5. SYSTEM PROMPT ---
SYSTEM_PROMPT = """
Du bist ein Experte für industrielle Problemlösungsmethoden (z.B. 8D, UPS, Six Sigma).
Du befindest dich in Schritt 5: "Standardize & Reapply" (Standardisieren & Übertragen).

Deine Aufgabe:
Nimm die gelösten Probleme (aus Texteingabe oder PDF) entgegen und bereite die Standardisierung vor.

WICHTIG FÜR DIE ANALYSE:
Prüfe, ob die Vorarbeit sauber geleistet wurde. Benenne die Methoden explizit:

1.  Nenne die Problembeschreibung ausdrücklich "Ergebnis der Problem Investigation (6W-2H)".
2.  Nenne die Ursache ausdrücklich "Ergebnis der Root Cause Analysis (5-Why)".

Strukturiere deine Antwort exakt so:

TEIL 1: QUALITÄTS-CHECK DER VORARBEIT
* **Problem Investigation (6W-2H):** Fasse das Problem kurz zusammen. Ist es präzise beschrieben?
* **Root Cause Analysis (5-Why):** Wurde die wahre Ursache gefunden?
* **Lösung & Verifikation:** Ist die Lösung nachhaltig?

TEIL 2: STANDARDISIERUNG (SOPs & Dokumente)
* Erstelle einen Entwurf für eine Standard-Arbeitsanweisung (SOP) oder A3-Report.
* Welche Dokumente müssen angepasst werden? (Wartungspläne, FMEA).

TEIL 3: REAPPLICATION MATRIX (Wissenstransfer)
* **Copy Exact:** Wo kann diese Lösung 1:1 übernommen werden?
* **Copy with Change:** Wo ist das Prinzip übertragbar?

Sei präzise, methodisch stark und lösungsorientiert. Verzichte auf Emojis in der Ausgabe, damit das PDF sauber generiert werden kann.
"""

# --- 6. VERBINDUNG HERSTELLEN & CHAT ---
if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # Modell-Check
        verfuegbare_modelle = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                verfuegbare_modelle.append(m.name)
        
        modell_name = 'models/gemini-pro'
        if modell_name not in verfuegbare_modelle and verfuegbare_modelle:
            modell_name = verfuegbare_modelle[0]
        
        model = genai.GenerativeModel(modell_name)

        # Chat-History initialisieren
        if "messages" not in st.session_state:
            st.session_state.messages = []
            st.session_state.chat = model.start_chat(history=[
                {"role": "user", "parts": ["Instruktion: " + SYSTEM_PROMPT]},
                {"role": "model", "parts": ["Verstanden. Ich erstelle Analysen für SOPs und Reapplication ohne Emojis."]}
            ])

        # Alte Nachrichten anzeigen
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # --- LOGIK: ENTWEDER PDF ANALYSIEREN ODER CHAT ---
        user_input = None
        
        # Button für PDF-Analyse (nur wenn PDF da ist)
        if pdf_text and st.sidebar.button("PDF Analysieren"):
            user_input = f"Hier ist der Inhalt eines hochgeladenen PDF-Reports. Analysiere ihn:\n\n{pdf_text}"
            display_text = "📂 *PDF-Analyse gestartet...*" # Was im Chat angezeigt wird
        
        # Normales Chat-Eingabefeld
        elif prompt := st.chat_input("Beschreibe dein Problem..."):
            user_input = prompt
            display_text = prompt

        # Wenn eine Eingabe vorliegt (egal ob PDF oder Text)
        if user_input:
            # 1. User Nachricht anzeigen
            st.session_state.messages.append({"role": "user", "content": display_text})
            with st.chat_message("user"):
                st.markdown(display_text)

            # 2. KI Fragen
            try:
                response = st.session_state.chat.send_message(user_input)
                bot_text = response.text
                
                # 3. KI Antwort anzeigen
                st.session_state.messages.append({"role": "assistant", "content": bot_text})
                with st.chat_message("assistant"):
                    st.markdown(bot_text)
                    
                    # --- HIER IST DAS NEUE FEATURE: PDF DOWNLOAD ---
                    st.markdown("---")
                    pdf_data = create_pdf(bot_text)
                    st.download_button(
                        label="📥 Ergebnis als PDF herunterladen",
                        data=pdf_data,
                        file_name="UPS_Schritt5_Report.pdf",
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"Fehler: {e}")

    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
else:
    st.info("⬅️ Bitte gib links deinen API Key ein.")
