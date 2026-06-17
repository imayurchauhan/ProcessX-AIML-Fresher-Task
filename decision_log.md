# Decision Log - ProcessX Falls Management Compliance Checker

- **How the Policy was Structured as Input**: 
  - The policy was structured into a set of deterministic, section-by-section rules defined in `backend/app/policy_rules.py` and implemented programmatically in `backend/app/evaluator.py`.
  - Instead of passing raw, unstructured PDF/Word text directly to the LLM (which introduces non-deterministic hallucinations and false positives), the policy rules are mapped to specific requirement fields (e.g., "Pain scale not documented", "Vital signs not recorded").

- **AI Suggestion Changed or Rejected**:
  - The AI suggested flagging each missing vital sign parameter (BP, HR, RR, Temp, SpO2) as an individual line-item flag. 
  - **Why rejected**: In the sample gold standard output for Peter Parker, if vital signs are omitted entirely, they are consolidated into a single flag ("Vital signs not recorded"). Raising 5 separate flags makes the report unnecessarily noisy and cluttered for the nursing staff. I rejected the individual flags and consolidated them into a single warning.

- **Decision the AI Could Not Make**:
  - The AI could not determine the boundary between "monitor/observe" advice (which is vague and lacks clinical utility) and specific conditional actions. 
  - **Resolution**: I designed a lookup pattern where "monitor" or "observe" is flagged as vague *unless* it is accompanied by concrete clinical action thresholds or next-step keywords (such as "X-ray", "hospital transfer", "if unable to weight bear", "if pain worsens"). This ensures we catch vague GP advice while correctly identifying complete plans.
