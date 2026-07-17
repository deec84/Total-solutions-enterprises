"""Conservative sign-language extraction without inventing legal meaning."""

import re


class SignInterpreter:
    def interpret(self, text: str) -> tuple[str, tuple[str, ...], int]:
        normalized = " ".join(text.casefold().split())
        restrictions: list[str] = []
        risk = 50
        if re.search(r"\b(no parking|no estacionar|no estacionamiento)\b", normalized):
            restrictions.append("Parking is prohibited.")
            risk = 100
        if re.search(r"\b(tow away|tow-away|remolque|grúa)\b", normalized):
            restrictions.append("Vehicles may be towed.")
            risk = max(risk, 95)
        if re.search(r"\b(resident|residents|residente|permiso)\b", normalized):
            restrictions.append("A resident or parking permit may be required.")
            risk = max(risk, 80)
        if re.search(r"\b(loading|carga|commercial vehicles)\b", normalized):
            restrictions.append("The space may be restricted to loading or commercial use.")
            risk = max(risk, 75)
        day_pattern = (
            r"\b(mon|tue|wed|thu|fri|sat|sun|lunes|martes|miércoles|jueves|viernes)\b"
        )
        if re.search(day_pattern, normalized):
            restrictions.append("The restriction applies only on specified days; verify the sign.")
        if re.search(r"\b\d{1,2}(:\d{2})?\s*(am|pm)\b", normalized):
            restrictions.append("The restriction applies during specified hours; verify the sign.")
        if not restrictions:
            return (
                "The sign could not be interpreted confidently. Read it directly before parking.",
                (),
                70,
            )
        return " ".join(restrictions), tuple(restrictions), risk
