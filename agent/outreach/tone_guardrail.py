from __future__ import annotations


def apply_tone_guardrail(text: str) -> str:
    replacements = {
        "guarantee": "aim to",
        "always": "typically",
        "best-in-class": "high-performing",
        "revolutionary": "practical",
    }
    output = text
    for src, dest in replacements.items():
        output = output.replace(src, dest)
        output = output.replace(src.capitalize(), dest.capitalize())
    return output
