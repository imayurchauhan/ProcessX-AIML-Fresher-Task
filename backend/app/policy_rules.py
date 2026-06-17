from __future__ import annotations

DAY1_REQUIREMENTS = [
    "Date and time of fall",
    "Location of fall",
    "Witnessed/unwitnessed status",
    "Pain score (0-10)",
    "Consciousness and orientation",
    "Visible injury",
    "Ability to move all limbs",
    "Vital signs: BP",
    "Vital signs: HR",
    "Vital signs: RR",
    "Vital signs: Temperature",
    "Vital signs: SpO2",
    "Immediate actions taken",
    "GP name",
    "GP notification time",
    "GP advice",
    "NOK name",
    "NOK notification time",
    "NOK response",
    "Conditional GP actions",
    "Falls history",
    "Medications",
    "Mobility aid status",
    "Care plan reviewed and updated",
    "Falls risk score",
]

DAY2_REQUIREMENTS = [
    "Pain status",
    "Pain score",
    "Mobility status",
    "Full weight-bearing status",
    "New symptoms",
    "Vital signs",
    "GP follow-up",
    "Care plan changes",
]

DAY3_REQUIREMENTS = [
    "Pain outcome",
    "Mobility returned to baseline",
    "Outstanding actions resolved",
    "Formal incident closure",
    "Falls prevention review",
    "Escalation if unstable",
]

ALLOWED_FLAG_TYPES = ["🚩 Missing", "⚠ Vague", "✅ Complete"]

LOCATION_TERMS = [
    "bathroom",
    "bedroom",
    "room",
    "corridor",
    "dining room",
    "lounge",
    "beside bed",
    "living room",
    "hallway",
    "toilet",
    "ensuite",
]

VAGUE_MOBILITY_TERMS = [
    "walking around",
    "mobilising well",
    "moving normally",
    "doing better",
    "up and about",
]

NEW_SYMPTOM_SATISFYING_PHRASES = [
    "no new symptoms",
    "no swelling",
    "no bruising",
    "no confusion",
    "no change",
    "symptoms settled",
]

FALLS_PREVENTION_REVIEW_PHRASES = [
    "falls prevention plan reviewed",
    "reviewed with resident",
    "discussed with family",
    "care plan discussed",
    "falls prevention review",
]

FALLS_HISTORY_PHRASES = [
    "one previous fall",
    "three falls in past year",
    "first recorded fall",
    "history of falls",
    "previous falls",
    "frequent falls",
    "fall history",
    "no previous falls",
    "no falls history",
]

MOBILITY_AID_PHRASES = [
    "walking without aid",
    "uses walking stick",
    "no mobility aid",
    "mobility aid",
    "walking frame",
    "frame",
    "cane",
    "walking stick",
    "aid within reach",
    "within reach",
]

GP_FOLLOWUP_PHRASES = [
    "gp contacted",
    "gp updated",
    "gp informed",
    "gp follow up",
    "follow-up",
    "reviewed by gp",
    "gp reviewed",
    "x-ray result",
    "contacted dr",
    "contacted gp",
    "no x-ray required",
    "continue monitoring",
    "reviewed on day 2",
]

CONDITIONAL_GP_ACTION_PHRASES = [
    "monitor",
    "observe",
    "reassess",
    "arrange x-ray if",
    "keep mobile",
    "monitor pain",
    "observe overnight",
    "monitor mobility",
    "arrange x-ray if pain worsens",
    "hospital transfer if unable to weight bear",
    "x-ray arranged",
    "gp reviewed",
    "follow-up with gp",
]

ESCALATION_PHRASES = [
    "escalate to the care manager",
    "escalated to care manager",
    "escalate",
    "review by care manager",
]
