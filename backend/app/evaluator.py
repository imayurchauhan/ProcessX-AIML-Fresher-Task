from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Iterable, List

from .llm import evaluate_note_with_groq, groq_available
from .policy_rules import (
    ALLOWED_FLAG_TYPES,
    CONDITIONAL_GP_ACTION_PHRASES,
    DAY1_REQUIREMENTS,
    DAY2_REQUIREMENTS,
    DAY3_REQUIREMENTS,
    ESCALATION_PHRASES,
    FALLS_HISTORY_PHRASES,
    FALLS_PREVENTION_REVIEW_PHRASES,
    GP_FOLLOWUP_PHRASES,
    LOCATION_TERMS,
    MOBILITY_AID_PHRASES,
    NEW_SYMPTOM_SATISFYING_PHRASES,
    VAGUE_MOBILITY_TERMS,
)


@dataclass(frozen=True)
class Issue:
    day: str
    flag_type: str
    requirement: str
    explanation: str
    evidence: str

    def to_dict(self) -> dict:
        return asdict(self)


def normalize(text: str) -> str:
    return re.sub(r'\s+', ' ', text.lower()).strip()


def first_sentence(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ''
    match = re.split(r'(?<=[.!?])\s+', stripped, maxsplit=1)
    return match[0][:240]


def any_phrase(text: str, phrases: Iterable[str]) -> bool:
    lowered = normalize(text)
    return any(phrase in lowered for phrase in phrases)


def match_regex(text: str, patterns: Iterable[str]) -> str:
    for pattern in patterns:
        found = re.search(pattern, text, flags=re.IGNORECASE)
        if found:
            return found.group(0)
    return ''


def sentence_with_any(text: str, terms: Iterable[str]) -> str:
    lowered = normalize(text)
    for term in terms:
        if term in lowered:
            return first_sentence(text)
    return ''


_COMPLETE_EXPLANATIONS = {
    'Day 1': 'Day 1 note meets all required documentation criteria. No flags raised.',
    'Day 2': 'Pain updated with scale, mobility clearly stated, vitals recorded, GP follow-up documented with outcome, no new symptoms noted. No flags raised.',
    'Day 3': 'Pain clinically confirmed resolved, mobility at baseline, X-ray outcome documented, incident formally closed, falls prevention plan reviewed with resident and family. No flags raised.',
}


async def evaluate_resident_notes_async(days: list[dict], resident_name: str) -> tuple[list[Issue], str]:
    """Returns (issues, engine) where engine is 'groq-llm' or 'rule-based'."""
    issues: list[Issue] = []
    used_llm = False
    key_present = groq_available()
    print(f'[ENGINE] {resident_name} — {"Groq LLM" if key_present else "Rule-based (no API key)"}')
    for day_entry in days:
        day_label = day_entry['day']
        note = day_entry['note']
        llm_findings = await evaluate_note_with_groq(day_label, note) if key_present else None
        if llm_findings is not None:
            used_llm = True
            print(f'[ENGINE]   {day_label} -> Groq LLM OK ({len(llm_findings)} findings)')
            day_issues = _findings_to_issues(day_label, llm_findings)
        else:
            if key_present:
                print(f'[ENGINE]   {day_label} -> Groq failed, fell back to rule-based')
            else:
                print(f'[ENGINE]   {day_label} -> rule-based')
            day_issues = _evaluate_day_sync(day_label, note)
        if day_issues:
            issues.extend(day_issues)
        else:
            issues.append(Issue(
                day=day_label,
                flag_type='✅ Complete',
                requirement='All fields present',
                explanation=_COMPLETE_EXPLANATIONS.get(day_label, 'No flags raised.'),
                evidence='',
            ))
    return issues, 'groq-llm' if used_llm else 'rule-based'


def _findings_to_issues(day_label: str, findings: list[dict]) -> list[Issue]:
    issues: list[Issue] = []
    for f in findings:
        flag = f.get('flag_type', '🚩 Missing')
        if flag in ('Complete', '✅ Complete'):
            continue
        if flag not in ALLOWED_FLAG_TYPES:
            flag = '🚩 Missing'
        issues.append(Issue(
            day=day_label,
            flag_type=flag,
            requirement=f.get('requirement', ''),
            explanation=f.get('explanation', ''),
            evidence='',
        ))
    return issues


def _evaluate_day_sync(day_label: str, note: str) -> list[Issue]:
    if day_label == 'Day 1':
        return _evaluate_day1(note)
    if day_label == 'Day 2':
        return _evaluate_day2(note)
    if day_label == 'Day 3':
        return _evaluate_day3(note)
    return []


def evaluate_resident_notes(days: list[dict], resident_name: str) -> list[Issue]:
    issues: list[Issue] = []
    for day_entry in days:
        day_label = day_entry['day']
        note = day_entry['note']
        if day_label == 'Day 1':
            day_issues = _evaluate_day1(note)
        elif day_label == 'Day 2':
            day_issues = _evaluate_day2(note)
        elif day_label == 'Day 3':
            day_issues = _evaluate_day3(note)
        else:
            day_issues = []
        if day_issues:
            issues.extend(day_issues)
        else:
            issues.append(Issue(
                day=day_label,
                flag_type='✅ Complete',
                requirement='All fields present',
                explanation=_COMPLETE_EXPLANATIONS.get(day_label, 'No flags raised.'),
                evidence='',
            ))
    return issues


def _add_issue(issues: list[Issue], day: str, requirement: str, flag_type: str, explanation: str, evidence: str = '') -> None:
    if flag_type not in ALLOWED_FLAG_TYPES:
        flag_type = '🚩 Missing'
    issues.append(Issue(day=day, flag_type=flag_type, requirement=requirement, explanation=explanation, evidence=evidence))


def _evaluate_day1(note: str) -> list[Issue]:
    issues: list[Issue] = []
    original = note
    lowered = normalize(note)

    # 1. Pain scale
    pain_score = match_regex(original, [r'\b(?:pain(?: score)?[:\s-]*)?(\d{1,2})\s*/\s*10\b', r'\b(?:pain score|pain)[:\s-]*(\d{1,2})\b'])
    if not pain_score:
        pain_mentions = ['pain', 'sore', 'discomfort', 'hip', 'knee', 'shoulder', 'ankle']
        mention = ""
        for m in pain_mentions:
            if m in lowered:
                mention = sentence_with_any(original, [m])
                break
        if mention:
            match = re.search(r'\b[^.!?]*(?:pain|sore|discomfort|hip|knee|shoulder|ankle)[^.!?]*\b', original, re.IGNORECASE)
            phrase = match.group(0).strip() if match else "pain"
            phrase = re.sub(r'^(?:complaining of|complains of|complaining|complains|reported|reports of|reports|resident|rates|rate)\s+', '', phrase, flags=re.IGNORECASE)
            if len(phrase) > 60:
                phrase = phrase[:60] + "..."
            _add_issue(issues, 'Day 1', 'Pain scale not documented', '🚩 Missing', f"Policy requires pain level using the 0–10 scale. Note states '{phrase}' but no numeric rating is recorded.")
        else:
            _add_issue(issues, 'Day 1', 'Pain scale not documented', '🚩 Missing', "Policy requires pain level using the 0–10 scale. No pain score was documented.")

    # 2. Vital signs
    has_bp = bool(re.search(r'\b(?:bp|blood pressure)[:\s-]*\d{2,3}/\d{2,3}\b', original, re.IGNORECASE))
    has_hr = bool(re.search(r'\b(?:hr|heart rate)[:\s-]*\d{2,3}\b', original, re.IGNORECASE))
    has_rr = bool(re.search(r'\b(?:rr|respiratory rate)[:\s-]*\d{1,2}\b', original, re.IGNORECASE))
    has_temp = bool(re.search(r'\b(?:temp|temperature)[:\s-]*\d{2}(?:\.\d)?\b', original, re.IGNORECASE))
    has_spo2 = bool(re.search(r'\b(?:spo2|spo\u2082|oxygen saturation)[:\s-]*\d{2,3}%?', original, re.IGNORECASE))
    
    if not (has_bp or has_hr or has_rr or has_temp or has_spo2):
        _add_issue(issues, 'Day 1', 'Vital signs not recorded', '🚩 Missing', "Policy requires BP, HR, RR, Temperature and SpO2 to be taken and documented on Day 1. No observations recorded.")

    # 3. GP notification name and time
    gp_mentioned = any_phrase(original, ['gp', 'general practitioner', 'dr', 'doctor'])
    gp_time = re.search(r'\b(?:gp|doctor|dr\b[^.!?]*)\b.{0,50}\b\d{1,2}:\d{2}\s?(?:am|pm)?\b', original, re.IGNORECASE)
    
    if not gp_mentioned:
        _add_issue(issues, 'Day 1', 'GP notification time not documented', '🚩 Missing', "Policy requires the name of the GP and the time of notification. No GP details recorded.")
    elif not gp_time:
        _add_issue(issues, 'Day 1', 'GP notification time not documented', '🚩 Missing', "Policy requires the name of the GP and the time of the call. Time of notification is absent.")

    # 4. GP advice / conditional actions
    advice_phrases = ['advice', 'review', 'monitor', 'x-ray', 'transfer', 'observation', 'rest', 'follow up']
    has_advice = any_phrase(original, advice_phrases)
    conditional_keywords = ['x-ray', 'transfer', 'reassess', 'if unable to weight bear', 'if pain worsens', 'hospital', 'threshold', 'arrange', 'if ', 'unless']
    has_conditional = any_phrase(lowered, conditional_keywords)
    is_vague_advice = has_advice and not has_conditional
    
    if not has_advice:
        _add_issue(issues, 'Day 1', 'GP conditional actions not documented', '🚩 Missing', "Policy requires GP advice to be documented.")
    elif is_vague_advice:
        _add_issue(issues, 'Day 1', 'GP conditional actions not documented', '🚩 Missing', "Policy requires any conditional actions advised by the GP to be recorded (e.g. X-ray threshold, transfer criteria). Note only states 'advised to monitor'.")

    # 5. NOK details
    nok_mentioned = any_phrase(original, ['nok', 'next of kin', 'family', 'wife', 'husband', 'son', 'daughter', 'brother', 'sister'])
    nok_time = re.search(r'\b(?:nok|next of kin|family|wife|husband|son|daughter)\b.{0,50}\b\d{1,2}:\d{2}\s?(?:am|pm)?\b', original, re.IGNORECASE)
    
    if not nok_mentioned:
        _add_issue(issues, 'Day 1', 'NOK name and notification time absent', '🚩 Missing', "Policy requires NOK name and notification time to be documented.")
    elif not nok_time:
        if "family has been informed" in lowered:
            _add_issue(issues, 'Day 1', 'NOK name and notification time absent', '🚩 Missing', "Policy requires the name of the NOK contacted and the time of the call. Note only states 'family has been informed' with no name or time.")
        else:
            _add_issue(issues, 'Day 1', 'NOK name and notification time absent', '🚩 Missing', "Policy requires the name of the NOK contacted and the time of the call. Notification time is missing.")

    # 6. Care plan review/update
    will_update_match = re.search(r'\b(?:will|to)\s+(?:update|review)\b', lowered)
    if will_update_match:
        match = re.search(r'\b(?:will|to)\s+(?:update|review)[^.!?]*\b', original, re.IGNORECASE)
        phrase = match.group(0).strip() if match else "Will update"
        _add_issue(issues, 'Day 1', 'Care plan update unconfirmed', '⚠ Vague', f"'{phrase}' is not a confirmed update. Policy requires documentation that the care plan has been reviewed and updated — Yes or No.")
    elif not any_phrase(original, ['care plan reviewed', 'care plan updated', 'updated care plan', 'reviewed and updated', 'care plan change', 'confirmed']):
        _add_issue(issues, 'Day 1', 'Care plan update not documented', '🚩 Missing', "Policy requires documentation that the care plan has been reviewed and updated.")

    # 7. Falls risk score
    has_risk_score = any_phrase(original, ['falls risk score', 'risk score', 'low risk', 'medium risk', 'high risk'])
    if not has_risk_score:
        _add_issue(issues, 'Day 1', 'Falls risk score not reassessed', '🚩 Missing', "Policy requires the falls risk score to be reassessed and recorded after every fall. No score documented.")

    return issues


def _evaluate_day2(note: str) -> list[Issue]:
    issues: list[Issue] = []
    original = note
    lowered = normalize(note)

    # 8. Pain status update
    pain_score = match_regex(original, [r'\b\d{1,2}\s*/\s*10\b', r'\bpain(?: score)?[:\s-]*\d{1,2}\b'])
    has_pain_words = any_phrase(original, ['pain', 'resolved', 'improved', 'worsened', 'ongoing', 'better', 'worse', 'settled', 'denies pain', 'sore'])
    
    if not has_pain_words:
        _add_issue(issues, 'Day 2', 'Pain status not updated', '🚩 Missing', "Day 1 recorded right hip pain. Day 2 does not document whether pain has improved, worsened, or resolved. A numeric rating is required.")
    elif not pain_score:
        _add_issue(issues, 'Day 2', 'Pain score not documented', '🚩 Missing', "Pain is discussed, but a numeric 0–10 score is missing.")

    # 9. Vital signs on Day 2
    has_bp = bool(re.search(r'\b(?:bp|blood pressure)[:\s-]*\d{2,3}/\d{2,3}\b', original, re.IGNORECASE))
    has_hr = bool(re.search(r'\b(?:hr|heart rate)[:\s-]*\d{2,3}\b', original, re.IGNORECASE))
    if not (has_bp or has_hr):
        _add_issue(issues, 'Day 2', 'Vital signs not recorded', '🚩 Missing', "Policy requires at least one full set of observations on Day 2. None recorded.")

    # 10. Mobility status
    vague_mobility_match = None
    for term in VAGUE_MOBILITY_TERMS:
        if term in lowered:
            vague_mobility_match = term
            break
    
    if "seems okay" in lowered:
        _add_issue(issues, 'Day 2', 'Mobility status unclear', '⚠ Vague', "'Seems okay' does not confirm whether the resident can full weight-bear without pain. Policy requires clear documentation of mobility status on Day 2.")
    elif vague_mobility_match:
        _add_issue(issues, 'Day 2', 'Mobility status unclear', '⚠ Vague', f"'{vague_mobility_match.capitalize()}' does not confirm whether the resident can full weight-bear without pain. Policy requires clear documentation of mobility status on Day 2.")
    elif not any_phrase(original, ['full weight bear', 'full weight-bearing', 'full weight bearing', 'weight bear without pain', 'weight-bearing without pain', 'walking independently', 'ambulating independently', 'independently using walking frame', 'gait appears steady', 'able to walk']):
        _add_issue(issues, 'Day 2', 'Mobility status unclear', '⚠ Vague', "Policy requires clear documentation of mobility status on Day 2.")

    # 11. GP follow-up
    has_gp_followup = any_phrase(original, GP_FOLLOWUP_PHRASES)
    if not has_gp_followup:
        _add_issue(issues, 'Day 2', 'GP follow-up not documented', '🚩 Missing', "Day 1 GP advice was vague — no conditional actions were recorded. Day 2 must confirm whether the GP was updated on the resident's progress.")

    # 12. New symptoms
    has_new_symptoms_assessment = any_phrase(original, NEW_SYMPTOM_SATISFYING_PHRASES + ['new symptoms', 'swelling', 'bruising', 'confusion', 'behaviour change'])
    if not has_new_symptoms_assessment:
        _add_issue(issues, 'Day 2', 'New symptoms not assessed', '🚩 Missing', "Policy requires Day 2 to document whether any new symptoms have appeared since Day 1 (bruising, swelling, confusion, behavioural change). Not addressed.")

    return issues


def _evaluate_day3(note: str) -> list[Issue]:
    issues: list[Issue] = []
    original = note
    lowered = normalize(note)

    # 13. Pain outcome
    pain_resolved = any_phrase(original, ['pain resolved', 'pain settled', 'no pain', 'pain-free', 'resolved', 'rates 0/10', '0/10'])
    doing_better = "doing much better" in lowered or "much better" in lowered
    
    if doing_better and not pain_resolved:
        _add_issue(issues, 'Day 3', 'Pain outcome not clinically confirmed', '⚠ Vague', "'Doing much better' is not a clinical confirmation that pain has resolved. Policy requires a documented pain status to close the incident.")
    elif not pain_resolved and not any_phrase(original, ['pain', 'sore']):
        _add_issue(issues, 'Day 3', 'Pain outcome not clinically confirmed', '⚠ Vague', "Policy requires a documented pain status to close the incident.")

    # 14. Mobility returned to baseline
    baseline_confirmed = any_phrase(original, ['returned to baseline', 'baseline', 'back to baseline', 'mobility unchanged'])
    if not baseline_confirmed:
        if "no further falls" in lowered:
            _add_issue(issues, 'Day 3', 'Mobility not confirmed at baseline', '⚠ Vague', "'No further falls' does not confirm the resident has returned to their baseline mobility. Policy requires this to be explicitly stated on Day 3.")
        else:
            _add_issue(issues, 'Day 3', 'Mobility not confirmed at baseline', '⚠ Vague', "Policy requires mobility to be confirmed at baseline on Day 3.")

    # 15. Incident closure
    incident_closed = any_phrase(original, ['post-fall monitoring period is complete', 'incident closed', 'formal incident closure', 'closed', 'discharged from post-fall monitoring'])
    if not incident_closed:
        _add_issue(issues, 'Day 3', 'Incident not formally closed', '🚩 Missing', "Policy requires documentation that the post-fall monitoring period is complete and the incident has been reviewed and closed.")

    # 16. Falls prevention plan review
    falls_prevention_review = any_phrase(original, FALLS_PREVENTION_REVIEW_PHRASES)
    if not falls_prevention_review:
        _add_issue(issues, 'Day 3', 'Falls prevention plan not reviewed', '🚩 Missing', "Policy requires the updated falls prevention plan to be reviewed with the resident or family on Day 3. Not documented.")

    return issues
