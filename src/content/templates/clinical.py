import textwrap


class ClinicalTemplates:
    SOAP = {
        "name": "SOAP Note",
        "root_type": "notes",
        "sub_type": "soap",
        "content": textwrap.dedent("""\
            # SOAP Progress Note

            **Patient:** [patient_name] ([age]yo [gender])
            **Date:** [date]

            ## S - Subjective

            [patient_complaint]

            ## O - Objective

            Vitals: BP [vital_bp] | HR [vital_hr] | Temp [vital_temp] | SpO2 [vital_spo2]

            Physical Exam:
            [physical_exam_finding]

            ## A - Assessment

            [diagnosis]

            ## P - Plan

            1. [plan_item_1]
            2. [plan_item_2]
            3. [plan_item_3]

            **Follow-up:** [follow_up_plan]

            ---
            **Dr. [doctor_name]**
        """),
    }

    HPI = {
        "name": "History of Present Illness",
        "root_type": "notes",
        "sub_type": "hpi",
        "content": textwrap.dedent("""\
            # History of Present Illness

            **Patient:** [patient_name] ([age]yo [gender])
            **Date:** [date]

            ## Chief Complaint

            [chief_complaint]

            ## Onset and Duration

            Began [onset_time] ago. [onset_description]

            ## Character and Severity

            Severity: [pain_severity]/10
            Character: [pain_character]
            Radiation: [radiation]

            ## Aggravating and Alleviating Factors

            - Worse: [aggravating_factors]
            - Better: [alleviating_factors]

            ## Associated Symptoms

            [associated_symptoms]

            ## Current Medications

            [current_medications]

            ## Relevant Past History

            [relevant_past_history]

            ## Summary

            [hpi_summary]

            ---
            **Dr. [doctor_name]**
        """),
    }

    HP = {
        "name": "History and Physical",
        "root_type": "notes",
        "sub_type": "hp",
        "content": textwrap.dedent("""\
            # History and Physical Examination

            **Patient:** [patient_name] ([age]yo [gender])
            **Date:** [date]
            **Attending:** Dr. [doctor_name]

            ## Chief Complaint

            [chief_complaint]

            ## History of Present Illness

            [hpi_narrative]

            ## Past Medical History

            - Medical: [past_medical_conditions]
            - Surgical: [past_surgeries]

            ## Medications

            [current_medications]

            ## Allergies

            [allergies]

            ## Physical Examination

            Vitals: BP [vital_bp] | HR [vital_hr] | RR [vital_rr] | Temp [vital_temp] | SpO2 [vital_spo2]

            General: [exam_general]
            CVS: [exam_cardiovascular]
            Resp: [exam_respiratory]
            Abdomen: [exam_abdomen]
            Neuro: [exam_neurological]

            ## Assessment

            [diagnosis]

            ## Plan

            [treatment_plan]

            ---
            **Dr. [doctor_name]**
        """),
    }

    PROGRESS_NOTE = {
        "name": "Progress Note",
        "root_type": "notes",
        "sub_type": "progress_note",
        "content": textwrap.dedent("""\
            # Progress Note

            **Patient:** [patient_name] ([age]yo [gender])
            **Date:** [date]

            ## Subjective

            [subjective_update]

            ## Objective

            Vitals: [vitals]
            Exam: [exam_findings]

            ## Assessment

            [assessment_update]

            ## Plan

            [plan_update]

            ---
            **Dr. [doctor_name]**
        """),
    }

    CONSULTATION_NOTE = {
        "name": "Consultation Note",
        "root_type": "notes",
        "sub_type": "consultation_note",
        "content": textwrap.dedent("""\
            # Consultation Note

            **Patient:** [patient_name] ([age]yo [gender])
            **Date:** [date]
            **Consultant:** Dr. [doctor_name]

            ## Reason for Consultation

            [reason_for_consultation]

            ## History

            [history]

            ## Examination Findings

            [exam_findings]

            ## Impression

            [impression]

            ## Recommendations

            [recommendations]

            ---
            **Dr. [doctor_name]**
        """),
    }

    @classmethod
    def all(cls):
        return [cls.SOAP, cls.HPI, cls.HP, cls.PROGRESS_NOTE, cls.CONSULTATION_NOTE]
