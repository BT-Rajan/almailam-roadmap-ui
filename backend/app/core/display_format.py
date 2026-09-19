from datetime import date


def format_display_date(value: date) -> str:
    """DD-MM-YYYY -- the same format the frontend's formatDate() shows
    everywhere in the UI. For dates written into user-facing text
    (validation errors, notifications, emails); machine-readable values
    (API fields, storage) stay ISO 8601."""
    return value.strftime("%d-%m-%Y")
