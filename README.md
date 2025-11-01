# AI Resume Analyzer Agent

A lightweight exploration of AI agents using LangChain. This project analyzes resumes against job descriptions using custom tools in a reasoning loop.

## Setup

1. **Install dependencies using uv:**
   ```bash
   uv sync
   ```

2. **Set up your Google AI Studio API key:**
   Create a `.env` file in the project root:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```
   
   To get your API key:
   1. Go to [Google AI Studio](https://aistudio.google.com)
   2. Sign in with your Google account
   3. Click "Get API key" and create a new key
   4. Copy the key and add it to your `.env` file

## Usage

### Step 1: Install dependencies
```bash
uv sync
```

### Step 2: Set up your Google AI Studio API key
Create a `.env` file in the project root:
```
GOOGLE_API_KEY=your_google_api_key_here
```

To get your API key:
1. Go to [Google AI Studio](https://aistudio.google.com)
2. Sign in with your Google account
3. Click "Get API key" and create a new key
4. Copy the key and add it to your `.env` file

### Step 3: Run the agent
Run the agent with a resume and job description:

```bash
uv run python main.py <resume_path> <job_description_path>
```

**Examples:**

Using the example files provided:
```bash
uv run python main.py resumes/example_resume.txt job_descriptions/example_job.txt
```

With your own PDF resume:
```bash
uv run python main.py resumes/my_resume.pdf job_descriptions/job.txt
```

With absolute paths:
```bash
uv run python main.py /path/to/resume.pdf /path/to/job_description.txt
```

### What the agent does:
1. Reads both the resume and job description files
2. Extracts skills from each document using an LLM
3. Calculates a match score (0.0 to 1.0) between the skills
4. Provides a structured analysis with recommendations

**Supported file formats:** `.txt` and `.pdf` files

## Project Structure

- `resume_parser_agent/` - Main package
  - `tools.py` - Custom tools (file reader, skill extractor, match score calculator)
  - `agent.py` - LangChain agent definition
- `main.py` - CLI entry point
- `resumes/` - Directory for resume files
- `job_descriptions/` - Directory for job description files

## Tools

The agent has access to three custom tools:

1. **read_file**: Reads text content from .txt or .pdf files
2. **extract_skills**: Uses an LLM to extract skills from text
3. **calculate_match_score**: Calculates a match score (0.0 to 1.0) between two skill lists

## Requirements

- Python 3.9+
- Google AI Studio API key (free tier available)
- uv (for package management)

## Model Information

This project uses **Gemini 2.5 Pro** via Google AI Studio, which offers:
- Free tier with generous usage limits
- Fast response times
- Good performance for structured tasks

