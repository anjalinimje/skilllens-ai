import ollama

MODEL_NAME = "qwen3:latest"


def generate_ai_response(prompt: str) -> str:
    """
    Generate a response using the locally running Ollama model.
    """

    response = ollama.chat(
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
    )

    return response["message"]["content"]