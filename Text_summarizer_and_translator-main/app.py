import streamlit as st
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import defaultdict
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import pandas as pd
import docx
import PyPDF2
from deep_translator import GoogleTranslator

# ------------------ NLTK Setup ------------------ #
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

# ------------------ Summarizer ------------------ #
def summarize_text(text, max_sentences=5):
    sentences = sent_tokenize(text)

    if len(sentences) == 0:
        return "⚠️ No valid sentences found."

    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words("english"))

    freq = defaultdict(int)
    for w in words:
        if w.isalnum() and w not in stop_words:
            freq[w] += 1

    if not freq:
        return "⚠️ Unable to generate summary."

    sentence_scores = {}
    for sent in sentences:
        for w in word_tokenize(sent.lower()):
            if w in freq:
                sentence_scores[sent] = sentence_scores.get(sent, 0) + freq[w]

    summary = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:max_sentences]
    return " ".join(summary)

# ------------------ Extract Text ------------------ #
def extract_text_from_file(uploaded_file):
    try:
        if uploaded_file.type == "text/plain":
            return uploaded_file.read().decode("utf-8")

        elif uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text if text else "⚠️ No text found in PDF."

        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])

        elif uploaded_file.type == "text/csv":
            df = pd.read_csv(uploaded_file)
            return df.to_string()

        return "❌ Unsupported file type."

    except Exception as e:
        return f"❌ Error reading file: {e}"

# ------------------ PDF Generator ------------------ #
def generate_pdf(text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    story = []
    for line in text.split("\n"):
        story.append(Paragraph(line, styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ------------------ Translation ------------------ #
def translate_text(text, lang_code):
    try:
        return GoogleTranslator(source='auto', target=lang_code).translate(text)
    except Exception:
        return "❌ Translation failed. Try again."

# ------------------ Streamlit UI ------------------ #
st.set_page_config(page_title="Text Summarizer", layout="centered")
st.title("📄 Text Summarizer + 🌍 Translator")

# Session state
if "summary_text" not in st.session_state:
    st.session_state.summary_text = ""

if "translated_summary" not in st.session_state:
    st.session_state.translated_summary = ""

# Clear
if st.button("🗑️ Clear All"):
    st.session_state.clear()
    st.success("Cleared!")

# Text input
st.markdown("### ✏️ Enter Text")
user_text = st.text_area("Paste your text here...", height=200)

if user_text.strip() and st.button("✨ Summarize Text"):
    st.session_state.summary_text = summarize_text(user_text)

# File upload
st.markdown("### 📤 Upload File (.txt, .pdf, .docx, .csv)")
uploaded_file = st.file_uploader("Upload your file", type=["txt", "pdf", "docx", "csv"])

if uploaded_file:
    text = extract_text_from_file(uploaded_file)

    st.subheader("📜 Extracted Text")
    with st.expander("View Extracted Text"):
        st.write(text)

    if st.button("✨ Summarize File"):
        st.session_state.summary_text = summarize_text(text)

# Display summary
if st.session_state.summary_text:
    st.markdown("### ✍️ Summary")
    st.success(st.session_state.summary_text)

    st.download_button(
        "📥 Download Summary as PDF",
        generate_pdf(st.session_state.summary_text),
        "summary.pdf",
        "application/pdf"
    )

    # Translation
    st.markdown("### 🌍 Translate Summary")
    languages = {
        "English": "en",
        "Hindi": "hi",
        "Telugu": "te",
        "Tamil": "ta",
        "Kannada": "kn"
    }

    lang = st.selectbox("Select Language", list(languages.keys()))

    if st.button("🔁 Translate"):
        st.session_state.translated_summary = translate_text(
            st.session_state.summary_text,
            languages[lang]
        )

    if st.session_state.translated_summary:
        st.subheader(f"🌐 Translated Summary ({lang})")
        st.info(st.session_state.translated_summary)

# Info
if not user_text.strip() and uploaded_file is None:
    st.info("⬆️ Enter text or upload a file to start summarizing.")