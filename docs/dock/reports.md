"""Clinical documentation templates."""


class ClinicalTemplates:
    """System templates for clinical notes and documentation."""

    SOAP = {
        "name": "SOAP Note",
        "category": "Progress Notes",
        "description": "Standard Subjective, Objective, Assessment, Plan format for progress notes",
        "content": """
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
        """
    }

    HPI = {
        "name": "History of Present Illness (HPI)",
        "category": "Histories",
        "description": "Focused narrative of the current complaint and presenting symptoms",
        "content": """
            # History of Present Illness

            **Patient:** [patient_name] ([age]yo [gender])
            **Date of Visit:** [date]

            ## Chief Complaint

            [chief_complaint]

            ## Onset and Duration

            Began [onset_time] ago. Started [onset_description].

            ## Character and Severity

            Pain/Severity: [pain_severity]/10
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
        """
    }

    HP = {
        "name": "History and Physical (H&P)",
        "category": "Histories",
        "description": "Comprehensive admission/consultation note with full examination",
        "content": """
            # History and Physical Examination

            **Patient:** [patient_name] ([age]yo [gender] | ID: [identifier])
            **Date:** [date]
            **Attending:** Dr. [doctor_name]

            ---

            ## Chief Complaint

            [chief_complaint]

            ---

            ## History of Present Illness

            [hpi_narrative]

            ---

            ## Past Medical History

            - **Medical:** [past_medical_conditions]
            - **Surgical:** [past_surgeries]
            - **Psychiatric:** [psychiatric_history]

            ---

            ## Medications

            [current_medications]

            ---

            ## Allergies

            [allergies]

            ---

            ## Family History

            [family_history]

            ---

            ## Social History

            - **Occupation:** [occupation]
            - **Tobacco:** [tobacco_use]
            - **Alcohol:** [alcohol_use]
            - **Other:** [other_substance_use]

            ---

            ## Review of Systems

            ### General
            [ros_general]

            ### Constitutional
            [ros_constitutional]

            ### HEENT
            [ros_heent]

            ### Cardiovascular
            [ros_cardiovascular]

            ### Respiratory
            [ros_respiratory]

            ### Gastrointestinal
            [ros_gastrointestinal]

            ### Neurological
            [ros_neurological]

            ---

            ## Physical Examination

            ### Vitals
            BP: [vital_bp] | HR: [vital_hr] | RR: [vital_rr] | Temp: [vital_temp] | SpO2: [vital_spo2]

            ### General
            [exam_general]

            ### HEENT
            [exam_heent]

            ### Cardiovascular
            [exam_cardiovascular]

            ### Respiratory
            [exam_respiratory]

            ### Abdomen
            [exam_abdomen]

            ### Neurological
            [exam_neurological]

            ---

            ## Labs and Imaging

            [lab_results]

            ---

            ## Assessment

            [diagnosis]

            ---

            ## Plan

            [treatment_plan]

            ---
            **Dr. [doctor_name]**
            **Credentials:** [credentials]
        """
    }

    DISCHARGE_SUMMARY = {
        "name": "Discharge Summary",
        "category": "Progress Notes",
        "description": "Summary for hospital discharge or visit conclusion",
        "content": """
            # Discharge Summary

            **Patient:** [patient_name] ([age]yo [gender] | ID: [identifier])
            **Admission Date:** [admission_date]
            **Discharge Date:** [discharge_date]
            **Attending:** Dr. [doctor_name]

            ---

            ## Chief Complaint on Admission

            [chief_complaint]

            ---

            ## Hospital Course

            [hospital_course]

            ---

            ## Discharge Diagnosis

            [discharge_diagnosis]
            1. [diagnosis_1]
            2. [diagnosis_2]
            3. [diagnosis_3]

            ---

            ## Procedures Performed

            [procedures_performed]

            ---

            ## Discharge Medications

            [discharge_medications]

            ---

            ## Discharge Instructions

            [discharge_instructions]

            ### Activity
            [activity_instructions]

            ### Diet
            [diet_instructions]

            ### Warnings
            [warning_signs]

            ---

            ## Follow-up

            [follow_up_plan]

            ---
            **Dr. [doctor_name]**
            [credentials]
        """
    }

    @classmethod
    def all(cls):
        """Return all clinical templates as a list."""
        return [cls.SOAP, cls.HPI, cls.HP, cls.DISCHARGE_SUMMARY]