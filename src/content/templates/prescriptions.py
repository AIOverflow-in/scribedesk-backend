import textwrap


class PrescriptionTemplates:
    DEFAULT = {
        "name": "Prescription",
        "root_type": "prescription",
        "sub_type": None,
        "content": textwrap.dedent("""\
            # Prescription

            **Patient:** [patient_name] ([age]yo [gender])
            **Date:** [date]

            [medications_table]

            **Dr. [doctor_name]**
            [credentials]

            *Note: Structured medication data (name, dosage, form, frequency, duration) is stored in the report metadata.*
        """),
    }

    @classmethod
    def all(cls):
        return [cls.DEFAULT]
