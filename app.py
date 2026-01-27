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

# --- 3. FUNKTIONEN (SMART PDF ERSTELLEN) ---
def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Haupt-Überschrift (Header des Dokuments)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "UPS Expert Bot - Report (Schritt 5)", ln=True, align='C')
    
    # Untertitel / Disclaimer
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 100, 100) # Grau
    pdf.cell(0, 8, "Automatisch generierter Entwurf für A3-Summary & SOPs", ln=True, align='C')
    
    # Trennlinie
    pdf.set_draw_color(0, 0, 0) # Schwarz
    pdf.line(10, 30, 200, 30)
    pdf.ln(10) # Abstand nach unten
    
    # 2. Text intelligent verarbeiten
    pdf.set_text_color(0, 0, 0) # Zurück zu Schwarz
    
    # Wir teilen den Text in einzelne Zeilen auf
    lines = text.split('\n')
    
    for line in lines:
        # Bereinigung: Markdown-Sternchen entfernen
        clean_line = line.replace("**", "").replace("##", "")
        
        # Encoding Fix für Umlaute (Wichtig!)
        clean_line = clean_line.encode('latin-1', 'replace').decode('latin-1')
        
        # CHECK: Ist das eine Überschrift? (Erkennt "TEIL 1", "TEIL 2" oder Zeilen mit Doppelpunkt am Ende)
        if "TEIL" in clean_line and ":" in clean_line:
            # ---> ÜBERSCHRIFT-FORMATIERUNG
            pdf.ln(5) # Etwas Abstand vor neuer Sektion
            pdf.set_font("Arial", 'B', 12) # Fett, Größe 12
            pdf.set_fill_color(230, 230, 230) # Hellgrauer Hintergrund
            # (Breite 0 = ganze Zeile, Höhe 8, Text, Rahmen 0, Zeilenumbruch 1, Ausrichtung L, Füllen True)
            pdf.cell(0, 8, txt=clean_line, ln=True, align='L', fill=True)
            pdf.set_font("Arial", '', 11) # Zurücksetzen für nächsten Text
            
        # CHECK: Ist es ein wichtiger Unterpunkt? (Startet mit "- " oder "* ")
        elif clean_line.strip().startswith("-") or clean_line.strip().startswith("*"):
            # ---> LISTEN-FORMATIERUNG
            pdf.set_font("Arial", '', 11)
            pdf.set_x(15) # Einrückung nach rechts
            pdf.multi_cell(0, 6, txt=clean_line)
            pdf.set_x(10) # Zurücksetzen
            
        else:
            # ---> STANDARD-TEXT
            # Leere Zeilen überspringen wir nicht komplett, damit Absätze bleiben
            if clean_line.strip() == "":
                pdf.ln(2)
            else:
                pdf.set_font("Arial", '', 11)
                pdf.multi_cell(0, 6, txt=clean_line)

    # Footer
    pdf.set_y(-15)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 10, 'Generiert durch Google Gemini & Streamlit | Gruppe 7', 0, 0, 'C')
    
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

# --- 5. SYSTEM PROMPT (Der "Gehirn"-Teil) ---
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

Sei präzise, methodisch stark und lösungsorientiert.
WICHTIG: Verzichte auf Emojis in der Ausgabe, damit das PDF sauber generiert werden kann.
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
        display_text = None
        
        # Button für PDF-Analyse (nur wenn PDF da ist)
        if pdf_text and st.sidebar.button("PDF Analysieren"):
            user_input = f"Hier ist der Inhalt eines hochgeladenen PDF-Reports. Analysiere ihn:\n\n{pdf_text}"
            display_text = "📂 *PDF-Analyse gestartet...*"
        
        # Normales Chat-Eingabefeld
        elif prompt := st.chat_input("Beschreibe dein Problem..."):
            user_input = prompt
            display_text = prompt

        # Wenn eine Eingabe vorliegt (egal ob PDF oder Text)
        if user_input and display_text:
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
                    
                    # --- PDF DOWNLOAD BUTTON ---
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
