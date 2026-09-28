import streamlit as st
from pypdf import PdfReader
from docx import Document
from google import genai
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)
from io import BytesIO
import re


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="🤖",
    layout="wide"
)


# =========================================================
# UI STYLE
# =========================================================

st.markdown("""
<style>

.stApp {
    background-color: #eef2f7 !important;
}

[data-testid="stAppViewContainer"] {
    background-color: #eef2f7 !important;
}

[data-testid="stHeader"] {
    background-color: #eef2f7 !important;
}

h1, h2, h3 {
    color: #172033 !important;
}

p, label {
    color: #374151 !important;
}

.main-title {
    text-align: center;
    font-size: 42px;
    font-weight: 800;
    color: #172033 !important;
    margin-top: 10px;
}

.subtitle {
    text-align: center;
    font-size: 18px;
    color: #667085 !important;
    margin-bottom: 30px;
}

.section-title {
    font-size: 25px;
    font-weight: 700;
    color: #172033 !important;
    margin-top: 28px;
    margin-bottom: 12px;
}

.card {
    background-color: #ffffff !important;
    border: 1px solid #d9dee8;
    border-radius: 16px;
    padding: 22px;
    text-align: center;
    margin-bottom: 20px;
    box-shadow: 0px 4px 14px rgba(20, 30, 50, 0.08);
}

.card-title {
    color: #667085 !important;
    font-size: 14px;
    font-weight: 700;
}

.card-value {
    color: #2563eb !important;
    font-size: 34px;
    font-weight: 800;
}

textarea {
    background-color: white !important;
    color: #172033 !important;
}

input {
    background-color: white !important;
    color: #172033 !important;
}

.stButton > button {
    background-color: #2563eb !important;
    color: white !important;
    border: none !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
}

.stDownloadButton > button {
    background-color: #16a34a !important;
    color: white !important;
    border: none !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# GEMINI
# =========================================================

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🤖 AI Resume Analyzer</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Analyze your resume, check ATS compatibility, '
    'and compare it with a job description.'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# UPLOAD
# =========================================================

st.markdown(
    '<div class="section-title">📤 Upload Resume</div>',
    unsafe_allow_html=True
)

resume = st.file_uploader(
    "Upload your Resume",
    type=["pdf", "docx"]
)


# =========================================================
# JOB DESCRIPTION
# =========================================================

st.markdown(
    '<div class="section-title">💼 Job Description</div>',
    unsafe_allow_html=True
)

job_description = st.text_area(
    "Paste the job description below",
    height=200,
    placeholder="Paste the complete job description here..."
)


# =========================================================
# PDF REPORT FUNCTION
# =========================================================

def create_pdf_report(
    resume_name,
    ats_score,
    final_match,
    found_skills,
    found_sections,
    missing_skills,
    suggestions,
    matching_skills,
    missing_job_skills,
    matching_keywords,
    missing_keywords
):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#172033"),
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#667085"),
        spaceAfter=20
    )

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=15,
        textColor=colors.HexColor("#172033"),
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#374151")
    )

    score_style = ParagraphStyle(
        "Score",
        parent=styles["Heading1"],
        fontSize=25,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#2563eb")
    )

    story = []

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "🤖 AI Resume Analyzer",
            title_style
        )
    )

    story.append(
        Paragraph(
            "Professional Resume Analysis Report",
            subtitle_style
        )
    )

    story.append(
        Paragraph(
            f"<b>Resume:</b> {resume_name}",
            body_style
        )
    )

    story.append(Spacer(1, 15))

    # -----------------------------------------------------
    # SCORE TABLE
    # -----------------------------------------------------

    job_score = (
        f"{final_match}%"
        if final_match is not None
        else "N/A"
    )

    score_data = [
        [
            Paragraph("<b>ATS SCORE</b>", body_style),
            Paragraph("<b>JOB MATCH</b>", body_style)
        ],
        [
            Paragraph(
                f"<font size='22' color='#2563eb'><b>{ats_score}/100</b></font>",
                body_style
            ),
            Paragraph(
                f"<font size='22' color='#2563eb'><b>{job_score}</b></font>",
                body_style
            )
        ]
    ]

    score_table = Table(
        score_data,
        colWidths=[230, 230]
    )

    score_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#d9dee8")),
            ("INNERGRID", (0, 0), (-1, -1), 1, colors.HexColor("#d9dee8")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12)
        ])
    )

    story.append(score_table)

    # -----------------------------------------------------
    # HELPER
    # -----------------------------------------------------

    def add_section(title, items):

        story.append(
            Paragraph(
                title,
                heading_style
            )
        )

        if not items:

            story.append(
                Paragraph(
                    "None",
                    body_style
                )
            )

            return

        if isinstance(items, list):

            text = ", ".join(
                str(item)
                for item in items
            )

        else:

            text = str(items)

        story.append(
            Paragraph(
                text,
                body_style
            )
        )

    # -----------------------------------------------------
    # SKILLS
    # -----------------------------------------------------

    add_section(
        "🛠️ Skills Detected",
        found_skills
    )

    # -----------------------------------------------------
    # SECTIONS
    # -----------------------------------------------------

    add_section(
        "📋 Resume Sections",
        found_sections
    )

    # -----------------------------------------------------
    # MISSING GENERAL SKILLS
    # -----------------------------------------------------

    add_section(
        "⚠️ General Missing Skills",
        missing_skills[:10]
    )

    # -----------------------------------------------------
    # SUGGESTIONS
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "💡 Resume Suggestions",
            heading_style
        )
    )

    for suggestion in suggestions:

        story.append(
            Paragraph(
                "• " + suggestion,
                body_style
            )
        )

    # -----------------------------------------------------
    # JOB MATCH
    # -----------------------------------------------------

    if final_match is not None:

        story.append(
            Paragraph(
                "🎯 Job Description Match",
                heading_style
            )
        )

        story.append(
            Paragraph(
                f"<b>Job Match Score:</b> {final_match}%",
                body_style
            )
        )

        add_section(
            "✅ Matching Skills",
            matching_skills
        )

        add_section(
            "⚠️ Skills Missing From Resume",
            missing_job_skills
        )

        add_section(
            "🔑 Matching Keywords",
            matching_keywords[:25]
        )

        add_section(
            "🚨 Important Missing Keywords",
            missing_keywords[:25]
        )

        story.append(
            Paragraph(
                "📌 Job Match Summary",
                heading_style
            )
        )

        if final_match >= 75:

            summary = (
                "Strong match for this job description."
            )

        elif final_match >= 50:

            summary = (
                "Moderate match. Some relevant "
                "skills and keywords could be improved."
            )

        else:

            summary = (
                "Low match. Consider adding relevant "
                "skills, keywords, projects, or experience "
                "that you genuinely have."
            )

        story.append(
            Paragraph(
                summary,
                body_style
            )
        )

    # -----------------------------------------------------
    # FOOTER
    # -----------------------------------------------------

    story.append(Spacer(1, 25))

    story.append(
        Paragraph(
            "Generated by AI Resume Analyzer",
            subtitle_style
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer


# =========================================================
# PROCESS RESUME
# =========================================================

if resume:

    st.success("✅ Resume uploaded successfully!")

    text = ""

    # -----------------------------------------------------
    # PDF
    # -----------------------------------------------------

    if resume.name.lower().endswith(".pdf"):

        reader = PdfReader(resume)

        for page in reader.pages:

            text += page.extract_text() or ""

    # -----------------------------------------------------
    # DOCX
    # -----------------------------------------------------

    elif resume.name.lower().endswith(".docx"):

        document = Document(resume)

        for paragraph in document.paragraphs:

            text += paragraph.text + "\n"

    resume_lower = text.lower()

    # =====================================================
    # SKILLS
    # =====================================================

    skills = [

        "Python",
        "Java",
        "C++",
        "SQL",
        "Excel",
        "Machine Learning",
        "Artificial Intelligence",
        "Deep Learning",
        "Data Science",
        "Power BI",
        "Tableau",
        "Pandas",
        "NumPy",
        "Git",
        "GitHub",
        "HTML",
        "CSS",
        "JavaScript",
        "Data Analysis",
        "Data Visualization",
        "MySQL",
        "MongoDB",
        "TensorFlow",
        "Keras",
        "Scikit-learn"

    ]

    found_skills = []

    for skill in skills:

        if skill.lower() in resume_lower:

            found_skills.append(skill)

    # =====================================================
    # SECTIONS
    # =====================================================

    sections = {

        "Education": [
            "education",
            "academic"
        ],

        "Experience": [
            "experience",
            "work experience",
            "internship"
        ],

        "Skills": [
            "skills",
            "technical skills"
        ],

        "Projects": [
            "projects",
            "project"
        ],

        "Certifications": [
            "certification",
            "certifications"
        ],

        "Contact": [
            "email",
            "phone",
            "linkedin",
            "github"
        ]

    }

    found_sections = []

    for section, keywords in sections.items():

        if any(
            keyword in resume_lower
            for keyword in keywords
        ):

            found_sections.append(section)

    # =====================================================
    # ATS SCORE
    # =====================================================

    section_score = (
        len(found_sections) * 8
    )

    skill_score = min(
        len(found_skills) * 2,
        20
    )

    ats_score = min(
        100,
        40 + section_score + skill_score
    )

    # =====================================================
    # GENERAL MISSING SKILLS
    # =====================================================

    missing_skills = [

        skill
        for skill in skills
        if skill not in found_skills

    ]

    # =====================================================
    # SUGGESTIONS
    # =====================================================

    suggestions = []

    if len(found_skills) < 5:

        suggestions.append(
            "Add more relevant technical skills."
        )

    if "GitHub" not in found_skills:

        suggestions.append(
            "Add your GitHub profile or relevant projects."
        )

    if "Python" not in found_skills:

        suggestions.append(
            "Add Python if it is relevant to your skills."
        )

    if "Machine Learning" not in found_skills:

        suggestions.append(
            "Consider adding relevant Machine Learning projects."
        )

    if "Projects" not in found_sections:

        suggestions.append(
            "Add a Projects section to highlight practical work."
        )

    if "Certifications" not in found_sections:

        suggestions.append(
            "Add a Certifications section if you have relevant certificates."
        )

    if not suggestions:

        suggestions.append(
            "Your resume contains several relevant skills and sections."
        )

    # =====================================================
    # JOB MATCH
    # =====================================================

    final_match = None

    matching_skills = []
    missing_job_skills = []
    matching_keywords = []
    missing_keywords = []

    if job_description.strip():

        job_lower = job_description.lower()

        # -------------------------------------------------
        # JOB SKILLS
        # -------------------------------------------------

        job_skills = []

        for skill in skills:

            if skill.lower() in job_lower:

                job_skills.append(skill)

        for skill in job_skills:

            if skill.lower() in resume_lower:

                matching_skills.append(skill)

            else:

                missing_job_skills.append(skill)

        # -------------------------------------------------
        # IMPORTANT PHRASES
        # -------------------------------------------------

        important_phrases = [

            "data analysis",
            "data visualization",
            "machine learning",
            "artificial intelligence",
            "deep learning",
            "power bi",
            "data science",
            "problem solving",
            "problem-solving",
            "data driven",
            "data-driven",
            "data processing",
            "data cleaning",
            "dashboard",
            "dashboards",
            "reporting",
            "communication",
            "teamwork"

        ]

        matching_phrases = []
        missing_phrases = []

        for phrase in important_phrases:

            if phrase in job_lower:

                if phrase in resume_lower:

                    matching_phrases.append(phrase)

                else:

                    missing_phrases.append(phrase)

        # -------------------------------------------------
        # WORD MATCHING
        # -------------------------------------------------

        stop_words = {

            "the", "and", "for", "with",
            "that", "this", "are", "you",
            "your", "our", "from", "have",
            "will", "can", "who", "job",
            "work", "role", "team",
            "looking", "candidate", "candidates",
            "should", "using", "their",
            "they", "about", "which",
            "been", "being", "also",
            "good", "join", "members",
            "motivated", "required",
            "responsibilities", "skills",
            "experience", "ability",
            "strong", "excellent",
            "including", "we", "us",
            "into", "through", "within",
            "from", "this", "that",
            "with", "your", "our"

        }

        job_words = set(
            re.findall(
                r"\b[a-zA-Z][a-zA-Z+#.-]{3,}\b",
                job_lower
            )
        )

        resume_words = set(
            re.findall(
                r"\b[a-zA-Z][a-zA-Z+#.-]{3,}\b",
                resume_lower
            )
        )

        useful_job_words = (
            job_words - stop_words
        )

        matching_word_set = (
            useful_job_words & resume_words
        )

        missing_word_set = (
            useful_job_words - resume_words
        )

        matching_keywords = (
            matching_phrases
            + sorted(
                matching_word_set
            )
        )

        missing_keywords = (
            missing_phrases
            + sorted(
                missing_word_set
            )
        )

        # -------------------------------------------------
        # SCORE
        # -------------------------------------------------

        if job_skills:

            skill_score_match = (
                len(matching_skills)
                / len(job_skills)
            ) * 100

        else:

            skill_score_match = 0

        total_keywords = (
            len(
                useful_job_words
            )
            + len(
                matching_phrases
            )
            + len(
                missing_phrases
            )
        )

        matched_keywords = (
            len(matching_word_set)
            + len(matching_phrases)
        )

        if total_keywords:

            keyword_score = (
                matched_keywords
                / total_keywords
            ) * 100

        else:

            keyword_score = 0

        final_match = round(
            min(
                100,
                skill_score_match * 0.65
                + keyword_score * 0.35
            ),
            1
        )

    # =====================================================
    # DASHBOARD
    # =====================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">
                    📊 ATS SCORE
                </div>
                <div class="card-value">
                    {ats_score}/100
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        score_display = (
            f"{final_match}%"
            if final_match is not None
            else "—"
        )

        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">
                    🎯 JOB MATCH
                </div>
                <div class="card-value">
                    {score_display}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:

        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">
                    🛠️ SKILLS FOUND
                </div>
                <div class="card-value">
                    {len(found_skills)}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # =====================================================
    # ATS
    # =====================================================

    st.markdown(
        '<div class="section-title">📊 ATS Resume Score</div>',
        unsafe_allow_html=True
    )

    st.progress(
        ats_score / 100
    )

    if ats_score >= 80:

        st.success(
            "🌟 Your resume has a strong ATS structure."
        )

    elif ats_score >= 60:

        st.warning(
            "👍 Your resume has a moderate ATS structure."
        )

    else:

        st.error(
            "⚠️ Your resume could be improved for ATS compatibility."
        )

    # =====================================================
    # SKILLS
    # =====================================================

    st.markdown(
        '<div class="section-title">🛠️ Skills Detected</div>',
        unsafe_allow_html=True
    )

    st.write(
        ", ".join(found_skills)
        if found_skills
        else "No skills detected."
    )

    # =====================================================
    # SECTIONS
    # =====================================================

    st.markdown(
        '<div class="section-title">📋 Resume Sections</div>',
        unsafe_allow_html=True
    )

    st.write(
        " • ".join(found_sections)
        if found_sections
        else "No major sections detected."
    )

    # =====================================================
    # MISSING SKILLS
    # =====================================================

    st.markdown(
        '<div class="section-title">⚠️ General Missing Skills</div>',
        unsafe_allow_html=True
    )

    st.write(
        ", ".join(
            missing_skills[:10]
        )
        if missing_skills
        else "No major skills missing."
    )

    # =====================================================
    # SUGGESTIONS
    # =====================================================

    st.markdown(
        '<div class="section-title">💡 Resume Suggestions</div>',
        unsafe_allow_html=True
    )

    for suggestion in suggestions:

        st.write(
            "• " + suggestion
        )

    # =====================================================
    # JOB MATCHER
    # =====================================================

    st.markdown(
        '<div class="section-title">🎯 Job Description Matcher</div>',
        unsafe_allow_html=True
    )

    if final_match is not None:

        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">
                    🎯 JOB MATCH SCORE
                </div>
                <div class="card-value">
                    {final_match}%
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.progress(
            final_match / 100
        )

        st.markdown(
            "### ✅ Matching Skills"
        )

        st.write(
            ", ".join(matching_skills)
            if matching_skills
            else "None"
        )

        st.markdown(
            "### ⚠️ Skills Missing From Resume"
        )

        st.write(
            ", ".join(missing_job_skills)
            if missing_job_skills
            else "None"
        )

        st.markdown(
            "### 🔑 Matching Keywords"
        )

        st.write(
            ", ".join(
                matching_keywords[:25]
            )
            if matching_keywords
            else "None"
        )

        st.markdown(
            "### 🚨 Important Missing Keywords"
        )

        st.write(
            ", ".join(
                missing_keywords[:25]
            )
            if missing_keywords
            else "None"
        )

        st.markdown(
            "### 📌 Job Match Summary"
        )

        if final_match >= 75:

            st.success(
                "🌟 Strong match for this job description."
            )

        elif final_match >= 50:

            st.warning(
                "👍 Moderate match. Some relevant skills and keywords could be improved."
            )

        else:

            st.error(
                "⚠️ Low match. Consider adding relevant skills, keywords, projects, or experience that you genuinely have."
            )

    else:

        st.info(
            "Paste a job description above to compare it with your resume."
        )

    # =====================================================
    # PDF DOWNLOAD
    # =====================================================

    st.markdown(
        '<div class="section-title">📥 Download Professional Report</div>',
        unsafe_allow_html=True
    )

    pdf_file = create_pdf_report(
        resume_name=resume.name,
        ats_score=ats_score,
        final_match=final_match,
        found_skills=found_skills,
        found_sections=found_sections,
        missing_skills=missing_skills,
        suggestions=suggestions,
        matching_skills=matching_skills,
        missing_job_skills=missing_job_skills,
        matching_keywords=matching_keywords,
        missing_keywords=missing_keywords
    )

    st.download_button(
        label="📥 Download Professional PDF Report",
        data=pdf_file,
        file_name="AI_Resume_Analysis_Report.pdf",
        mime="application/pdf"
    )

    # =====================================================
    # AI ANALYSIS
    # =====================================================

    st.markdown(
        '<div class="section-title">🤖 AI Resume Analysis</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "✨ Analyze Resume with AI"
    ):

        with st.spinner(
            "Analyzing your resume..."
        ):

            prompt = f"""
You are an AI resume reviewer.

Analyze the following resume and provide:

1. Overall Resume Summary
2. Key Strengths
3. Weaknesses or Areas to Improve
4. Important Missing Keywords
5. Suitable Entry-Level Job Roles
6. Specific Resume Improvement Suggestions
7. A better professional resume summary

Keep the feedback practical, clear, and suitable
for a college student or entry-level candidate.

Do not invent experience, skills, education,
certifications, or achievements that are not present
in the resume.

Resume:

{text}
"""

            try:

                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt
                )

                st.success(
                    "✅ AI analysis completed!"
                )

                st.write(
                    response.text
                )

            except Exception as e:

                error = str(e)

                if (
                    "503" in error
                    or "UNAVAILABLE" in error
                ):

                    st.warning(
                        "⚠️ Gemini is temporarily unavailable."
                    )

                    st.info(
                        "Using the built-in Resume Analyzer instead."
                    )

                    st.markdown(
                        "### 📋 Resume Analysis"
                    )

                    st.write(
                        "✅ Your resume contains a good amount of information."
                    )

                    st.markdown(
                        "### 💪 Strengths"
                    )

                    if found_skills:

                        st.write(
                            "• Technical skills found: "
                            + ", ".join(found_skills)
                        )

                    if found_sections:

                        st.write(
                            "• Resume sections detected: "
                            + ", ".join(found_sections)
                        )

                    st.markdown(
                        "### ⚠️ Areas to Improve"
                    )

                    for suggestion in suggestions:

                        st.write(
                            "• " + suggestion
                        )

                    st.markdown(
                        "### 🎯 Suggested Entry-Level Roles"
                    )

                    st.write(
                        "• Data Analyst Intern"
                    )

                    st.write(
                        "• Software Developer Intern"
                    )

                    if (
                        "Machine Learning" in found_skills
                        or
                        "Artificial Intelligence" in found_skills
                    ):

                        st.write(
                            "• AI/ML Intern"
                        )

                    st.markdown(
                        "### 💡 Overall Recommendation"
                    )

                    st.write(
                        "Improve the resume by adding measurable "
                        "project achievements, relevant keywords, "
                        "and practical experience."
                    )

                elif "429" in error:

                    st.warning(
                        "⚠️ Gemini API limit reached."
                    )

                    st.info(
                        "Please try again later."
                    )

                else:

                    st.error(
                        "Unable to connect to Gemini."
                    )

                    st.write(error)