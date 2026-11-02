"""
AI service layer for the resume builder.

Wraps calls to the Groq API for three jobs:
1. Rewriting a user's plain-language job description into strong resume bullet points
2. Generating a professional summary
3. Generating a tailored cover letter from resume data + a pasted job description
"""

import os
import json
from openai import OpenAI

# Initialize the OpenAI client pointing to the GROQ endpoint
client = OpenAI(
    api_key=os.environ.get("XAI_API_KEY"),  # Reads your exported variable
    base_url="https://api.groq.com/openai/v1",  # <-- CHANGED to Groq's base URL
)

# Use a flagship Groq model
MODEL = "openai/gpt-oss-120b"# to a valid Groq model


# ---------------------------------------------------------------------------
# Bullet point rewriting
# ---------------------------------------------------------------------------

BULLET_SYSTEM_PROMPT = """You are an expert resume writer specializing in the Kenyan and East African \
job market (corporate, NGO, and gig-economy roles). You turn a candidate's plain description of their \
work into sharp, achievement-oriented resume bullet points.

Rules:
- Output 3-5 bullet points, one per line, no numbering or bullet characters.
- Start each line with a strong action verb (Led, Built, Reduced, Managed, Increased, Delivered, etc.).
- Quantify impact wherever the input gives you any basis to (numbers, percentages, team size, time saved). 
Never invent numbers that aren't implied by the input — if there's no basis, keep it qualitative.
- Keep each bullet to one line, ATS-friendly (no special characters, no emojis).
- If a target job title or job description is provided, lightly emphasize the skills and language that \
match it, without fabricating experience the candidate didn't describe.
- Return ONLY the bullet lines, nothing else — no preamble, no markdown formatting."""


def rewrite_bullet_points(job_title: str, company: str, raw_description: str,
                          target_job_title: str = "", target_job_description: str = "") -> list[str]:
    context = f"Role: {job_title} at {company}\n\nWhat the candidate wrote:\n{raw_description}"
    if target_job_title or target_job_description:
        context += f"\n\nTailor toward this target role: {target_job_title}\n{target_job_description[:1500]}"

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=400,
        messages=[
            {"role": "system", "content": BULLET_SYSTEM_PROMPT},
            {"role": "user", "content": context}
        ],
    )

    text = response.choices[0].message.content.strip()
    return [line.strip("-• ").strip() for line in text.splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Professional summary
# ---------------------------------------------------------------------------

SUMMARY_SYSTEM_PROMPT = """You write 2-3 sentence professional summaries for resumes, targeted at the \
Kenyan job market. Confident but not exaggerated. No buzzword soup ("synergy", "dynamic self-starter"). \
Ground it in the candidate's actual experience and, if given, the target role. Return ONLY the summary \
text, no preamble."""


def generate_professional_summary(full_name: str, work_experiences: list[dict],
                                  target_job_title: str = "", target_job_description: str = "") -> str:
    exp_text = "\n".join(
        f"- {exp['job_title']} at {exp['company']}: {exp['raw_description']}"
        for exp in work_experiences
    )
    context = f"Candidate: {full_name}\n\nExperience:\n{exp_text}"
    if target_job_title:
        context += f"\n\nTarget role: {target_job_title}\n{target_job_description[:1000]}"

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=200,
        messages=[
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": context}
        ],
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Cover letter generation
# ---------------------------------------------------------------------------

COVER_LETTER_SYSTEM_PROMPT = """You write tailored, one-page cover letters for job applications in Kenya \
and East Africa. Structure: greeting, opening hook tied to the specific role, 2 short body paragraphs \
connecting the candidate's real experience to the job requirements, closing with a call to action, sign-off.

Rules:
- Use only the experience provided — never invent employers, titles, or achievements.
- Match the requested tone (formal / friendly / confident).
- Keep it under 350 words.
- Return ONLY the letter text, no subject line, no markdown."""


def generate_cover_letter(full_name: str, work_experiences: list[dict], job_title: str,
                           company_name: str, job_description: str, tone: str = "formal") -> str:
    exp_text = "\n".join(
        f"- {exp['job_title']} at {exp['company']}: {exp['raw_description']}"
        for exp in work_experiences
    )
    context = (
        f"Candidate: {full_name}\n\n"
        f"Experience:\n{exp_text}\n\n"
        f"Applying for: {job_title} at {company_name}\n"
        f"Job description:\n{job_description[:2000]}\n\n"
        f"Tone: {tone}"
    )

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=600,
        messages=[
            {"role": "system", "content": COVER_LETTER_SYSTEM_PROMPT},
            {"role": "user", "content": context}
        ],
    )
    return response.choices[0].message.content.strip()