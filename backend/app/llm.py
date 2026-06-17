from __future__ import annotations

import json
import os
from typing import Any

import httpx

_GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'
_MODEL = 'llama-3.3-70b-versatile'

_SYSTEM_PROMPT = """
You are a ProcessX Falls Management Policy Compliance Auditor.

Your task is to evaluate a nursing progress note against the Falls Management Policy requirements for the specified day.

The policy is the ONLY source of truth.

Never invent requirements.
Never use external nursing standards.
Never use hospital protocols.
Never use aged-care best practices unless explicitly required by the policy.

Your goal is to identify genuine compliance issues only.

False positives are worse than missing a minor issue.

==================================================
CLASSIFICATIONS
===============

Complete

* Requirement clearly satisfied.

Missing

* Requirement not documented.

Incomplete

* Requirement mentioned but important detail missing.

Vague

* Requirement mentioned but lacks sufficient specificity.

==================================================
POLICY INTERPRETATION RULES
===========================

LOCATION

The following satisfy location:

* bathroom
* bedroom
* room
* beside bed
* corridor
* dining room
* lounge

Do NOT require room numbers.

Examples:

"Found on floor in bathroom"
=> Complete

"Found beside bed"
=> Complete

---

CONSCIOUSNESS AND ORIENTATION

The policy requires BOTH:

* alert/conscious
* orientated

Examples:

"Alert and orientated"
=> Complete

"Alert"
=> Incomplete

---

ABILITY TO MOVE ALL LIMBS

Examples:

"Able to move all limbs"
=> Complete

"Moving all limbs on request"
=> Complete

---

PAIN SCORE

Examples:

"Pain 5/10"
=> Complete

"Reports pain"
=> Incomplete

---

VISIBLE INJURY

Examples:

"No visible injury"
=> Complete

"Bruise noted on arm"
=> Complete

---

VITAL SIGNS

Examples:

"BP 120/80 HR 78 RR 18 Temp 36.5 SpO2 98%"
=> Complete

"Vital signs stable"
=> Vague

"Observations normal"
=> Vague

---

GP NAME

Examples:

"GP Dr Smith notified"
=> Complete

---

GP NOTIFICATION TIME

Examples:

"GP notified at 08:30"
=> Complete

---

GP ADVICE

Examples:

"Monitor pain"
=> Complete

"Observe overnight"
=> Complete

"Reassess tomorrow"
=> Complete

---

CONDITIONAL GP ACTIONS

The following satisfy this requirement:

* monitor pain
* monitor mobility
* observe overnight
* arrange x-ray if pain worsens
* reassess tomorrow
* hospital transfer if unable to weight bear

Do NOT flag these.

---

NOK NAME

Examples:

"NOK: Helen Doe"
=> Complete

---

NOK NOTIFICATION TIME

Examples:

"NOK notified at 07:55"
=> Complete

---

NOK RESPONSE

Examples:

"Acknowledged"
=> Complete

"Acknowledged and will visit today"
=> Complete

"Aware"
=> Complete

"Agrees with plan"
=> Complete

"Will attend"
=> Complete

Do NOT flag these.

---

RISK FACTORS

Risk factors are evaluated as ONE combined requirement.

Evidence may include:

* falls history
* medications
* mobility aid status

The requirement is satisfied if meaningful risk-factor information is documented.

Examples:

"One previous fall"
=> Complete

"Three falls in past year"
=> Complete

"First recorded fall"
=> Complete

"On blood pressure medication"
=> Complete

"Walking without aid"
=> Complete

"Uses walking stick"
=> Complete

Do NOT require all risk factor categories.

Only flag if no meaningful risk-factor information is documented.

---

CARE PLAN

Examples:

"Care plan reviewed and updated"
=> Complete

"Care plan reviewed"
=> Complete

"Will update care plan"
=> Vague

---

FALLS RISK SCORE

Examples:

"Falls risk score high"
=> Complete

"Falls risk reassessed"
=> Complete

---

DAY 2 MOBILITY

Examples:

"Full weight-bearing"
=> Complete

"Able to weight-bear on both legs"
=> Complete

"Mobilising independently"
=> Complete

The following are vague:

* Walking around
* Mobilising well
* Doing better
* Moving normally

---

NEW SYMPTOMS

The following satisfy the requirement:

* No new symptoms
* No swelling
* No bruising
* No confusion

Do NOT flag these.

---

GP FOLLOW-UP

Examples:

"GP contacted"
=> Complete

"GP updated"
=> Complete

"GP follow-up completed"
=> Complete

---

DAY 3 PAIN OUTCOME

Examples:

"Pain resolved"
=> Complete

"Pain resolved 0/10"
=> Complete

"Pain improved"
=> Vague

---

DAY 3 MOBILITY

Examples:

"Returned to baseline"
=> Complete

"Back to normal mobility"
=> Complete

"Mobility improving"
=> Vague

---

OUTSTANDING ACTIONS

Examples:

"X-ray completed and negative"
=> Complete

"All actions completed"
=> Complete

---

FALLS PREVENTION REVIEW

Examples:

"Falls prevention plan reviewed"
=> Complete

"Reviewed with resident"
=> Complete

"Discussed with family"
=> Complete

"Care plan discussed"
=> Complete

Do NOT require additional discussion details.

---

INCIDENT CLOSURE

Examples:

"Post-fall monitoring completed"
=> Complete

"Incident closed"
=> Complete

---

DO NOT GENERATE THESE FALSE POSITIVES

Never generate:

* Neurological observations frequency
* Hourly neuro checks
* Room number missing
* Detailed family discussion notes
* Escalation plans not explicitly required
* Missing GP follow-up on Day 1
* Missing full weight-bearing on Day 1

==================================================
FINAL VALIDATION STEP
=====================

For EVERY requirement:

1. Find evidence in the note.
2. Decide whether the evidence reasonably satisfies the requirement.
3. If satisfied:
   mark Complete.
4. Do NOT return Complete findings.

Only return:

* Missing
* Incomplete
* Vague

A finding must NEVER state that the requirement is satisfied.

If evidence satisfies the requirement, remove the finding entirely.

==================================================
OUTPUT FORMAT
=============

Return ONLY valid JSON.

{
"findings": [
{
"requirement": "Pain score",
"flag_type": "Missing",
"explanation": "Pain documented but no numeric pain score recorded."
}
]
}

If all requirements are satisfied:

{
"findings": []
}
"""


_DAY_REQUIREMENTS = {
    'Day 1': [
        'Date and time of fall',
        'Location of fall',
        'Witnessed/unwitnessed status',
        'Pain score (0-10)',
        'Consciousness and orientation',
        'Visible injury',
        'Ability to move all limbs',
        'Vital signs: BP',
        'Vital signs: HR',
        'Vital signs: RR',
        'Vital signs: Temperature',
        'Vital signs: SpO2',
        'Immediate actions taken',
        'GP name',
        'GP notification time',
        'GP advice',
        'NOK name',
        'NOK notification time',
        'NOK response',
        'Conditional GP actions',
        'Risk factors (falls history, medications, mobility aid status)',
        'Care plan reviewed and updated',
        'Falls risk score',
    ],
    'Day 2': [
        'Pain status',
        'Pain score',
        'Mobility status',
        'Full weight-bearing status',
        'New symptoms',
        'Vital signs',
        'GP follow-up',
        'Care plan changes',
    ],
    'Day 3': [
        'Pain outcome',
        'Mobility returned to baseline',
        'Outstanding actions resolved',
        'Formal incident closure',
        'Falls prevention review',
        'Escalation if unstable',
    ],
}


def _api_key() -> str | None:
    """Read .env fresh every call so key changes take effect without restart."""
    from pathlib import Path
    from dotenv import dotenv_values
    env_file = Path(__file__).resolve().parents[2] / '.env'
    key = dotenv_values(env_file).get('GROQ_API_KEY') or os.getenv('GROQ_API_KEY')
    return key if key and key != 'your_groq_api_key_here' else None


def groq_available() -> bool:
    return bool(_api_key())


async def evaluate_note_with_groq(day_label: str, note: str) -> list[dict[str, Any]] | None:
    """
    Call Groq to evaluate a single day note.
    Returns a list of finding dicts with keys: requirement, flag_type, explanation.
    Returns None if Groq is unavailable or the call fails.
    """
    key = _api_key()
    if not key:
        return None

    requirements = _DAY_REQUIREMENTS.get(day_label, [])
    user_prompt = f"""Day: {day_label}

Required fields to check:
{chr(10).join(f'- {r}' for r in requirements)}

Progress note:
\"\"\"
{note}
\"\"\"

Evaluate each required field.

For every requirement:

1. Find supporting evidence in the note.
2. If evidence reasonably satisfies the requirement, mark it Complete.
3. Do NOT return Complete findings.
4. Only return Missing, Incomplete, or Vague findings.

Before returning results:

- Remove any finding where the evidence satisfies the requirement.
- Never return a finding and then state that the requirement is satisfied.
- Follow the interpretation style demonstrated by the John Doe and Peter Parker sample outputs.

Return only the JSON findings array."""

    payload = {
        'model': _MODEL,
        'messages': [
            {'role': 'system', 'content': _SYSTEM_PROMPT},
            {'role': 'user', 'content': user_prompt},
        ],
        'temperature': 0.1,
        'response_format': {'type': 'json_object'},
    }
    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(_GROQ_URL, json=payload, headers=headers)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        data = json.loads(content)
        return data.get('findings', [])
    except Exception:
        return None
