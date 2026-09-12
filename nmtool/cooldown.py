from __future__ import annotations

import re


CLOCK = re.compile(r"\b(?:(\d+):)?([0-5]?\d):([0-5]\d)\b")


def parse_cooldown(text: str) -> int | None:
    text = " ".join(text.lower().split())
    clock = CLOCK.search(text)
    if clock:
        hours, minutes, seconds = (int(value or 0) for value in clock.groups())
        return hours * 3600 + minutes * 60 + seconds
    hour_match = re.search(r"(\d+)\s*(?:timer?|t|h)\b", text, re.I)
    minute_match = re.search(r"(\d+)\s*(?:minutter?|min|m)\b", text, re.I)
    second_match = re.search(r"(\d+)\s*(?:sekunder?|sek|s)\b", text, re.I)
    if not any((hour_match, minute_match, second_match)):
        return None
    hours = int(hour_match.group(1)) if hour_match else 0
    minutes = int(minute_match.group(1)) if minute_match else 0
    seconds = int(second_match.group(1)) if second_match else 0
    return hours * 3600 + minutes * 60 + seconds
