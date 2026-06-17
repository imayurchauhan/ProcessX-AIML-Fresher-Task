"""
Accuracy evaluation against a gold standard test set.
Run: .venv/Scripts/python.exe -m backend.app.eval_accuracy
"""
from __future__ import annotations
import asyncio
from dataclasses import dataclass

# ── Gold standard test cases ──────────────────────────────────────────────────
# Each case has a note, the day, and the fields expected to be flagged.
# expected_flags: set of (requirement, flag_type) — empty set = fully complete

TEST_CASES = [
    {
        'id': 'day1_complete',
        'day': 'Day 1',
        'note': (
            'Date: 10 June 2025. Time of fall: 07:15. '
            'Resident found on floor beside bed. Fall not witnessed. '
            'Pain 5/10 in left knee. No visible laceration or bruising. '
            'Alert and orientated. Able to move all limbs. '
            'BP 148/86, HR 78, RR 16, Temp 36.5, SpO2 97%. '
            'Assisted back to bed. '
            'GP Dr Santos notified at 07:40. Advised to monitor. '
            'NOK wife notified at 07:55. Acknowledged. '
            'Arrange X-ray if pain worsens. '
            'Two previous falls in past year. Prescribed Warfarin. '
            'Walking frame not within reach. '
            'Care plan reviewed and updated. Falls risk score HIGH.'
        ),
        'expected_flags': set(),  # fully complete
    },
    {
        'id': 'day1_missing_vitals',
        'day': 'Day 1',
        'note': (
            'Date: 10 June 2025. Time of fall: 07:15. '
            'Resident found on floor beside bed. Fall not witnessed. '
            'Pain 5/10. No visible injury. Alert and orientated. Able to move all limbs. '
            'Assisted back to bed. '
            'GP Dr Santos notified at 07:40. Advised to monitor. '
            'NOK wife notified at 07:55. Acknowledged. '
            'Monitor pain. Two previous falls. Prescribed Warfarin. '
            'Walking frame not within reach. '
            'Care plan reviewed and updated. Falls risk score HIGH.'
        ),
        'expected_flags': {
            ('Vital signs: BP', 'Missing'),
            ('Vital signs: HR', 'Missing'),
            ('Vital signs: RR', 'Missing'),
            ('Vital signs: Temperature', 'Missing'),
            ('Vital signs: SpO2', 'Missing'),
        },
    },
    {
        'id': 'day1_vague_care_plan',
        'day': 'Day 1',
        'note': (
            'Date: 10 June 2025. Time of fall: 08:00. '
            'Resident found on floor in corridor. Unwitnessed. '
            'Pain 3/10. No bruising. Alert and orientated. Able to move all limbs. '
            'BP 130/80, HR 72, RR 14, Temp 36.6, SpO2 98%. '
            'Returned to bed. '
            'GP Dr Lee notified at 08:15. Advised to observe. '
            'NOK son notified at 08:30. Will visit. '
            'Monitor mobility. First recorded fall. No medications. '
            'Uses walking stick. '
            'Will update care plan. Falls risk score medium.'
        ),
        'expected_flags': {
            ('Care plan reviewed and updated', 'Vague'),
        },
    },
    {
        'id': 'day2_complete',
        'day': 'Day 2',
        'note': (
            'Pain 2/10, improved since yesterday. '
            'Full weight-bearing on both legs. Gait steady. '
            'BP 135/82, HR 74. '
            'No new symptoms, no swelling or bruising. '
            'GP contacted Dr Santos, no X-ray required. '
            'No changes required to care plan.'
        ),
        'expected_flags': set(),
    },
    {
        'id': 'day2_vague_mobility',
        'day': 'Day 2',
        'note': (
            'Pain 2/10. '
            'Resident up and about today, mobilising well. '
            'BP 135/82, HR 74. '
            'No new symptoms. '
            'GP updated, continue monitoring. '
            'Care plan unchanged.'
        ),
        'expected_flags': {
            ('Mobility status', 'Vague'),
        },
    },
    {
        'id': 'day3_complete',
        'day': 'Day 3',
        'note': (
            'Pain resolved, 0/10. '
            'Mobility returned to baseline. '
            'No outstanding clinical actions, X-ray not required confirmed by GP. '
            'Post-fall monitoring period is complete. Incident closed. '
            'Falls prevention plan reviewed with resident and family.'
        ),
        'expected_flags': set(),
    },
    {
        'id': 'day3_missing_closure',
        'day': 'Day 3',
        'note': (
            'Pain resolved. '
            'Returned to baseline mobility. '
            'No outstanding actions. '
            'Falls prevention plan reviewed with resident.'
        ),
        'expected_flags': {
            ('Formal incident closure', 'Missing'),
        },
    },
]


@dataclass
class EvalResult:
    case_id: str
    day: str
    expected: set
    got: set
    true_positives: set    # correctly flagged
    false_positives: set   # flagged but shouldn't be
    false_negatives: set   # should be flagged but weren't


async def run_evaluation(use_llm: bool = False) -> None:
    from backend.app.evaluator import _evaluate_day_sync, evaluate_note_with_groq
    from backend.app.llm import groq_available
    from backend.app.evaluator import _findings_to_issues

    results: list[EvalResult] = []

    for case in TEST_CASES:
        day = case['day']
        note = case['note']

        if use_llm and groq_available():
            raw = await evaluate_note_with_groq(day, note)
            issues = _findings_to_issues(day, raw) if raw else _evaluate_day_sync(day, note)
        else:
            issues = _evaluate_day_sync(day, note)

        got_flags = {(i.requirement, i.flag_type) for i in issues}
        expected_flags = case['expected_flags']

        tp = got_flags & expected_flags
        fp = got_flags - expected_flags
        fn = expected_flags - got_flags

        results.append(EvalResult(
            case_id=case['id'],
            day=day,
            expected=expected_flags,
            got=got_flags,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
        ))

    # ── Print report ──────────────────────────────────────────────────────────
    engine = 'Groq LLM' if (use_llm and groq_available()) else 'Rule-based'
    print(f'\n{"="*60}')
    print(f'  Accuracy Report  |  Engine: {engine}')
    print(f'{"="*60}')

    total_tp = total_fp = total_fn = 0

    for r in results:
        status = 'PASS' if not r.false_positives and not r.false_negatives else 'FAIL'
        print(f'\n[{status}] {r.case_id} ({r.day})')
        if r.false_positives:
            for req, flag in sorted(r.false_positives):
                print(f'  FALSE POSITIVE: flagged "{req}" as {flag} (should be complete)')
        if r.false_negatives:
            for req, flag in sorted(r.false_negatives):
                print(f'  FALSE NEGATIVE: missed "{req}" ({flag})')
        total_tp += len(r.true_positives)
        total_fp += len(r.false_positives)
        total_fn += len(r.false_negatives)

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 1.0
    recall    = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 1.0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    passed    = sum(1 for r in results if not r.false_positives and not r.false_negatives)

    print(f'\n{"-"*60}')
    print(f'  Cases passed  : {passed}/{len(results)}')
    print(f'  Precision     : {precision:.1%}  (of flags raised, how many were correct)')
    print(f'  Recall        : {recall:.1%}  (of real issues, how many were caught)')
    print(f'  F1 Score      : {f1:.1%}')
    print(f'{"="*60}\n')


if __name__ == '__main__':
    import sys
    use_llm = '--llm' in sys.argv
    asyncio.run(run_evaluation(use_llm=use_llm))
