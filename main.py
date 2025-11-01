"""Main entry point for the resume analyzer agent."""

import argparse
import sys
from pathlib import Path

from resume_parser_agent.agent import create_agent_executor


def main():
    """Run the resume analyzer agent."""
    parser = argparse.ArgumentParser(
        description="Analyze a resume against a job description"
    )
    parser.add_argument(
        "resume_path", type=str, help="Path to the resume file (.txt or .pdf)"
    )
    parser.add_argument(
        "job_description_path",
        type=str,
        help="Path to the job description file (.txt or .pdf)",
    )

    args = parser.parse_args()

    # Validate file paths
    resume_path = Path(args.resume_path)
    job_path = Path(args.job_description_path)

    if not resume_path.exists():
        print(f"Error: Resume file not found: {resume_path}")
        sys.exit(1)

    if not job_path.exists():
        print(f"Error: Job description file not found: {job_path}")
        sys.exit(1)

    # Create agent and run analysis
    agent = create_agent_executor()

    input_text = f"""Analyze the resume at '{resume_path}' against the job description at '{job_path}'.

Provide:
1. A list of skills found in the resume
2. A list of skills required by the job
3. A match score between 0.0 and 1.0
4. Any relevant observations about the match"""

    print("\n" + "=" * 60)
    print("Resume Analyzer Agent")
    print("=" * 60 + "\n")

    # The new agent expects a "messages" list as input
    result = agent.invoke({"messages": [("user", input_text)]})

    print("\n" + "=" * 60)
    print("Analysis Result")
    print("=" * 60 + "\n")

    # The final response is in the "messages" list of the output
    final_message = result["messages"][-1]
    print(final_message.content)


if __name__ == "__main__":
    main()
