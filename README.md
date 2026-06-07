# Interview Question Generator

QuestionBomb is a Streamlit-based interview question generator and practice suite. It helps users create role-specific interview questions, optionally generate detailed answers, export content as text or PDF, and evaluate spoken or typed responses with AI feedback.

## Features

- Role-based interview question generation
- Customizable topic, difficulty, question count, and question types
- Optional answer generation for Q&A-style practice
- Multi-language generation support
- Export generated questions as `.txt` or `.pdf`
- Built-in user registration and login flow
- Session history persistence for the last 50 saved generations per user
- Voice interview mode with speech recognition and answer capture
- Text-to-speech playback of questions for spoken practice
- AI feedback scoring and improvement suggestions

## Tech Stack

- Python
- Streamlit
- Groq API (`groq` Python client)
- ReportLab for PDF export
- python-dotenv for environment configuration
- Web Speech API (browser-native) for text-to-speech and speech recognition

## Requirements

Install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

The core runtime dependencies include `streamlit`, `groq`, `python-dotenv`, and `reportlab` for PDF export.

## Setup

1. Create a virtual environment (recommended):

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your Groq API key:

```env
GROQ_API_KEY=your_api_key_here
```

4. Run the app:

```bash
streamlit run app.py
```

## Usage

1. Open the Streamlit app in your browser.
2. Register a new user or log in with an existing account.
3. Configure the job role, topic, difficulty, and question types.
4. Generate interview questions and optionally answers.
5. Download generated content as `.txt` or `.pdf`.
6. Use the Voice Interview Mode to practice answers and save them for AI feedback.
7. Click **Speak Question** to hear the selected question aloud before recording your answer.
8. Go to the AI Feedback tab to evaluate your answer and review strengths, improvements, and verdict.
9. Review past sessions in the Question History tab.

## Notes

- Authentication data is stored locally in `users.json`.
- Generated session history is stored locally in `question_history.json`.
- The app requires a valid `GROQ_API_KEY` set in the `.env` file.
- Voice recognition works best in supported browsers such as Chrome.
- Text-to-speech uses the browser's built-in Web Speech API — no additional installation required.
- Voice features (TTS + speech recognition) work best in Google Chrome on desktop.

## File Overview

- `app.py` — main Streamlit application file
- `requirements.txt` — Python dependencies
- `README.md` — project documentation
- `users.json` — local user auth storage (created at runtime)
- `question_history.json` — local session history storage (created at runtime)

## License

This project is provided as-is. Customize and extend it for your learning and interview preparation workflows.
