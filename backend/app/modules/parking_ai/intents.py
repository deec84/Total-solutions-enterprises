"""Conservative intent recognition and evidence-bound answers."""

from app.modules.parking_ai.domain import (
    AssistantIntent,
    ParkingAssessment,
    Recommendation,
)


def interpret_intent(question: str) -> AssistantIntent:
    normalized = " ".join(question.casefold().split())
    if any(term in normalized for term in ("nearest", "nearby", "closest", "cerca")):
        return AssistantIntent.NEAREST_SAFE_PARKING
    if any(term in normalized for term in ("cost", "fee", "price", "costo", "tarifa")):
        return AssistantIntent.TOWING_COST
    if any(term in normalized for term in ("resident", "permit", "residente", "permiso")):
        return AssistantIntent.RESIDENT_PERMIT
    if any(term in normalized for term in ("sign", "letrero", "señal")):
        return AssistantIntent.SIGN_MEANING
    if any(term in normalized for term in ("tow", "towing", "remolque", "grúa", "risk")):
        return AssistantIntent.TOWING_RISK
    return AssistantIntent.PARKING_LEGALITY


def answer_for(intent: AssistantIntent, assessment: ParkingAssessment) -> str:
    if intent is AssistantIntent.NEAREST_SAFE_PARKING:
        return (
            "Open Safer parking nearby to compare verified options ranked by safety, "
            "walking distance, price, towing history, ratings, and availability."
        )
    if intent is AssistantIntent.TOWING_COST:
        if assessment.average_towing_cost_cents is None:
            return "No verified towing-cost estimate is available for this location."
        dollars = assessment.average_towing_cost_cents / 100
        return f"The current estimated towing cost is ${dollars:.2f}; confirm official fees."
    if intent is AssistantIntent.SIGN_MEANING:
        return assessment.restriction_summary or (
            "No verified sign interpretation is attached to this location. Scan the sign "
            "or read it directly before parking."
        )
    if intent is AssistantIntent.RESIDENT_PERMIT:
        if assessment.recommendation is Recommendation.DO_NOT_PARK:
            return "The available evidence does not support parking here without valid permission."
        return (
            assessment.restriction_summary
            or "No verified resident-only restriction is attached to this location."
        )
    if intent is AssistantIntent.TOWING_RISK:
        return (
            f"The parking score is {assessment.score}/100 with risk level "
            f"{assessment.risk_level.value.replace('_', ' ')}."
        )
    return {
        Recommendation.PARK: "The available evidence indicates that parking is likely permitted.",
        Recommendation.CAUTION: "Use caution and read every posted sign before parking.",
        Recommendation.DO_NOT_PARK: "Do not park here based on the available evidence.",
    }[assessment.recommendation]
