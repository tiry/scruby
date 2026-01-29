"""Custom recognizers for HIPAA compliance."""

from presidio_analyzer import Pattern, PatternRecognizer


class MRNRecognizer(PatternRecognizer):
    """
    Recognizer for Medical Record Numbers (MRN).
    
    Detects common MRN formats:
    - MRN: 12345678
    - MRN-12345678
    - Medical Record: 12345678
    """
    
    PATTERNS = [
        Pattern(
            name="mrn_with_prefix",
            regex=r"\bMRN[:\-\s]?\d{6,10}\b",
            score=0.85
        ),
        Pattern(
            name="medical_record_with_prefix",
            regex=r"\bMedical\s+Record[:\-\s]?\d{6,10}\b",
            score=0.85
        ),
    ]
    
    def __init__(self):
        super().__init__(
            supported_entity="MEDICAL_RECORD_NUMBER",
            patterns=self.PATTERNS,
            context=["patient", "medical", "record", "chart"]
        )


class PrescriptionNumberRecognizer(PatternRecognizer):
    """
    Recognizer for prescription numbers.
    
    Detects formats like:
    - RX: 1234567
    - Prescription #1234567
    """
    
    PATTERNS = [
        Pattern(
            name="rx_with_prefix",
            regex=r"\bRX[:\-\s#]?\d{6,10}\b",
            score=0.80
        ),
        Pattern(
            name="prescription_with_prefix",
            regex=r"\bPrescription\s+[#:\-\s]?\d{6,10}\b",
            score=0.80
        ),
    ]
    
    def __init__(self):
        super().__init__(
            supported_entity="PRESCRIPTION_NUMBER",
            patterns=self.PATTERNS,
            context=["prescription", "medication", "pharmacy", "drug"]
        )


class InsuranceIDRecognizer(PatternRecognizer):
    """
    Recognizer for health insurance ID numbers.
    
    Detects formats like:
    - Insurance ID: ABC123456789
    - Member ID: 123456789
    """
    
    PATTERNS = [
        Pattern(
            name="insurance_id",
            regex=r"\b(?:Insurance|Member)\s+ID[:\-\s]?[A-Z0-9]{9,15}\b",
            score=0.75
        ),
        Pattern(
            name="policy_number",
            regex=r"\bPolicy\s+(?:Number|#)[:\-\s]?[A-Z0-9]{9,15}\b",
            score=0.75
        ),
    ]
    
    def __init__(self):
        super().__init__(
            supported_entity="INSURANCE_ID",
            patterns=self.PATTERNS,
            context=["insurance", "policy", "coverage", "member"]
        )
