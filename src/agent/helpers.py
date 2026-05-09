def format_patient_context(ctx: dict | None) -> str:
    if not ctx:
        return "No patient linked to this conversation."
    parts = [
        f"Name: {ctx.get('first_name', 'Unknown')} {ctx.get('last_name', '')}",
    ]
    if ctx.get("date_of_birth"):
        parts.append(f"DOB: {ctx['date_of_birth']}")
    if ctx.get("gender"):
        parts.append(f"Gender: {ctx['gender']}")
    if ctx.get("blood_group"):
        parts.append(f"Blood Group: {ctx['blood_group']}")
    return ", ".join(parts)


def format_session_context(ctx: dict | None) -> str:
    if not ctx:
        return "No active session."
    return (
        f"Title: {ctx.get('title', 'N/A')}\n"
        f"Status: {ctx.get('status', 'N/A')}\n"
        f"Summary: {ctx.get('clinical_summary', 'No summary yet')}"
    )
