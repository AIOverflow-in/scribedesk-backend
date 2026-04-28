import textwrap


class ReportPrompts:
    SYSTEM_PROMPT = "You are a medical scribe specializing in clinical documentation."

    GENERATE_FROM_TEMPLATE = textwrap.dedent("""\
        Generate a clinical report using the following template.

        **CURRENT DATE:** {current_date}

        **CONTEXT:**
        {context}

        **TRANSCRIPTS:**
        {transcripts}

        **TEMPLATE:**
        {template_content}

        **INSTRUCTIONS:**
        - Fill in all the placeholders in the template based on the transcripts and context
        - Preserve all Markdown formatting from the template (headers, bold, lists, etc.)
        - Use the CURRENT DATE for date fields, and doctor/clinic info from context
        - Return ONLY the completed template in Markdown format, nothing else

        **CRITICAL: Do NOT hallucinate medical facts.**
        - You MAY use: current date, doctor name, clinic details, patient demographics
        - You MAY include standard medical certificate language (e.g., "To Whom It May Concern", "Please note:", etc.)
        - DO NOT invent: diagnosis, specific symptoms, treatment dates, recovery periods, medical recommendations
        - If medical details are not mentioned in transcripts, leave those specific fields blank or use generic placeholders like "---" or "(pending medical review)"
    """)
