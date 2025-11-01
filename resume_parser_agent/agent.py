"""Agent definition for resume analysis."""

from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from resume_parser_agent.tools import calculate_match_score, extract_skills, read_file


def create_agent_executor():
    """Create and return a configured agent executor."""

    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

    tools = [read_file, extract_skills, calculate_match_score]

    # The system prompt is a simple string. The create_agent function
    # will handle the full prompt structure.
    system_prompt_text = """You are an AI assistant that analyzes resumes against job descriptions.

Your goal is to:
1. Read the resume file and job description file
2. Extract skills from both documents
3. Calculate a match score between the resume skills and job requirements
4. Provide a structured analysis of the match
"""

    agent = create_agent(model, tools=tools, system_prompt=system_prompt_text)

    return agent
