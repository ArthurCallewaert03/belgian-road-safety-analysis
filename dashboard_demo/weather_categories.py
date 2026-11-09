"""Shared, presentation-friendly categories for source weather codes."""

WEATHER_LABELS = {
    "1": "Normal",
    "2": "Rain",
    "3": "Fog",
    "4": "Strong wind",
    "5": "Snow",
    "6": "Hail",
    "7": "Other",
    "9": "Unknown",
}


def weather_category(code):
    if code is None or str(code) in ("<NA>", "nan", "None"):
        return "Unknown"
    return WEATHER_LABELS.get(str(code), "Mixed conditions")
