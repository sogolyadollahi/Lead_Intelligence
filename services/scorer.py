from core.config import SCORE_WEIGHTS, QUALITY_THRESHOLDS


def score_lead(
    email: str | None,
    company: str | None,
    website: str | None,
    ai_confidence: float,
    email_valid: bool,
) -> tuple[int, str]:
    """
    Returns (lead_score: int, quality_label: str)
    """
    score = 0

    if email_valid and email:
        score += SCORE_WEIGHTS["has_email"]

    if company:
        score += SCORE_WEIGHTS["has_company"]

    if website:
        score += SCORE_WEIGHTS["has_website"]

    # ai_confidence is 0.0–1.0; maps to 0–30 points
    score += int(ai_confidence * SCORE_WEIGHTS["ai_confidence"])

    score = min(score, 100)

    label = "Low"
    for tier, threshold in QUALITY_THRESHOLDS.items():
        if score >= threshold:
            label = tier
            break

    return score, label
