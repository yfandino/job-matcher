"""
Módulo para la pipeline de ranking de candidatos.
"""

import os
import re
from typing import Dict, List

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# --- Configuración Inicial ---
load_dotenv()
if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("GOOGLE_API_KEY no encontrada en el fichero .env")


def get_semantic_scores(
    job_description: str, cv_corpus: Dict[str, str]
) -> List[Dict[str, float]]:
    """
    Calcula la similitud semántica entre una oferta de trabajo y una lista de CVs.

    Este es el primer paso de filtrado (similar a un RAG) que nos da una puntuación
    inicial basada en la coincidencia conceptual.

    Args:
        job_description: El texto de la oferta de trabajo.
        cv_corpus: Un diccionario donde las claves son los nombres de archivo de los CVs
                   y los valores son el contenido de los mismos.

    Returns:
        Una lista de diccionarios, cada uno con 'candidate' (nombre del archivo)
        y 'semantic_score' (puntuación de similitud de 0 a 10).
    """
    try:
        embeddings_model = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")

        # Crear embeddings para los CVs
        cv_texts = list(cv_corpus.values())
        cv_names = list(cv_corpus.keys())

        # Usar FAISS para la búsqueda de similitud
        # LangChain FAISS wrapper maneja la creación de embeddings y el índice
        vector_store = FAISS.from_texts(
            cv_texts, embeddings_model, metadatas=[{"name": name} for name in cv_names]
        )

        # La función de similitud devuelve documentos y sus puntuaciones de similitud.
        # Una puntuación más BAJA significa MÁS similar en FAISS.
        # Por defecto, usa distancia L2.
        results_with_scores = vector_store.similarity_search_with_score(
            job_description, k=len(cv_names)
        )

        scores = []
        for doc, score in results_with_scores:
            # La distancia L2 no está acotada. La convertiremos a una escala 0-10.
            # 1. Invertir la puntuación (más alto es mejor)
            # 2. Normalizar
            # Esta es una forma simple de normalización; en un sistema real podría ser más sofisticada.
            normalized_score = 1 / (1 + score)  # Invertir y acotar entre 0 y 1

            scores.append(
                {
                    "candidate": doc.metadata["name"],
                    # Escalar a 10 y redondear
                    "semantic_score": round(normalized_score * 10, 2),
                }
            )

        return scores

    except Exception as e:
        print(f"Error durante el cálculo de la puntuación semántica: {e}")
        return []


# --- Funciones de Re-Ranking ---


def get_hard_skills_score(cv_text: str, required_skills: List[str]) -> Dict[str, float]:
    """
    Calcula una puntuación basada en la presencia de skills duros obligatorios.

    Args:
        cv_text: El texto del CV.
        required_skills: Una lista de skills que se deben buscar.

    Returns:
        Un diccionario con la puntuación 'hard_skills_score' de 0 a 10.
    """
    if not required_skills:
        return {"hard_skills_score": 0}

    found_skills = 0
    cv_text_lower = cv_text.lower()

    for skill in required_skills:
        # Búsqueda simple, se puede mejorar con regex para evitar falsos positivos
        if skill.lower() in cv_text_lower:
            found_skills += 1

    score = (found_skills / len(required_skills)) * 10
    return {"hard_skills_score": round(score, 2)}


def get_subjective_attribute_score(cv_text: str, attribute: str) -> Dict[str, any]:
    """
    Evalúa un atributo subjetivo de un candidato usando un LLM (Gemini) con LCEL.

    Args:
        cv_text: El texto del CV.
        attribute: El atributo a evaluar (ej. "proactividad", "liderazgo").

    Returns:
        Un diccionario con 'subjective_score' (0-10) y 'justification' (texto).
    """
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)

        prompt_template = PromptTemplate(
            input_variables=["cv_text", "attribute"],
            template="""
            Analiza el siguiente CV y evalúa el atributo: '{attribute}'.
            Basándote ÚNICAMENTE en la evidencia explícita del texto, proporciona:
            1. Una puntuación de 1 a 10.
            2. Una justificación de una sola frase.

            Formato de respuesta OBLIGATORIO: Puntuación: [tu puntuación] | Justificación: [tu justificación]

            CV:
            ---
            {cv_text}
            ---
            """,
        )

        output_parser = StrOutputParser()

        # Construcción de la cadena usando LangChain Expression Language (LCEL)
        chain = prompt_template | llm | output_parser

        response_text = chain.invoke({"cv_text": cv_text, "attribute": attribute})

        # Parsear la respuesta
        score_match = re.search(
            r"Puntuación:\s*(\d+\.?\d*)", response_text, re.IGNORECASE
        )
        justification_match = re.search(
            r"Justificación:\s*(.*)", response_text, re.IGNORECASE
        )

        score = float(score_match.group(1)) if score_match else 0.0
        justification = (
            justification_match.group(1).strip()
            if justification_match
            else "No se pudo generar una justificación."
        )

        return {"subjective_score": score, "justification": justification}

    except Exception as e:
        print(f"Error durante la evaluación subjetiva para '{attribute}': {e}")
        return {
            "subjective_score": 0.0,
            "justification": "Error al procesar la evaluación.",
        }


# --- Orquestación de la Pipeline ---


def run_ranking_pipeline(
    job_description: str,
    cv_corpus: Dict[str, str],
    hard_skills: List[str],
    subjective_attribute: str,
    weights: Dict[str, float],
) -> List[Dict[str, any]]:
    """
    Orquesta la pipeline completa de ranking de candidatos.

    Args:
        job_description: El texto de la oferta de trabajo.
        cv_corpus: Diccionario con los CVs (nombre_archivo: contenido).
        hard_skills: Lista de skills duros a evaluar.
        subjective_attribute: Atributo subjetivo a evaluar.
        weights: Diccionario con los pesos para cada puntuación
                 (ej. {'semantic': 0.4, 'hard': 0.4, 'subjective': 0.2}).

    Returns:
        Una lista de diccionarios, cada uno representando a un candidato,
        ordenada por la puntuación final.
    """
    # Paso 1: Obtener puntuaciones semánticas para todos los candidatos
    semantic_results = get_semantic_scores(job_description, cv_corpus)

    # Crear un diccionario para un acceso más fácil
    candidate_data = {result["candidate"]: result for result in semantic_results}

    # Pasos 2 y 3: Aplicar re-ranking
    for name, cv_text in cv_corpus.items():
        if name in candidate_data:
            # Puntuación de skills duros
            hard_skills_result = get_hard_skills_score(cv_text, hard_skills)
            candidate_data[name].update(hard_skills_result)

            # Puntuación subjetiva
            subjective_result = get_subjective_attribute_score(
                cv_text, subjective_attribute
            )
            candidate_data[name].update(subjective_result)

    # Paso 4: Calcular puntuación final ponderada
    ranked_candidates = []
    for name, data in candidate_data.items():
        final_score = (
            data.get("semantic_score", 0) * weights.get("semantic", 0)
            + data.get("hard_skills_score", 0) * weights.get("hard", 0)
            + data.get("subjective_score", 0) * weights.get("subjective", 0)
        )
        data["final_score"] = round(final_score, 2)
        ranked_candidates.append(data)

    # Ordenar candidatos por la puntuación final de mayor a menor
    ranked_candidates.sort(key=lambda x: x["final_score"], reverse=True)

    return ranked_candidates


# --- Bloque de Prueba para CLI ---

if __name__ == "__main__":
    print("--- Iniciando prueba de la pipeline de ranking desde CLI ---")

    # 1. Cargar datos de prueba
    try:
        with open("ranking_poc/data/job_description.txt", "r", encoding="utf-8") as f:
            job_desc_text = f.read()

        cv_files_path = "ranking_poc/cvs/"
        cv_files = [f for f in os.listdir(cv_files_path) if f.endswith(".txt")]

        corpus = {}
        for cv_file in cv_files:
            with open(os.path.join(cv_files_path, cv_file), "r", encoding="utf-8") as f:
                corpus[cv_file] = f.read()

        print(f"Cargados {len(corpus)} CVs y la descripción del puesto.")

    except FileNotFoundError as e:
        print(f"Error: No se encontró el archivo o directorio: {e}")
        print("Asegúrate de ejecutar este script desde la raíz del proyecto.")
        exit(1)

    # 2. Definir parámetros de la prueba
    test_hard_skills = ["Python", "RAG", "FAISS", "Google Gemini", "SQL"]
    test_subjective_attribute = "Proactividad"
    test_weights = {"semantic": 0.4, "hard": 0.4, "subjective": 0.2}

    print("\nParámetros de prueba:")
    print(f"  - Skills Duros: {', '.join(test_hard_skills)}")
    print(f"  - Atributo Subjetivo: {test_subjective_attribute}")
    print(
        f"  - Pesos: Semántico={test_weights['semantic'] * 100}%, Duros={test_weights['hard'] * 100}%, Subjetivo={test_weights['subjective'] * 100}%"
    )

    # 3. Ejecutar la pipeline
    print(
        "\n--- Ejecutando pipeline... (esto puede tardar unos segundos por las llamadas al LLM) ---"
    )
    final_ranking = run_ranking_pipeline(
        job_description=job_desc_text,
        cv_corpus=corpus,
        hard_skills=test_hard_skills,
        subjective_attribute=test_subjective_attribute,
        weights=test_weights,
    )

    # 4. Mostrar resultados
    print("\n--- Ranking Final de Candidatos ---")
    for i, candidate in enumerate(final_ranking):
        print(f"\n{i + 1}. Candidato: {candidate['candidate']}")
        print(f"   Puntuación Final: {candidate['final_score']:.2f}/10.00")
        print("   --- Desglose ---")
        print(f"   - P. Semántica:   {candidate.get('semantic_score', 0):.2f}/10.00")
        print(
            f"   - P. Skills Duros:  {candidate.get('hard_skills_score', 0):.2f}/10.00"
        )
        print(
            f"   - P. Subjetiva:     {candidate.get('subjective_score', 0):.2f}/10.00"
        )
        print(f"   - Justificación IA: {candidate.get('justification', 'N/A')}")

    print("\n--- Prueba finalizada ---")
