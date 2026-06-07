import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os
import json
import hashlib
import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io

# ── Load Token ────────────────────────────────────────────
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ── Groq Client ───────────────────────────────────────────
client = Groq(api_key=GROQ_API_KEY)

# ── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="QuestionBomb 💣",
    page_icon="💣",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .header-title {
        font-size: 2.8rem; font-weight: 700;
        background: linear-gradient(135deg, #667eea, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 5px;
    }
    .header-sub {
        text-align: center; color: #888;
        font-size: 1rem; margin-bottom: 30px;
    }
    .question-card {
        background: #1e2130;
        border-left: 4px solid #667eea;
        border-radius: 8px;
        padding: 15px 20px;
        margin: 10px 0;
        color: #e0e0e0;
        font-size: 15px;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white; border: none;
        border-radius: 10px;
        padding: 12px 30px;
        font-weight: 600; font-size: 16px;
        width: 100%;
    }
    .stButton > button:hover { opacity: 0.85; }
    .history-card {
        background: #1a1d2e;
        border: 1px solid #2d3150;
        border-radius: 10px;
        padding: 12px 16px;
        margin: 8px 0;
        cursor: pointer;
    }
    .feedback-card {
        background: #0d1117;
        border-left: 4px solid #4ade80;
        border-radius: 8px;
        padding: 15px 20px;
        margin: 10px 0;
        color: #d1fae5;
    }
    .score-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 14px;
    }
    .tab-content { padding: 20px 0; }
    .voice-recording {
        background: #1e2130;
        border: 2px dashed #667eea;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .lang-badge {
        background: #667eea22;
        border: 1px solid #667eea;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 12px;
        color: #a78bfa;
    }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# ── AUTH SYSTEM (Session-based, no DB needed) ─────────────
# ════════════════════════════════════════════════════════════
USERS_FILE = "users.json"
HISTORY_FILE = "question_history.json"

def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    users = load_json(USERS_FILE, {})
    if username in users:
        return False, "Username already exists!"
    users[username] = {"password": hash_password(password), "created": str(datetime.datetime.now())}
    save_json(USERS_FILE, users)
    return True, "Registration successful!"

def login_user(username, password):
    users = load_json(USERS_FILE, {})
    if username not in users:
        return False, "User not found!"
    if users[username]["password"] != hash_password(password):
        return False, "Wrong password!"
    return True, "Login successful!"

# ── Init session state ─────────────────────────────────────
for key, val in {
    "logged_in": False,
    "username": "",
    "auth_mode": "login",
    "voice_answer": "",
    "current_questions": "",
    "current_meta": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ════════════════════════════════════════════════════════════
# ── AUTH PAGE ─────────────────────────────────────────────
# ════════════════════════════════════════════════════════════
def show_auth():
    st.markdown('<div class="header-title">💣 QuestionBomb</div>', unsafe_allow_html=True)
    st.markdown('<div class="header-sub">Drop questions like a pro — Please sign in to continue! 💥</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        mode = st.radio("", ["🔐 Login", "📝 Register"], horizontal=True, label_visibility="collapsed")
        st.session_state.auth_mode = "login" if "Login" in mode else "register"

        with st.container():
            username = st.text_input("👤 Username", placeholder="Enter username")
            password = st.text_input("🔑 Password", type="password", placeholder="Enter password")

            if st.session_state.auth_mode == "register":
                confirm = st.text_input("🔑 Confirm Password", type="password", placeholder="Confirm password")
                if st.button("📝 Create Account"):
                    if not username or not password:
                        st.error("Please fill all fields!")
                    elif password != confirm:
                        st.error("Passwords don't match!")
                    else:
                        ok, msg = register_user(username, password)
                        if ok:
                            st.success(msg + " Please login now.")
                        else:
                            st.error(msg)
            else:
                if st.button("🔐 Login"):
                    if not username or not password:
                        st.error("Please fill all fields!")
                    else:
                        ok, msg = login_user(username, password)
                        if ok:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

        st.markdown("---")
        st.info("💡 **Quick Demo**: Register any username/password to get started!")

# ════════════════════════════════════════════════════════════
# ── HISTORY ───────────────────────────────────────────────
# ════════════════════════════════════════════════════════════
def save_to_history(username, meta, result):
    history = load_json(HISTORY_FILE, {})
    if username not in history:
        history[username] = []
    history[username].insert(0, {
        "id": str(datetime.datetime.now().timestamp()),
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "role": meta.get("role", ""),
        "topic": meta.get("topic", ""),
        "difficulty": meta.get("difficulty", ""),
        "num_questions": meta.get("num_questions", 0),
        "question_types": meta.get("question_types", []),
        "language": meta.get("language", "English"),
        "result": result
    })
    history[username] = history[username][:50]  # keep last 50
    save_json(HISTORY_FILE, history)

def get_user_history(username):
    history = load_json(HISTORY_FILE, {})
    return history.get(username, [])

# ════════════════════════════════════════════════════════════
# ── PDF EXPORT ────────────────────────────────────────────
# ════════════════════════════════════════════════════════════
def generate_pdf(result, meta, show_answers):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'],
                                  fontSize=22, textColor=colors.HexColor('#667eea'),
                                  spaceAfter=6)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'],
                                fontSize=10, textColor=colors.HexColor('#888888'),
                                spaceAfter=16)
    q_style = ParagraphStyle('Question', parent=styles['Normal'],
                               fontSize=12, textColor=colors.HexColor('#a78bfa'),
                               fontName='Helvetica-Bold', spaceAfter=6, spaceBefore=12)
    a_style = ParagraphStyle('Answer', parent=styles['Normal'],
                               fontSize=11, textColor=colors.HexColor('#333333'),
                               spaceAfter=10, leftIndent=16)

    story = []

    # Header
    story.append(Paragraph("💣 QuestionBomb", title_style))
    story.append(Paragraph(
        f"Role: {meta.get('role','')}  |  Topic: {meta.get('topic','')}  |  "
        f"Difficulty: {meta.get('difficulty','')}  |  Language: {meta.get('language','English')}  |  "
        f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        sub_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#667eea')))
    story.append(Spacer(1, 12))

    if show_answers:
        blocks = result.strip().split("\n\n")
        for block in blocks:
            if block.strip():
                lines = block.strip().split("\n")
                q, a = "", ""
                for line in lines:
                    if line.startswith("Q"):
                        q = line.strip()
                    elif line.startswith("A"):
                        a = line.strip()
                if q:
                    story.append(Paragraph(q, q_style))
                if a:
                    story.append(Paragraph(a, a_style))
    else:
        lines = [l.strip() for l in result.split("\n") if l.strip()]
        for line in lines:
            story.append(Paragraph(line, q_style))
            story.append(Spacer(1, 4))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc')))
    story.append(Paragraph("Generated by QuestionBomb — Drop questions like a pro! 💥", sub_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# ════════════════════════════════════════════════════════════
# ── GENERATE QUESTIONS ────────────────────────────────────
# ════════════════════════════════════════════════════════════
LANGUAGES = {
    "English": "English",
    "Hindi (हिंदी)": "Hindi",
    "Spanish (Español)": "Spanish",
    "French (Français)": "French",
    "German (Deutsch)": "German",
    "Chinese (中文)": "Chinese (Simplified)",
    "Japanese (日本語)": "Japanese",
    "Arabic (العربية)": "Arabic",
    "Portuguese (Português)": "Portuguese",
    "Russian (Русский)": "Russian",
    "Korean (한국어)": "Korean",
    "Italian (Italiano)": "Italian",
}

def generate_questions(topic, role, num_questions, difficulty, question_type, show_answers, language="English"):
    types_str = ", ".join(question_type) if question_type else "Conceptual, Practical"
    lang = LANGUAGES.get(language, "English")

    if show_answers:
        format_instruction = f"""Format strictly like this for each question (in {lang}):
Q1. [Question here]
A1. [Detailed answer here]

Q2. [Question here]
A2. [Detailed answer here]

And so on..."""
    else:
        format_instruction = f"""Format strictly as a numbered list (in {lang}):
1. [Question]
2. [Question]
Only output questions, no answers."""

    prompt = f"""You are an expert interviewer with 10+ years of experience 
conducting interviews for {role} positions at top companies.

Generate exactly {num_questions} {difficulty}-level interview questions 
for a {role} position about: "{topic}".

Question types to include: {types_str}

IMPORTANT: Generate ALL questions and answers in {lang} language.

Rules:
- Each question must be unique and non-repetitive
- Questions should progressively increase in depth
- {format_instruction}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": f"You are an expert interviewer for {role} positions. Always respond in {lang}."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2048 if show_answers else 1024,
        temperature=0.7,
    )
    return response.choices[0].message.content


# ════════════════════════════════════════════════════════════
# ── AI FEEDBACK ON ANSWER ─────────────────────────────────
# ════════════════════════════════════════════════════════════
def get_ai_feedback(question, user_answer, role, language="English"):
    lang = LANGUAGES.get(language, "English")
    prompt = f"""You are a senior {role} interviewer evaluating a candidate's answer.

Question: {question}
Candidate's Answer: {user_answer}

Provide feedback in {lang} with:
1. Score (0-10)
2. Strengths (2-3 bullet points)
3. Areas to Improve (2-3 bullet points)
4. Ideal Answer Summary (2-3 sentences)
5. Overall Verdict: Excellent / Good / Needs Improvement / Poor

Format as:
SCORE: [X/10]
STRENGTHS:
• [point]
• [point]
IMPROVEMENTS:
• [point]
• [point]
IDEAL ANSWER: [summary]
VERDICT: [verdict]"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": f"You are an expert {role} interviewer giving constructive feedback in {lang}."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=800,
        temperature=0.5,
    )
    return response.choices[0].message.content


# ════════════════════════════════════════════════════════════
# ── MAIN APP ──────────────────────────────────────────────
# ════════════════════════════════════════════════════════════
def show_main_app():

    # ── Sidebar ───────────────────────────────────────────
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"👤 Logged in as **{st.session_state.username}**")
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

        st.markdown("---")
        st.markdown("💣 **QuestionBomb**")
        st.markdown("*Drop questions like a pro!*")
        st.header("⚙️ Configuration")

        role = st.text_input("🧑‍💼 Job Role",
                             placeholder="e.g. Software Engineer, Doctor...")
        st.caption("💡 Type any job role — works for all professions!")

        difficulty = st.select_slider("📊 Difficulty Level",
                                       options=["Easy", "Medium", "Hard", "Expert"],
                                       value="Medium")

        num_questions = st.slider("🔢 Number of Questions", 3, 15, 5)

        question_type = st.multiselect(
            "📝 Question Types",
            ["Conceptual", "Practical", "Scenario-based", "Coding", "System Design"],
            default=["Conceptual", "Practical"]
        )

        # 🌍 Multi-language Support
        st.markdown("---")
        language = st.selectbox("🌍 Language", list(LANGUAGES.keys()), index=0)
        st.caption("Questions will be generated in the selected language")

        st.markdown("---")
        show_answers = st.toggle("📝 Generate Answers Too", value=False)
        st.markdown("---")

        st.markdown("""
        <div style="display:flex; flex-direction:column; gap:8px;">
        <div style="background:#1e2130; border-radius:8px; padding:10px 15px;">
            💣 <span style="color:#a78bfa; font-weight:600">Unlimited Job Roles</span>
            <p style="color:#888; font-size:12px; margin:2px 0 0 0">Works for any profession in the world</p>
        </div>
        <div style="background:#1e2130; border-radius:8px; padding:10px 15px;">
            🌍 <span style="color:#a78bfa; font-weight:600">Multi-language</span>
            <p style="color:#888; font-size:12px; margin:2px 0 0 0">12 languages supported</p>
        </div>
        <div style="background:#1e2130; border-radius:8px; padding:10px 15px;">
            📄 <span style="color:#a78bfa; font-weight:600">PDF Export</span>
            <p style="color:#888; font-size:12px; margin:2px 0 0 0">Download as styled PDF</p>
        </div>
        <div style="background:#1e2130; border-radius:8px; padding:10px 15px;">
            🎤 <span style="color:#a78bfa; font-weight:600">Voice Interview Mode</span>
            <p style="color:#888; font-size:12px; margin:2px 0 0 0">Practice speaking your answers</p>
        </div>
        <div style="background:#1e2130; border-radius:8px; padding:10px 15px;">
            🤖 <span style="color:#a78bfa; font-weight:600">AI Feedback</span>
            <p style="color:#888; font-size:12px; margin:2px 0 0 0">Get scored on your answers</p>
        </div>
        <div style="background:#1e2130; border-radius:8px; padding:10px 15px;">
            📜 <span style="color:#a78bfa; font-weight:600">Question History</span>
            <p style="color:#888; font-size:12px; margin:2px 0 0 0">Your last 50 sessions saved</p>
        </div>
        </div>
        """, unsafe_allow_html=True)

        if role.strip():
            st.markdown("---")
            st.markdown(f"""
            <div style="background:#667eea22; border:1px solid #667eea; 
                    border-radius:8px; padding:10px; text-align:center;">
                <p style="color:#888; margin:0; font-size:12px">CURRENT ROLE</p>
                <p style="color:#a78bfa; font-weight:700; margin:0; font-size:16px">🧑‍💼 {role}</p>
            </div>
            """, unsafe_allow_html=True)

    # ── Header ─────────────────────────────────────────────
    st.markdown('<div class="header-title">💣 QuestionBomb</div>', unsafe_allow_html=True)
    st.markdown('<div class="header-sub">Drop questions like a pro — No job too big, No question too small! 💥</div>', unsafe_allow_html=True)

    if not GROQ_API_KEY:
        st.error("❌ GROQ_API_KEY not found in .env file!")
        st.stop()

    # ── TABS ───────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚀 Generate Questions",
        "🎤 Voice Interview Mode",
        "🤖 AI Feedback",
        "📜 Question History"
    ])

    # ════════════════════════════════
    # TAB 1: Generate Questions
    # ════════════════════════════════
    with tab1:
        topic = st.text_input(
            "💡 Enter Topic / Technology",
            placeholder="e.g. Python, React, Machine Learning, Patient Care..."
        )
        generate_btn = st.button("🚀 Generate Questions", key="gen_btn")

        if generate_btn:
            if not role.strip() and not topic.strip():
                st.warning("⚠️ Please enter both Job Role and Topic.")
            elif not role.strip():
                st.warning("⚠️ Please enter a Job Role in the sidebar.")
            elif not topic.strip():
                st.warning("⚠️ Please enter a Topic.")
            else:
                with st.spinner(f"⚡ Generating {num_questions} {difficulty} questions for **{role}** on **{topic}**..."):
                    try:
                        result = generate_questions(
                            topic, role, num_questions, difficulty,
                            question_type, show_answers, language
                        )
                        st.session_state.current_questions = result
                        st.session_state.current_meta = {
                            "role": role, "topic": topic, "difficulty": difficulty,
                            "num_questions": num_questions, "question_types": question_type,
                            "show_answers": show_answers, "language": language
                        }

                        # Save to history
                        save_to_history(st.session_state.username, st.session_state.current_meta, result)

                        mode = "Questions & Answers" if show_answers else "Questions"
                        lang_label = language.split("(")[0].strip()
                        st.markdown(f"### 📋 {difficulty} {mode} — {role} | {topic}")
                        st.markdown(
                            f'<span class="lang-badge">🌍 {lang_label}</span>',
                            unsafe_allow_html=True
                        )
                        st.markdown("---")

                        if show_answers:
                            blocks = result.strip().split("\n\n")
                            for block in blocks:
                                if block.strip():
                                    lines = block.strip().split("\n")
                                    question, answer = "", ""
                                    for line in lines:
                                        if line.startswith("Q"):
                                            question = line.strip()
                                        elif line.startswith("A"):
                                            answer = line.strip()
                                    if question:
                                        st.markdown(f"""
                                        <div style="background:#1e2130; border-left:4px solid #667eea;
                                                    border-radius:8px; padding:15px 20px; margin:10px 0;">
                                            <p style="color:#a78bfa; font-weight:700; margin:0 0 8px 0">{question}</p>
                                            <p style="color:#e0e0e0; margin:0">{answer}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                        else:
                            lines = [l.strip() for l in result.split("\n") if l.strip()]
                            for line in lines:
                                st.markdown(
                                    f'<div class="question-card">{line}</div>',
                                    unsafe_allow_html=True
                                )

                        st.markdown("---")

                        # ── Download buttons ─────────────────
                        col_txt, col_pdf = st.columns(2)
                        with col_txt:
                            st.download_button(
                                label="📥 Download (.txt)",
                                data=result,
                                file_name=f"{role}_{topic}_{difficulty}_{'QA' if show_answers else 'Q'}.txt",
                                mime="text/plain"
                            )
                        with col_pdf:
                            pdf_bytes = generate_pdf(
                                result, st.session_state.current_meta, show_answers
                            )
                            st.download_button(
                                label="📄 Download (.pdf)",
                                data=pdf_bytes,
                                file_name=f"{role}_{topic}_{difficulty}_{'QA' if show_answers else 'Q'}.pdf",
                                mime="application/pdf"
                            )

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

        # Show PDF download for previous results too
        elif st.session_state.current_questions and st.session_state.current_meta:
            st.info("💡 Previous questions still available. Generate new ones or switch to another tab.")

    # ════════════════════════════════
    # TAB 2: Voice Interview Mode
    # ════════════════════════════════
    with tab2:
        st.markdown("### 🎤 Voice Interview Mode")

        if not st.session_state.current_questions:
            st.warning("⚠️ Please generate questions first in the '🚀 Generate Questions' tab.")
        else:
            meta = st.session_state.current_meta
            result = st.session_state.current_questions

            st.markdown(f"**Session:** {meta.get('role','')} — {meta.get('topic','')} ({meta.get('difficulty','')})")

            # Extract questions only
            raw_lines = [l.strip() for l in result.split("\n") if l.strip()]
            questions = []
            for line in raw_lines:
                if line.startswith("Q") or (len(line) > 0 and line[0].isdigit() and "." in line[:3]):
                    if not line.startswith("A"):
                        questions.append(line)
            if not questions:
                questions = raw_lines

            selected_q = st.selectbox("📋 Select a Question to Practice", questions)

            # language → BCP-47 map for TTS
            lang_to_bcp47 = {
                "English": "en-US",
                "Hindi (हिंदी)": "hi-IN",
                "Spanish (Español)": "es-ES",
                "French (Français)": "fr-FR",
                "German (Deutsch)": "de-DE",
                "Chinese (中文)": "zh-CN",
                "Japanese (日本語)": "ja-JP",
                "Arabic (العربية)": "ar-SA",
                "Portuguese (Português)": "pt-PT",
                "Russian (Русский)": "ru-RU",
                "Korean (한국어)": "ko-KR",
                "Italian (Italiano)": "it-IT",
            }
            tts_lang = lang_to_bcp47.get(meta.get("language", "English"), "en-US")
            stt_lang = tts_lang  # same language for mic input

            # Escape quotes for JS safety
            safe_q = selected_q.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")

            st.components.v1.html(f"""
<!DOCTYPE html>
<html>
<head>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Inter', sans-serif;
    background: transparent;
    color: #e0e0e0;
    padding: 12px;
  }}
  .card {{
    background: #1e2130;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 14px;
  }}
  .section-title {{
    color: #a78bfa;
    font-weight: 700;
    font-size: 14px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .question-box {{
    background: #0d1117;
    border-left: 4px solid #a78bfa;
    border-radius: 8px;
    padding: 14px 16px;
    color: #e0e0e0;
    font-size: 15px;
    line-height: 1.6;
    margin-bottom: 12px;
  }}
  .btn {{
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }}
  .btn:hover {{ opacity: 0.85; }}
  .btn-speak {{
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
  }}
  .btn-stop-speak {{
    background: #4b5563;
    color: white;
    display: none;
  }}
  .btn-record {{
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: white;
  }}
  .btn-stop-rec {{
    background: #ef4444;
    color: white;
    display: none;
  }}
  .btn-copy {{
    background: #2d3150;
    color: #a78bfa;
    font-size: 12px;
    padding: 7px 14px;
  }}
  .btn-clear {{
    background: #374151;
    color: #9ca3af;
    font-size: 12px;
    padding: 7px 14px;
  }}
  .btn-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 10px;
  }}
  .status-bar {{
    font-size: 12px;
    padding: 6px 10px;
    border-radius: 6px;
    margin-bottom: 10px;
    background: #0d1117;
    color: #9ca3af;
    min-height: 30px;
  }}
  .status-bar.recording {{
    color: #f87171;
    background: #1f1010;
    border: 1px solid #7f1d1d;
  }}
  .status-bar.speaking {{
    color: #60a5fa;
    background: #0f172a;
    border: 1px solid #1e3a5f;
  }}
  .status-bar.ok {{
    color: #4ade80;
    background: #0f1f0f;
    border: 1px solid #14532d;
  }}
  #transcript {{
    background: #0d1117;
    border-radius: 8px;
    padding: 12px;
    min-height: 80px;
    color: #e0e0e0;
    font-size: 14px;
    line-height: 1.6;
    white-space: pre-wrap;
    border: 1px solid #2d3150;
  }}
  .interim {{ color: #6b7280; font-style: italic; }}
  .speed-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
    font-size: 13px;
    color: #9ca3af;
  }}
  input[type=range] {{ accent-color: #667eea; width: 120px; }}
</style>
</head>
<body>

<!-- QUESTION + TTS -->
<div class="card">
  <div class="section-title">❓ Question (read aloud by AI)</div>
  <div class="question-box" id="qbox">{selected_q}</div>

  <div class="speed-row">
    🐢 Speed:
    <input type="range" id="speedSlider" min="0.6" max="1.4" step="0.1" value="0.9"
           oninput="document.getElementById('speedVal').innerText = this.value + 'x'">
    <span id="speedVal">0.9x</span>
    &nbsp;&nbsp;
    🔊 Voice:
    <select id="voiceSelect" style="background:#1e2130; color:#e0e0e0; border:1px solid #2d3150;
            border-radius:6px; padding:3px 8px; font-size:12px;">
      <option value="">Default</option>
    </select>
  </div>

  <div class="btn-row">
    <button class="btn btn-speak" id="speakBtn" onclick="speakQuestion()">🔊 Speak Question</button>
    <button class="btn btn-stop-speak" id="stopSpeakBtn" onclick="stopSpeaking()">⏹️ Stop Speaking</button>
  </div>
  <div class="status-bar" id="ttsStatus">Press "Speak Question" to hear it read aloud.</div>
</div>

<!-- MIC / ANSWER -->
<div class="card">
  <div class="section-title">🎤 Your Answer (speak or type)</div>
  <div class="btn-row">
    <button class="btn btn-record" id="recBtn" onclick="startRecording()">🎙️ Start Recording</button>
    <button class="btn btn-stop-rec" id="stopRecBtn" onclick="stopRecording()">⏹️ Stop Recording</button>
  </div>
  <div class="status-bar" id="recStatus">Press "Start Recording" and speak your answer.</div>
  <div id="transcript">Your transcribed answer will appear here...</div>
  <br>
  <div class="btn-row">
    <button class="btn btn-copy" onclick="copyAnswer()">📋 Copy Answer</button>
    <button class="btn btn-clear" onclick="clearAnswer()">🗑️ Clear</button>
  </div>
</div>

<script>
const TTS_LANG = "{tts_lang}";
const STT_LANG = "{stt_lang}";
let synth = window.speechSynthesis;
let utterance = null;
let voices = [];
let recognition = null;
let finalTranscript = "";
let isSpeaking = false;
let isRecording = false;

// ── Load voices ──────────────────────────────
function loadVoices() {{
  voices = synth.getVoices().filter(v => v.lang.startsWith(TTS_LANG.split('-')[0]));
  const sel = document.getElementById('voiceSelect');
  sel.innerHTML = '<option value="">Default</option>';
  voices.forEach((v, i) => {{
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = v.name + (v.localService ? ' (local)' : ' (online)');
    sel.appendChild(opt);
  }});
}}
loadVoices();
if (speechSynthesis.onvoiceschanged !== undefined) {{
  speechSynthesis.onvoiceschanged = loadVoices;
}}

// ── TTS ──────────────────────────────────────
function speakQuestion() {{
  if (isSpeaking) {{ synth.cancel(); }}
  const text = document.getElementById('qbox').innerText;
  utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = TTS_LANG;
  utterance.rate = parseFloat(document.getElementById('speedSlider').value);

  const voiceIdx = document.getElementById('voiceSelect').value;
  if (voiceIdx !== "" && voices[voiceIdx]) {{
    utterance.voice = voices[voiceIdx];
  }}

  utterance.onstart = () => {{
    isSpeaking = true;
    setTTSStatus("🔵 Speaking question...", "speaking");
    document.getElementById('speakBtn').style.display = 'none';
    document.getElementById('stopSpeakBtn').style.display = 'inline-flex';
  }};
  utterance.onend = () => {{
    isSpeaking = false;
    setTTSStatus("✅ Done! Now record your answer below.", "ok");
    document.getElementById('speakBtn').style.display = 'inline-flex';
    document.getElementById('stopSpeakBtn').style.display = 'none';
  }};
  utterance.onerror = (e) => {{
    isSpeaking = false;
    setTTSStatus("❌ TTS error: " + e.error, "");
    document.getElementById('speakBtn').style.display = 'inline-flex';
    document.getElementById('stopSpeakBtn').style.display = 'none';
  }};
  synth.speak(utterance);
}}

function stopSpeaking() {{
  synth.cancel();
  isSpeaking = false;
  setTTSStatus("⏹️ Stopped.", "");
  document.getElementById('speakBtn').style.display = 'inline-flex';
  document.getElementById('stopSpeakBtn').style.display = 'none';
}}

function setTTSStatus(msg, cls) {{
  const el = document.getElementById('ttsStatus');
  el.innerText = msg;
  el.className = 'status-bar ' + cls;
}}

// ── STT ──────────────────────────────────────
function startRecording() {{
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {{
    setRecStatus("❌ Speech Recognition not supported. Use Google Chrome!", "");
    return;
  }}
  // stop TTS first so mic doesn't pick it up
  synth.cancel();

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SR();
  recognition.lang = STT_LANG;
  recognition.continuous = true;
  recognition.interimResults = true;

  recognition.onstart = () => {{
    isRecording = true;
    setRecStatus("🔴 Recording... speak your answer now!", "recording");
    document.getElementById('recBtn').style.display = 'none';
    document.getElementById('stopRecBtn').style.display = 'inline-flex';
  }};

  recognition.onresult = (event) => {{
    let interim = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {{
      if (event.results[i].isFinal) {{
        finalTranscript += event.results[i][0].transcript + ' ';
      }} else {{
        interim += event.results[i][0].transcript;
      }}
    }}
    document.getElementById('transcript').innerHTML =
      finalTranscript +
      (interim ? '<span class="interim">' + interim + '</span>' : '');
  }};

  recognition.onerror = (e) => {{
    setRecStatus("❌ Error: " + e.error + ". Try again.", "");
    resetRecButtons();
  }};

  recognition.onend = () => {{
    isRecording = false;
    if (finalTranscript.trim()) {{
      setRecStatus("✅ Recording complete! Copy your answer above.", "ok");
    }} else {{
      setRecStatus("⏹️ Stopped. No speech detected.", "");
    }}
    resetRecButtons();
  }};

  recognition.start();
}}

function stopRecording() {{
  if (recognition) recognition.stop();
}}

function resetRecButtons() {{
  document.getElementById('recBtn').style.display = 'inline-flex';
  document.getElementById('stopRecBtn').style.display = 'none';
}}

function setRecStatus(msg, cls) {{
  const el = document.getElementById('recStatus');
  el.innerText = msg;
  el.className = 'status-bar ' + cls;
}}

function copyAnswer() {{
  const text = finalTranscript || document.getElementById('transcript').innerText;
  navigator.clipboard.writeText(text).then(() => {{
    setRecStatus("📋 Copied to clipboard! Paste in the AI Feedback tab.", "ok");
  }}).catch(() => {{
    setRecStatus("⚠️ Copy failed — please select text manually.", "");
  }});
}}

function clearAnswer() {{
  finalTranscript = "";
  document.getElementById('transcript').innerHTML = "Your transcribed answer will appear here...";
  setRecStatus("🗑️ Cleared. Ready to record again.", "");
}}
</script>
</body>
</html>
""", height=620)

            st.markdown("---")
            st.info("💡 **How to use:** Click **Speak Question** → listen → click **Start Recording** → speak your answer → **Stop Recording** → **Copy Answer** → paste it in the **🤖 AI Feedback** tab.")

            voice_answer = st.text_area(
                "✏️ Or manually type / paste your answer here:",
                height=140,
                placeholder="Paste your copied transcript or type your answer...",
                key="voice_input_area"
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Answer for Feedback", key="save_voice"):
                    if voice_answer.strip():
                        st.session_state.voice_answer = voice_answer
                        st.session_state.voice_question = selected_q
                        st.success("✅ Saved! Switch to '🤖 AI Feedback' tab.")
                    else:
                        st.warning("Please paste or type your answer first.")
            with col2:
                if st.button("🔄 Clear", key="clear_voice"):
                    st.session_state.voice_answer = ""
                    st.rerun()

    # ════════════════════════════════
    # TAB 3: AI Feedback
    # ════════════════════════════════
    with tab3:
        st.markdown("### 🤖 AI Feedback on Your Answer")

        if not st.session_state.current_questions:
            st.warning("⚠️ Please generate questions first in the '🚀 Generate Questions' tab.")
        else:
            meta = st.session_state.current_meta

            # Pre-fill if coming from voice mode
            prefill_q = getattr(st.session_state, 'voice_question', '')
            prefill_a = st.session_state.voice_answer or ""

            st.markdown("#### 📝 Enter Question & Your Answer")
            eval_question = st.text_area("Question:", value=prefill_q, height=80,
                                          placeholder="Paste or type the interview question...")
            eval_answer = st.text_area("Your Answer:", value=prefill_a, height=150,
                                        placeholder="Type or paste your answer for AI evaluation...")

            col1, col2 = st.columns([1, 2])
            with col1:
                feedback_lang = st.selectbox("Feedback Language", list(LANGUAGES.keys()),
                                              index=list(LANGUAGES.keys()).index(meta.get("language", "English")))

            if st.button("🤖 Get AI Feedback", key="feedback_btn"):
                if not eval_question.strip() or not eval_answer.strip():
                    st.warning("⚠️ Please enter both question and your answer.")
                else:
                    with st.spinner("🤖 Evaluating your answer..."):
                        try:
                            feedback = get_ai_feedback(
                                eval_question, eval_answer,
                                meta.get("role", "Professional"), feedback_lang
                            )

                            st.markdown("---")
                            st.markdown("### 📊 Feedback Report")

                            # Parse score
                            score_line = [l for l in feedback.split("\n") if l.startswith("SCORE:")]
                            verdict_line = [l for l in feedback.split("\n") if l.startswith("VERDICT:")]

                            score_text = score_line[0].replace("SCORE:", "").strip() if score_line else "N/A"
                            verdict_text = verdict_line[0].replace("VERDICT:", "").strip() if verdict_line else "N/A"

                            verdict_colors = {
                                "Excellent": "#4ade80", "Good": "#60a5fa",
                                "Needs Improvement": "#fbbf24", "Poor": "#f87171"
                            }
                            v_color = verdict_colors.get(verdict_text, "#888")

                            col_score, col_verdict = st.columns(2)
                            with col_score:
                                st.markdown(f"""
                                <div style="background:#1e2130; border-radius:10px; padding:16px; text-align:center;">
                                    <p style="color:#888; margin:0; font-size:12px">SCORE</p>
                                    <p style="color:#a78bfa; font-size:2.5rem; font-weight:900; margin:0">{score_text}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            with col_verdict:
                                st.markdown(f"""
                                <div style="background:#1e2130; border-radius:10px; padding:16px; text-align:center;">
                                    <p style="color:#888; margin:0; font-size:12px">VERDICT</p>
                                    <p style="color:{v_color}; font-size:1.5rem; font-weight:900; margin:0">{verdict_text}</p>
                                </div>
                                """, unsafe_allow_html=True)

                            st.markdown("---")
                            st.markdown(f"""
                            <div class="feedback-card">
                                <pre style="white-space: pre-wrap; font-family: Inter, sans-serif;
                                            color: #d1fae5; font-size: 14px; margin: 0;">{feedback}</pre>
                            </div>
                            """, unsafe_allow_html=True)

                            # Download feedback
                            st.download_button(
                                "📥 Download Feedback (.txt)",
                                data=f"Question:\n{eval_question}\n\nYour Answer:\n{eval_answer}\n\nFeedback:\n{feedback}",
                                file_name=f"feedback_{meta.get('role','')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                                mime="text/plain"
                            )

                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

    # ════════════════════════════════
    # TAB 4: Question History
    # ════════════════════════════════
    with tab4:
        st.markdown("### 📜 Your Question History")
        history = get_user_history(st.session_state.username)

        if not history:
            st.info("📭 No history yet. Generate some questions to see them here!")
        else:
            st.markdown(f"**{len(history)} session(s) saved** (showing last 50)")

            col_search, col_filter = st.columns([2, 1])
            with col_search:
                search_term = st.text_input("🔍 Search history", placeholder="Search by role, topic...")
            with col_filter:
                diff_filter = st.selectbox("Filter by difficulty",
                                            ["All", "Easy", "Medium", "Hard", "Expert"])

            filtered = [h for h in history if
                       (not search_term or
                        search_term.lower() in h.get("role","").lower() or
                        search_term.lower() in h.get("topic","").lower()) and
                       (diff_filter == "All" or h.get("difficulty","") == diff_filter)]

            if not filtered:
                st.info("No results match your filter.")
            else:
                for i, session in enumerate(filtered):
                    lang_label = session.get("language", "English").split("(")[0].strip()
                    expander_label = (
                        f"🕐 {session['timestamp']} | "
                        f"🧑‍💼 {session['role']} | "
                        f"💡 {session['topic']} | "
                        f"📊 {session['difficulty']} | "
                        f"🌍 {lang_label}"
                    )
                    with st.expander(expander_label):
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.markdown(f"**Role:** {session['role']}")
                            st.markdown(f"**Topic:** {session['topic']}")
                        with col_b:
                            st.markdown(f"**Difficulty:** {session['difficulty']}")
                            st.markdown(f"**Questions:** {session['num_questions']}")
                        with col_c:
                            st.markdown(f"**Language:** {lang_label}")
                            st.markdown(f"**Types:** {', '.join(session.get('question_types', []))}")

                        st.markdown("---")
                        if st.button(f"📂 Load this session", key=f"load_{i}"):
                            st.session_state.current_questions = session["result"]
                            st.session_state.current_meta = session
                            st.success("✅ Session loaded! Switch to the Generate tab to view/download.")

                        result_lines = [l for l in session["result"].split("\n") if l.strip()]
                        for line in result_lines[:5]:
                            st.markdown(f'<div class="question-card" style="padding:8px 14px; font-size:13px">{line}</div>',
                                       unsafe_allow_html=True)
                        if len(result_lines) > 5:
                            st.caption(f"...and {len(result_lines)-5} more lines. Load session to see all.")

                        # Download from history
                        col_d1, col_d2 = st.columns(2)
                        with col_d1:
                            st.download_button(
                                "📥 .txt",
                                data=session["result"],
                                file_name=f"{session['role']}_{session['topic']}_{session['difficulty']}.txt",
                                mime="text/plain",
                                key=f"dl_txt_{i}"
                            )
                        with col_d2:
                            pdf_b = generate_pdf(session["result"], session,
                                                  session.get("show_answers", False))
                            st.download_button(
                                "📄 .pdf",
                                data=pdf_b,
                                file_name=f"{session['role']}_{session['topic']}_{session['difficulty']}.pdf",
                                mime="application/pdf",
                                key=f"dl_pdf_{i}"
                            )

# ════════════════════════════════════════════════════════════
# ── ENTRY POINT ───────────────────────────────────────────
# ════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    show_auth()
else:
    show_main_app()