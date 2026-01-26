from datetime import date
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import subprocess

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

usage_tracker = {}
FREE_LIMIT = 3


class DecisionInput(BaseModel):
    decision: str


@app.post("/simulate")
def simulate(data: DecisionInput, request: Request):

    user_ip = request.client.host
    today = str(date.today())
    key = f"{user_ip}_{today}"

    if key not in usage_tracker:
        usage_tracker[key] = 0

    if usage_tracker[key] >= FREE_LIMIT:
        return {
            "limit_reached": True,
            "message": "Free limit reached. Upgrade to continue."
        }

    usage_tracker[key] += 1

    prompt = prompt = f"""
You are a Decision Intelligence System.

Your job:
Help the user decide clearly, not write essays.

STRICT RULES:
- Simple, clear English
- Short sentences
- No long paragraphs
- No philosophy
- No disclaimers
- No repetition
- Max 120 words TOTAL

OUTPUT FORMAT (follow exactly):

Decision Summary:
<What is the decision in 1 line>

Score:
<0–10>/10

Key Positives:
- <clear benefit 1>
- <clear benefit 2>

Key Risks:
- <clear risk 1>
- <clear risk 2>

Reality Check:
<1 honest line in plain language>

Final Signal:
<PROCEED / PROCEED WITH CAUTION / AVOID>

Decision:
{data.decision}
"""

    result = subprocess.run(
        ["ollama", "run", "mistral"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode != 0:
        return {"error": result.stderr}

    return {
        "analysis": result.stdout.strip(),
        "remaining": FREE_LIMIT - usage_tracker[key]
    }
