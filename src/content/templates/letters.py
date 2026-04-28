import textwrap


class LetterTemplates:
    REFERRAL = {
        "name": "Referral Letter",
        "root_type": "letters",
        "sub_type": "referral",
        "content": textwrap.dedent("""\
            # Referral Letter

            **Date:** [date]

            **To:**
            Dr. [referral_doctor_name]
            [referral_specialty]
            [referral_hospital]

            **Re:** [patient_name] ([age]yo [gender])

            Dear Dr. [referral_doctor_name],

            ## Reason for Referral

            [reason_for_referral]

            ## Clinical Summary

            [clinical_summary]

            ## Relevant History

            [relevant_history]

            ## Investigations Done

            [investigations_done]

            ## Request

            [referral_request]

            Thank you for seeing this patient.

            Yours sincerely,

            **Dr. [doctor_name]**
            [credentials]
        """),
    }

    DISCHARGE_SUMMARY = {
        "name": "Discharge Summary",
        "root_type": "letters",
        "sub_type": "discharge_summary",
        "content": textwrap.dedent("""\
            # Discharge Summary

            **Patient:** [patient_name] ([age]yo [gender])
            **Admission Date:** [admission_date]
            **Discharge Date:** [discharge_date]
            **Attending:** Dr. [doctor_name]

            ## Chief Complaint on Admission

            [chief_complaint]

            ## Hospital Course

            [hospital_course]

            ## Discharge Diagnosis

            [discharge_diagnosis]

            ## Procedures Performed

            [procedures_performed]

            ## Discharge Medications

            [discharge_medications]

            ## Discharge Instructions

            [discharge_instructions]

            ## Follow-up

            [follow_up_plan]

            ---
            **Dr. [doctor_name]**
        """),
    }

    MEDICAL_LEAVE = {
        "name": "Medical Leave Certificate",
        "root_type": "letters",
        "sub_type": "medical_leave",
        "content": textwrap.dedent("""\
            # Medical Leave Certificate

            **Date:** [date]

            This is to certify that **[patient_name]** ([age]yo [gender]) is under my medical care for [condition].

            **Period of Leave:** From [leave_from] to [leave_to] ([duration_days] days)

            **Recommendation:** [recommendation]

            Issued at [hospital_name] on [date].

            **Dr. [doctor_name]**
            [credentials]
        """),
    }

    DOCTOR_NOTE = {
        "name": "Doctor's Note",
        "root_type": "letters",
        "sub_type": "doctor_note",
        "content": textwrap.dedent("""\
            # Doctor's Note

            **Date:** [date]

            **To Whom It May Concern,**

            This is to confirm that **[patient_name]** ([age]yo [gender]) was seen by me on [visit_date] for [visit_reason].

            [additional_details]

            Please excuse the patient for [absence_period].

            **Dr. [doctor_name]**
            [credentials]
        """),
    }

    @classmethod
    def all(cls):
        return [cls.REFERRAL, cls.DISCHARGE_SUMMARY, cls.MEDICAL_LEAVE, cls.DOCTOR_NOTE]
