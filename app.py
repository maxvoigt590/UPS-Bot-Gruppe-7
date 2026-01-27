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

# --- 3. FUNKTIONEN (SMART PDF ERSTELLEN - CLEAN VERSION) ---
def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "A3 Summary Sheet - Documentation", ln=True, align='C')
    
    # Untertitel
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 100, 100) # Grau
    pdf.cell(0, 8, "Automatisch generierter Entwurf für Schritt 5", ln=True, align='C')
    
    # Trennlinie
    pdf.set_draw_color(0, 0, 0) # Schwarz
    pdf.line(10, 30, 200, 30)
    pdf.ln(10)
    
    # Text verarbeitung
    pdf.set_text_color(0, 0, 0)
    lines = text.split('\n')
    
    for line in lines:
        clean_line = line.replace("**", "").replace("##", "")
        clean_line = clean_line.encode('latin-1', 'replace').decode('latin-1')
        
        # LOGIK: Erkenne die 5 A3-Phasen anhand der Nummerierung
        if clean_line.strip().startswith(("1. ", "2. ", "3. ", "4. ", "5. ")):
            # ---> ÜBERSCHRIFT (Grauer Balken)
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.set_fill_color(230, 230, 230) # Hellgrau
            pdf.cell(0, 8, txt=clean_line, ln=True, align='L', fill=True)
            pdf.set_font("Arial", '', 11)
            
        # Listenpunkte
        elif clean_line.strip().startswith("-") or clean_line.strip().startswith("*"):
            pdf.set_font("Arial", '', 11)
            pdf.set_x(15) 
            pdf.multi_cell(0, 6, txt=clean_line)
            pdf.set_x(10)
            
        else:
            # Normaler Text
            if clean_line.strip() == "":
                pdf.ln(2)
            else:
                pdf.set_font("Arial", '', 11)
                pdf.multi_cell(0, 6, txt=clean_line)

    # HIER WURDE DER FOOTER GELÖSCHT
    # Keine "Generiert durch..." Zeile mehr -> Keine extra Seite!
    
    return pdf.output(dest='S').encode('latin-1')

# --- 4. PDF UPLOADER ---
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

# --- 5. SYSTEM PROMPT (ANGEMPASST AN DEIN BILD) ---
SYSTEM_PROMPT = """
Du bist ein Experte für industrielle Problemlösung (A3-Methode).
Du befindest dich in Schritt 5: "Standardize & Reapply".

Deine Aufgabe:
Erstelle basierend auf dem gelösten Problem einen Inhalt für das "A3-Summary Sheet".

Strukturiere deine Antwort EXAKT nach diesen 5 Überschriften (Achte auf die Nummerierung!):

1. Understand the situation
   - Fasse die "Problem Investigation" (6W-2H) kurz zusammen.
   - Bewerte den Business Impact (Kosten, Qualität, Sicherheit).

2. Root Cause Investigation
   - Nenne die identifizierte "True Cause" (aus der 5-Why Analyse).
   - Erkläre kurz, warum das Problem nicht früher entdeckt wurde ("Why it passed").

3. Countermeasures
   - Beschreibe die Lösung, die implementiert wurde.
   - Erwähne technische Details (Teilenummern, IP-Schutzklassen etc.).

4. Sustain Results
   - Beschreibe, wie die Lösung standardisiert wird (SOPs, Wartungspläne).
   - Welche Dokumente müssen aktualisiert werden? (FMEA, Control Plan).

5. Reapplication and Next steps
   - Copy Exact: Wo kann die Lösung 1:1 übernommen werden?
   - Reapplication at other lines: Wo ist das Prinzip übertragbar?

WICHTIG:
- Sei präzise und technisch.
- Verzichte auf Emojis, damit das PDF sauber generiert werden kann.
- Nutze Spiegelstriche für Listen.
"""

# --- 6. VERBINDUNG HERSTELLEN & CHAT ---
if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # Modell-Wahl
        verfuegbare_modelle = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                verfuegbare_modelle.append(m.name)
        
        modell_name = 'models/gemini-pro'
        if modell_name not in verfuegbare_modelle and verfuegbare_modelle:
            modell_name = verfuegbare_modelle[0]
        
        model = genai.GenerativeModel(modell_name)

        if "messages" not in st.session_state:
            st.session_state.messages = []
            st.session_state.chat = model.start_chat(history=[
                {"role": "user", "parts": ["Instruktion: " + SYSTEM_PROMPT]},
                {"role": "model", "parts": ["Verstanden. Ich erstelle das A3-Summary nach den 5 Phasen."]}
            ])

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # --- INPUT LOGIK ---
        user_input = None
        display_text = None
        
        if pdf_text and st.sidebar.button("PDF Analysieren"):
            user_input = f"Analysiere diesen Report für das A3 Sheet:\n\n{pdf_text}"
            display_text = "📂 *PDF-Analyse gestartet...*"
        
        elif prompt := st.chat_input("Beschreibe dein Problem..."):
            user_input = prompt
            display_text = prompt

        if user_input and display_text:
            st.session_state.messages.append({"role": "user", "content": display_text})
            with st.chat_message("user"):
                st.markdown(display_text)

            try:
                response = st.session_state.chat.send_message(user_input)
                bot_text = response.text
                
                st.session_state.messages.append({"role": "assistant", "content": bot_text})
                with st.chat_message("assistant"):
                    st.markdown(bot_text)
                    
                    st.markdown("---")
                    pdf_data = create_pdf(bot_text)
                    st.download_button(
                        label="📥 A3-Sheet als PDF herunterladen",
                        data=pdf_data,
                        file_name="A3_Summary_Result.pdf",
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"Fehler: {e}")

    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
else:
    st.info("⬅️ Bitte gib links deinen API Key ein.")

