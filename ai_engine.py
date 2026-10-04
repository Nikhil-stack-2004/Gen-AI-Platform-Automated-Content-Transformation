import os
from dotenv import load_dotenv
from google import genai

# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY not found. "
        "Please check your .env file."
    )

print("Gemini API key loaded: True")


# =========================================================
# GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# CONTENT TRANSFORMATION
# =========================================================

def transform_content(
    content,
    transformation="Summarize",
    tone="Professional",
    language="English"
):

    system_prompt = f"""
You are a professional Generative AI content transformation
assistant.

Your task is to transform the user's content.

Transformation:
{transformation}

Tone:
{tone}

Language:
{language}

Rules:
1. Preserve the original meaning.
2. Produce clear and high-quality content.
3. Follow the requested transformation.
4. Follow the requested tone.
5. Write in the requested language.
6. Do not explain the process.
7. Return only the transformed content.
"""

    user_prompt = f"""
{system_prompt}

CONTENT TO TRANSFORM:

{content}
"""

    try:

        # =================================================
        # GEMINI INTERACTIONS API
        # =================================================

        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input=user_prompt
        )

        # =================================================
        # GET GENERATED TEXT
        # =================================================

        if interaction.output_text:

            return interaction.output_text.strip()

        return "Gemini returned an empty response."

    except Exception as e:

        print("=" * 60)
        print("Gemini API Error:")
        print(type(e).__name__)
        print(str(e))
        print("=" * 60)

        return (
            "Unable to generate AI content. "
            "Please check the Gemini API configuration."
        )