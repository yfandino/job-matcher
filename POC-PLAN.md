### **Plan de Acción Definitivo: POC de Sistema de Ranking Híbrido (Alternativa B)**

**Fase 1: Configuración del Entorno y Simulación de la Base de Datos**

*   **Tarea 1.1: Estructura del Proyecto:**
    *   Crear directorio `ranking_poc/` con subdirectorios `cvs/` (nuestra simulación de la base de datos de candidatos) y `data/`.
*   **Tarea 1.2: Crear Dataset de Prueba:**
    *   Crear los 5-7 CVs de ejemplo en `ranking_poc/cvs/`.
    *   Crear el archivo `ranking_poc/data/job_description.txt`.
*   **Tarea 1.3: Configurar Entorno con `uv`:**
    *   Crear `pyproject.toml` especificando Python `~=3.12` y las dependencias: `streamlit`, `langchain`, `langchain-google-genai`, `scikit-learn`, `python-dotenv`, `faiss-cpu`.
    *   Crear el `requirements.txt` correspondiente.

**Fase 2: Implementación de la Pipeline de Ranking (El "Backend")**

*   **Tarea 2.1: Crear Módulo de Lógica (`ranking_poc/ranking_pipeline.py`):**
    *   Este archivo contendrá todas las funciones de la pipeline.
*   **Tarea 2.2: Implementar la Búsqueda Semántica (Paso 1 del RAG):**
    *   Función `get_semantic_scores(cv_corpus, job_description)`: Tomará la oferta y todos los CVs, generará embeddings con `GoogleGenerativeAIEmbeddings`, y devolverá una lista de candidatos con su `score_semantico`.
*   **Tarea 2.3: Implementar la Lógica de Re-Ranking (Pasos 2 y 3):**
    *   Función `get_hard_skills_score(cv_text, required_skills)`: Lógica determinista para puntuar los skills duros.
    *   Función `get_subjective_attribute_score(cv_text, attribute)`: Usará LangChain para construir un `Chain` que llame a Gemini con un prompt estructurado, extraiga la puntuación y la justificación.
*   **Tarea 2.4: Orquestar la Pipeline Completa:**
    *   Función principal `run_ranking_pipeline(...)` que:
        1.  Toma la lista de candidatos pre-puntuada semánticamente.
        2.  Itera sobre cada candidato para aplicar las funciones de re-ranking (`hard_skills` y `subjective`).
        3.  Calcula la `puntuacion_final` ponderada para cada uno.
        4.  Devuelve una lista de candidatos ordenada de mayor a menor.

**Fase 3: Desarrollo de la Interfaz de Streamlit (El "Panel de Control")**

*   **Tarea 3.1: Crear Archivo Principal (`ranking_poc/app.py`):**
    *   Punto de entrada de la aplicación.
*   **Tarea 3.2: Diseñar la UI:**
    *   Implementar la barra lateral para la descripción del puesto, skills y atributo subjetivo.
    *   Añadir los *sliders* para los pesos, que controlarán la fórmula de la `puntuacion_final` en el backend.
    *   El botón `Rank Candidates` llamará a la función `run_ranking_pipeline`.

**Fase 4: Visualización de Resultados**

*   **Tarea 4.1: Mostrar el Ranking Final:**
    *   La aplicación tomará la lista final ordenada devuelta por la pipeline.
    *   Mostrará las "tarjetas" de cada candidato con su puntuación final, el desglose y la justificación del LLM.

**Fase 5: Documentación**

*   **Tarea 5.1: Crear `README.md`:**
    *   Documentación clara sobre cómo configurar el entorno con `uv` y ejecutar el POC.