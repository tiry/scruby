"""Custom recognizers for HIPAA compliance."""

from presidio_analyzer import Pattern, PatternRecognizer


class SSNRecognizer(PatternRecognizer):
    """
    Recognizer for US Social Security Numbers (SSN).
    
    Detects SSN in various formats:
    - 123-45-6789
    - 123 45 6789
    - SSN: 123-45-6789
    - Social Security Number: 123-45-6789
    """
    
    PATTERNS = [
        Pattern(
            name="ssn_dashes",
            regex=r"\b\d{3}-\d{2}-\d{4}\b",
            score=0.95  # High score for strong pattern
        ),
        Pattern(
            name="ssn_spaces",
            regex=r"\b\d{3}\s\d{2}\s\d{4}\b",
            score=0.95
        ),
        Pattern(
            name="ssn_no_separators",
            regex=r"\b\d{9}\b",
            score=0.60  # Lower score as it's less specific
        ),
    ]
    
    def __init__(self):
        super().__init__(
            supported_entity="US_SSN",
            patterns=self.PATTERNS,
            context=["ssn", "social security", "social", "security"]
        )


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


class InternationalPhoneRecognizer(PatternRecognizer):
    """
    Recognizer for international phone numbers.
    
    Detects international phone numbers with country codes:
    - +91 1234567890 (India)
    - +44 20 1234 5678 (UK)
    - +1 234 567 8900 (US)
    - +86 138 0000 0000 (China)
    """
    
    PATTERNS = [
        Pattern(
            name="intl_phone_with_plus",
            regex=r"\+\d{1,3}\s?\d{7,15}",
            score=0.85
        ),
        Pattern(
            name="intl_phone_formatted",
            regex=r"\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,9}",
            score=0.80
        ),
    ]
    
    def __init__(self):
        super().__init__(
            supported_entity="PHONE_NUMBER",
            patterns=self.PATTERNS,
            context=["phone", "mobile", "tel", "contact", "call"]
        )
