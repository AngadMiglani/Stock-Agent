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


def analyse_stock(stock_info: dict, notes: str = "", recent_news=None) -> dict:
    """
    Uses Gemini to analyse a stock given some basic info and optional notes.
    Returns a dict with a single key "raw_analysis" (a string).
    """
    if recent_news is None:
        recent_news = []

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
        "recent_news": recent_news
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


def analyse_portfolio_risk(stock_info: dict, notes: str = "", recent_news=None) -> dict:
    """
    Returns {"risk_summary": "...", "risk_flag": "LOW|MEDIUM|HIGH"} using Gemini.
    """
    if recent_news is None:
        recent_news = []

    system_instruction = (
        "You are a risk analyst for a concentrated public equities portfolio. "
        "Given limited structured market info, news info and the manager's notes, produce: "
        "(1) a short risk summary, and (2) a single risk flag: LOW, MEDIUM, or HIGH. "
        "Focus on downside risks, governance/management concerns, leverage/fragility, "
        "and valuation overstretch if it is obvious from the limited data. "
        "If evidence is insufficient, say so and keep the flag conservative (usually MEDIUM)."
    )

    user_payload = {"stock_info": stock_info, "notes": notes, "recent_news": recent_news}

    prompt = (
        system_instruction
        + "\n\nData:\n"
        + str(user_payload)
        + "\n\nReturn in exactly this format:\n"
        + "RISK_FLAG: <LOW|MEDIUM|HIGH>\n"
        + "SUMMARY: <2-5 sentences>\n"
    )

    response = model.generate_content(prompt)
    text = (response.text or "").strip()

    # simple parse
    risk_flag = "MEDIUM"
    summary = text

    for line in text.splitlines():
        if line.strip().upper().startswith("RISK_FLAG:"):
            risk_flag = line.split(":", 1)[1].strip().upper() or "MEDIUM"
        if line.strip().upper().startswith("SUMMARY:"):
            summary = line.split(":", 1)[1].strip() or text

    # clamp
    if risk_flag not in {"LOW", "MEDIUM", "HIGH"}:
        risk_flag = "MEDIUM"

    return {"risk_summary": summary, "risk_flag": risk_flag}

