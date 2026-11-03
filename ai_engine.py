
import streamlit as st
from groq import Groq

MODEL_NAME = "qwen/qwen3.8-27b"


def generate_ai_response(prompt: str) -> str:
    """Generate an AI response using Groq's hosted API."""

    api_key = st.secrets.get("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing. Add it to Streamlit Secrets."
        )

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are SkillLens AI, a professional resume analysis "
                    "assistant. Provide accurate, practical career guidance. "
                    "Never invent a candidate's skills, qualifications, "
                    "achievements, or work experience."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
        max_tokens=3000,
    )

    return response.choices[0].message.content or ""
