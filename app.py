import json
import os
import re
import tempfile
import time
from collections import namedtuple
from pathlib import Path

import streamlit as st

# Importar el creador del agente
from resume_parser_agent.agent import create_agent_executor

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("AI Resume Analyzer")

# --- Controles en la barra lateral ---
st.sidebar.title("Controls")
google_api_key = st.sidebar.text_input("Enter your Google API Key", type="password")

resume_file = st.sidebar.file_uploader(
    "Upload Resume", type=["pdf", "txt"], accept_multiple_files=False
)
job_description_file = st.sidebar.file_uploader(
    "Upload Job Description", type=["pdf", "txt"], accept_multiple_files=False
)

analyze_button = st.sidebar.button("Analyze")


# Estructura para el resultado del análisis
AnalysisResult = namedtuple(
    "AnalysisResult", ["score", "resume_skills", "job_skills", "analysis"]
)


def parse_analysis(text: str) -> AnalysisResult:
    """Parsea el texto markdown estructurado del agente a un objeto."""

    # Extraer las habilidades del currículum
    resume_skills_match = re.search(
        r"\*\*1\. Skills found in the resume:\*\*\n(.*?)\n\*\*2\.", text, re.DOTALL
    )

    # Extraer las habilidades del trabajo
    job_skills_match = re.search(
        r"\*\*2\. Skills required by the job:\*\*\n(.*?)\n\*\*3\.", text, re.DOTALL
    )

    # Extraer el puntaje
    score_match = re.search(
        r"\*\*3\. Match Score:\*\*(.*?)\*\*4\.", text, re.DOTALL | re.IGNORECASE
    )

    # Extraer las observaciones
    analysis_match = re.search(
        r"\*\*4\. Relevant observations about the match:\*\*\n(.*)", text, re.DOTALL
    )

    def extract_skills_from_md(md_text):
        if not md_text:
            return []
        return [
            line.strip("- *").strip()
            for line in md_text.strip().split("\n")
            if line.strip()
        ]

    resume_skills = extract_skills_from_md(
        resume_skills_match.group(1) if resume_skills_match else ""
    )
    job_skills = extract_skills_from_md(
        job_skills_match.group(1) if job_skills_match else ""
    )
    score = score_match.group(1).strip() if score_match else "0%"
    analysis = (
        analysis_match.group(1).strip() if analysis_match else "No analysis provided."
    )

    return AnalysisResult(score, resume_skills, job_skills, analysis)


# --- Lógica de análisis y visualización ---
if analyze_button:
    if not google_api_key:
        st.error("Please enter your Google API Key.")
    elif not resume_file or not job_description_file:
        st.error("Please upload both a resume and a job description.")
    else:
        os.environ["GOOGLE_API_KEY"] = google_api_key

        with st.spinner("Analyzing... This may take a moment.", show_time=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)

                # Guardar archivos subidos a un directorio temporal
                resume_path = temp_dir_path / resume_file.name
                with open(resume_path, "wb") as f:
                    f.write(resume_file.getbuffer())

                job_path = temp_dir_path / job_description_file.name
                with open(job_path, "wb") as f:
                    f.write(job_description_file.getbuffer())

                # Crear agente y ejecutar análisis
                agent = create_agent_executor()

                input_text = f"""Analyze the resume at '{resume_path}' against the job description at '{job_path}'.

Provide:
1. A list of skills found in the resume
2. A list of skills required by the job
3. A match score between 0.0 and 1.0 (e.g., 85%)
4. Any relevant observations about the match, formatted as markdown."""

                start_time = time.time()
                result = agent.invoke({"messages": [("user", input_text)]})
                end_time = time.time()

                duration = end_time - start_time
                st.session_state.analysis_duration = duration

                # Guardar el resultado en el estado de la sesión
                final_message = result["messages"][-1]

                content = final_message.content
                text_to_parse = ""
                if isinstance(content, list):
                    # Unir el texto de todas las partes si es una lista de dicts
                    text_to_parse = "".join(
                        part.get("text", "")
                        for part in content
                        if isinstance(part, dict) and part.get("type") == "text"
                    )
                elif isinstance(content, str):
                    text_to_parse = content

                st.session_state.analysis_result = text_to_parse

if "analysis_result" in st.session_state:
    parsed_result = parse_analysis(st.session_state.analysis_result)

    # UI para el puntaje
    st.subheader("Match Score")

    if "analysis_duration" in st.session_state and st.session_state.analysis_duration:
        st.caption(
            f"Analysis completed in {st.session_state.analysis_duration:.2f} seconds"
        )

    st.metric(label="Score", value=parsed_result.score)
    try:
        score_text = parsed_result.score
        score_value = 0.0

        # Find all numbers (int or float) in the string
        numbers = re.findall(r"(\d+(?:\.\d+)?)", score_text)

        if numbers:
            # Convert string numbers to floats
            float_numbers = [float(n) for n in numbers]

            # Prefer numbers that look like percentages (e.g., 90) over floats (e.g., 0.9)
            percentages = [n for n in float_numbers if n > 1]

            if percentages:
                score_value = percentages[0] / 100.0
            else:
                # Otherwise, take the first number found (should be a float like 0.9)
                score_value = float_numbers[0]

        # Clamp the value to be safe for st.progress
        score_value = max(0.0, min(1.0, score_value))
        st.progress(score_value)
    except (ValueError, TypeError):
        st.progress(0.0)
    st.divider()

    # UI para las habilidades
    st.subheader("Skills Comparison")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Resume Skills")
        if parsed_result.resume_skills:
            st.markdown(
                "\n".join(f"- {skill}" for skill in parsed_result.resume_skills)
            )
        else:
            st.warning("No skills extracted from resume.")
    with col2:
        st.markdown("#### Job Skills")
        if parsed_result.job_skills:
            st.markdown("\n".join(f"- {skill}" for skill in parsed_result.job_skills))
        else:
            st.warning("No skills extracted from job description.")
    st.divider()

    # UI para el análisis
    st.subheader("Analysis")
    st.info(parsed_result.analysis)

    # Mostrar el resultado raw del agente
    with st.expander("Show Raw Agent Output"):
        st.text(st.session_state.analysis_result)
