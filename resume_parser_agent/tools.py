"""Custom tools for the resume analyzer agent."""

import json
from pathlib import Path
from typing import List, Union

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from PyPDF2 import PdfReader

load_dotenv()


@tool
def read_file(file_path: str) -> str:
    """
    Read the text content from a file.

    Args:
        file_path: Path to the file (.txt or .pdf)

    Returns:
        The text content of the file
    """
    path = Path(file_path)

    if not path.exists():
        return f"Error: File not found at {file_path}"

    if path.suffix.lower() == ".txt":
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    elif path.suffix.lower() == ".pdf":
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        # Sanitize the text to remove null bytes that can corrupt the file
        text = text.replace("\x00", "")

        # Save the extracted text to a .txt file
        txt_path = path.with_suffix(".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)

        return text
    else:
        return f"Error: Unsupported file type. Only .txt and .pdf are supported."

    return ""


@tool
def extract_skills(text: str) -> str:
    """
    Extract a list of skills from a block of text using an LLM.

    Args:
        text: The text block to extract skills from

    Returns:
        A JSON string containing a list of skills found in the text
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)

    prompt = f"""Extract all technical and professional skills from the following text.
Return only a comma-separated list of skills, nothing else.

Text:
{text}

Skills:"""

    response = llm.invoke(prompt)
    skills_text = response.content.strip()

    # Parse the comma-separated list
    skills = [skill.strip() for skill in skills_text.split(",") if skill.strip()]

    # Return as JSON string for agent compatibility
    return json.dumps(skills)


@tool
def calculate_match_score(resume_skills: str, job_skills: str) -> float:
    """
    Calculate a semantic match score between two lists of skills using an LLM.

    Args:
        resume_skills: JSON string of skills from the resume
        job_skills: JSON string of skills required by the job

    Returns:
        A match score between 0.0 and 1.0
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

    prompt = f"""
        You are an expert recruiter analyzing a candidate's skills against a job description.
        Your task is to provide a match score from 0.0 to 1.0.

        Consider that skills can be related even if the wording is not identical.
        For example, 'Cloud Architecture' in a resume is a strong match for 'Architecture' in a job description.
        'LLM experience' is a match for 'AI Orchestration'.

        Here are the skills from the job description:
        {job_skills}

        Here are the skills from the candidate's resume:
        {resume_skills}

        Based on a semantic comparison of these two lists, what is the match score?
        Return only a single floating-point number (e.g., 0.85), and nothing else.
    """

    response = llm.invoke(prompt)
    try:
        score = float(response.content.strip())
        return round(score, 2)
    except (ValueError, TypeError):
        # Fallback to a simple match score if the LLM fails to return a valid number
        try:
            job_skills = json.loads(job_skills)
        except json.JSONDecodeError:
            return 0.0

    if not job_skills:
        return 0.0

    # Normalize skills to lowercase for comparison
    resume_skills_normalized = [skill.lower().strip() for skill in resume_skills]
    job_skills_normalized = [skill.lower().strip() for skill in job_skills]

    # Count matches
    matches = 0
    for job_skill in job_skills_normalized:
        # Check for exact matches or if job skill is contained in resume skills
        for resume_skill in resume_skills_normalized:
            if job_skill in resume_skill or resume_skill in job_skill:
                matches += 1
                break

    # Calculate score as percentage of job skills matched
    score = matches / len(job_skills_normalized)

    return round(score, 2)
