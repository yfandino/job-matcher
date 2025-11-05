"""
Aplicación de Streamlit para el POC de Ranking Multi-Factorial de Candidatos.
"""

import os

import streamlit as st
from ranking_pipeline import run_ranking_pipeline

# --- Configuración de la Página ---
st.set_page_config(
    page_title="POC Ranking de Candidatos",
    page_icon="🏅",
    layout="wide",
)

st.title("🏅 POC: Sistema de Ranking Multi-Factorial de Candidatos")
st.markdown(
    "Esta aplicación demuestra un sistema de ranking híbrido que combina búsqueda semántica, "
    "evaluación de skills duros y análisis de atributos subjetivos con un LLM."
)

# --- Funciones de Carga de Datos ---


@st.cache_data
def load_file_content(file_path):
    """Carga el contenido de un archivo de texto."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"Archivo no encontrado: {file_path}")
        return ""


@st.cache_data
def load_cv_corpus(cv_dir):
    """Carga todos los CVs de un directorio."""
    corpus = {}
    try:
        for filename in os.listdir(cv_dir):
            if filename.endswith(".txt"):
                file_path = os.path.join(cv_dir, filename)
                corpus[filename] = load_file_content(file_path)
        return corpus
    except FileNotFoundError:
        st.error(f"Directorio de CVs no encontrado: {cv_dir}")
        return {}


# --- Barra Lateral de Configuración ---

with st.sidebar:
    st.header("⚙️ Parámetros de Evaluación")

    # Cargar descripción del puesto por defecto
    default_jd = load_file_content("ranking_poc/data/job_description.txt")
    job_description = st.text_area(
        "📝 Descripción del Puesto",
        value=default_jd,
        height=300,
        help="Pega aquí la oferta de trabajo. Se ha cargado un ejemplo por defecto.",
    )

    hard_skills_input = st.text_input(
        "🛠️ Skills Obligatorios (separados por coma)",
        value="Python, RAG, FAISS, Google Gemini, SQL",
        help="Introduce los skills no negociables. Ej: Python, AWS, Docker",
    )

    subjective_attribute = st.text_input(
        "🧠 Atributo Subjetivo a Evaluar",
        value="Proactividad",
        help="Introduce el atributo blando que el LLM debe evaluar. Ej: Liderazgo, Trabajo en equipo",
    )

    st.markdown("---")
    st.header("⚖️ Ponderación de Puntuaciones")

    # Sliders para los pesos
    semantic_weight = st.slider(
        "Peso Semántico (%)",
        0,
        100,
        40,
        5,
        help="Importancia del 'fit' general y la coincidencia conceptual.",
    )
    hard_skills_weight = st.slider(
        "Peso de Skills Duros (%)",
        0,
        100,
        40,
        5,
        help="Importancia de los requisitos técnicos no negociables.",
    )
    subjective_weight = st.slider(
        "Peso Subjetivo (%)",
        0,
        100,
        20,
        5,
        help="Importancia del atributo evaluado por el LLM.",
    )

# --- Funciones de Visualización ---


def display_results(ranked_candidates, subjective_attribute):
    """Muestra los resultados del ranking en tarjetas expandibles."""
    st.subheader("🏆 Ranking Final de Candidatos")

    for i, candidate in enumerate(ranked_candidates):
        rank = i + 1
        name = (
            candidate.get("candidate", "N/A")
            .replace(".txt", "")
            .replace("_", " ")
            .title()
        )

        with st.expander(
            f"**#{rank} - {name}** | Puntuación Final: **{candidate.get('final_score', 0):.2f}**"
        ):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    label="🔗 Similitud Semántica",
                    value=f"{candidate.get('semantic_score', 0):.2f} / 10",
                )
            with col2:
                st.metric(
                    label="🛠️ Skills Duros",
                    value=f"{candidate.get('hard_skills_score', 0):.2f} / 10",
                )
            with col3:
                st.metric(
                    label=f"🧠 {subjective_attribute.title()}",
                    value=f"{candidate.get('subjective_score', 0):.2f} / 10",
                )

            st.markdown("**Justificación de la IA:**")
            st.info(f"_{candidate.get('justification', 'No disponible.')}_")


# --- Lógica Principal y Visualización ---

# Botón para iniciar el ranking
if st.button("🚀 Rank Candidates", type="primary"):
    # Normalizar los pesos para que sumen 1
    total_weight = semantic_weight + hard_skills_weight + subjective_weight
    if total_weight == 0:
        st.error(
            "La suma de los pesos no puede ser cero. Por favor, ajusta los sliders."
        )
    else:
        weights = {
            "semantic": semantic_weight / total_weight,
            "hard": hard_skills_weight / total_weight,
            "subjective": subjective_weight / total_weight,
        }

        # Convertir skills a lista
        hard_skills = [skill.strip() for skill in hard_skills_input.split(",")]

        # Cargar CVs
        cv_corpus = load_cv_corpus("ranking_poc/cvs/")

        if not job_description or not cv_corpus:
            st.warning(
                "Por favor, asegúrate de que la descripción del puesto y los CVs estén cargados."
            )
        else:
            with st.spinner(
                f"Procesando {len(cv_corpus)} CVs... Esto puede tardar unos segundos..."
            ):
                # Llamada a la pipeline de ranking
                final_ranking = run_ranking_pipeline(
                    job_description=job_description,
                    cv_corpus=cv_corpus,
                    hard_skills=hard_skills,
                    subjective_attribute=subjective_attribute,
                    weights=weights,
                )

            # Mostrar resultados
            display_results(final_ranking, subjective_attribute)


else:
    st.info(
        "Ajusta los parámetros en la barra lateral y haz clic en 'Rank Candidates' para comenzar."
    )
