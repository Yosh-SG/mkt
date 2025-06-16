import streamlit as st
import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import spacy

# Cargar modelo de lenguaje en español
try:
    nlp = spacy.load("es_core_news_sm")
except:
    st.warning("Descargando modelo de spaCy...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "es_core_news_sm"])
    nlp = spacy.load("es_core_news_sm")

# Función para limpiar y tokenizar el texto
def clean_text(text):
    text = re.sub(r'\s+', ' ', text.lower())
    text = re.sub(r'[^a-záéíóúüñ0-9 ]', '', text)
    return text

# Stopwords básicas
STOPWORDS = set([
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", 
    "para", "con", "no", "una", "su", "al", "lo", "como", "más", "pero", "sus", "le"
])

def extract_keywords(text):
    text = clean_text(text)
    words = [token.text for token in nlp(text) if token.is_alpha and token.text not in STOPWORDS and len(token.text) > 3]
    return Counter(words)

def extract_semantic_keywords(text):
    doc = nlp(text)
    lemas = [token.lemma_ for token in doc if token.is_alpha and token.text not in STOPWORDS and len(token.text) > 3]
    return Counter(lemas)

def extract_seo_elements(soup):
    return {
        "Title": soup.title.string.strip() if soup.title else "No encontrado",
        "Meta Description": soup.find("meta", {"name": "description"}).get("content", "") if soup.find("meta", {"name": "description"}) else "No encontrada",
        "Meta Keywords": soup.find("meta", {"name": "keywords"}).get("content", "") if soup.find("meta", {"name": "keywords"}) else "No encontradas",
        "H1": [h.get_text(strip=True) for h in soup.find_all("h1")],
        "H2": [h.get_text(strip=True) for h in soup.find_all("h2")],
        "H3": [h.get_text(strip=True) for h in soup.find_all("h3")],
    }

def generate_wordcloud(counter):
    wc = WordCloud(width=800, height=400, background_color="white").generate_from_frequencies(counter)
    fig, ax = plt.subplots()
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig)

# Streamlit App
st.set_page_config(page_title="Análisis SEO de URL", layout="wide")
st.title("🔎 Analizador de Palabras Clave y SEO On-Page")
st.markdown("Introduce la URL de tu competidor para analizar títulos, metaetiquetas y extraer palabras clave semánticamente relevantes.")

url = st.text_input("Introduce una URL (con http/https):", "https://")

if st.button("Analizar"):
    if not url.startswith("http"):
        st.error("Por favor, introduce una URL válida que comience con http o https.")
    else:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            seo = extract_seo_elements(soup)
            text = soup.get_text()
            keywords = extract_keywords(text)
            semantic_keywords = extract_semantic_keywords(text)

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🎯 Elementos SEO")
                for k, v in seo.items():
                    if isinstance(v, list):
                        st.markdown(f"**{k}:**")
                        for item in v:
                            st.markdown(f"- {item}")
                    else:
                        st.markdown(f"**{k}:** {v}")

            with col2:
                st.subheader("🔑 Palabras clave más frecuentes")
                st.dataframe(Counter(keywords).most_common(20), use_container_width=True)

            st.subheader("🧠 Palabras clave semánticas (lematizadas)")
            st.dataframe(Counter(semantic_keywords).most_common(20), use_container_width=True)

            st.subheader("☁️ Nube de palabras clave")
            generate_wordcloud(keywords)

        except Exception as e:
            st.error(f"Ocurrió un error: {e}")
