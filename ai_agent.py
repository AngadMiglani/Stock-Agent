import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"  # free / fast model, good for this use-case

if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in .env")

# Configure the Gemini client
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(MODEL_NAME)


def analyse_stock(stock_info: dict, notes: str = "") -> dict:
    """
    Uses Gemini to analyse a stock given some basic info and optional notes.
    Returns a dict with a single key "raw_analysis" (a string).
    """

    system_instruction = (
        "You are an equity analyst helping a fund manager monitor public stocks. "
        "You are given basic price/valuation information and some notes from the manager. "
        "Your job is to briefly explain how the stock seems to be doing recently, "
        "and mention any obvious governance or valuation concerns. "
        "If information is limited or noisy, say so explicitly and be conservative."
    )

    user_payload = {
        "stock_info": stock_info,
        "notes": notes,
    }

    # For now we just send a simple text prompt combining system + user.
    prompt = (
        system_instruction
        + "\n\nHere is the data you have:\n"
        + str(user_payload)
        + "\n\nWrite a short analysis (3–6 sentences)."
    )

    response = model.generate_content(prompt)

    # Gemini SDK puts the text in response.text
    analysis_text = (response.text or "").strip()

    return {"raw_analysis": analysis_text}
