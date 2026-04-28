"""Prompt templates for session title and summary generation."""

import textwrap


class ScribePrompts:
    TITLE = textwrap.dedent("""\
        You are a medical scribe. Generate a concise 3-word title for this consultation session.

        **TRANSCRIPTS:**
        {transcripts}

        **INSTRUCTIONS:**
        - Return ONLY a 3-word title (e.g., "Follow-up: Hypertension")
        - Do NOT include quotes or extra text
        - Focus on the primary reason for visit
    """)

    SUMMARY_UPDATE = textwrap.dedent("""\
        You are a medical scribe. Update the following clinical summary with new transcript information.

        **EXISTING SUMMARY:**
        {existing_summary}

        **NEW TRANSCRIPTS:**
        {transcripts}

        **INSTRUCTIONS:**
        - Return an updated clinical summary in Markdown format
        - Write as 4-5 concise paragraphs with simple section headers
        - Use ## for section headers (format: ## Header Name)
        - Use **bold** only for critical information within paragraphs (diagnoses, warnings)
        - First paragraph: Reason for visit and presenting symptoms
        - Second paragraph: Relevant history and background
        - Third paragraph: Assessment/diagnosis and treatment plan
        - Fourth paragraph: Key questions asked by the doctor (medicolegal documentation)
        - Fifth paragraph (if applicable): Follow-up plan and next steps

        **CRITICAL — Questions Section:**
        - Document ALL important questions the doctor asked the patient
        - Include BOTH positive responses ("Patient reports chest pain") AND negative responses ("Patient denies fever")
        - Capture questions about symptoms, medications, allergies, family history

        - Keep it brief and natural — like a doctor's quick note
        - Preserve existing information unless contradicted by new transcripts
        - If existing_summary is empty, create a new summary
    """)
