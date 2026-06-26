"""
Legal & Compliance Agent

AI-powered legal document analysis, contract review, and regulatory compliance checking.
"""

__version__ = "1.0.0"
__author__ = "Legal & Compliance Agent Team"
__license__ = "MIT"

from src.contract_analyzer import ContractAnalyzer
from src.compliance_checker import ComplianceChecker
from src.legal_qa import LegalQASystem
from src.clause_extractor import ClauseExtractor
from src.policy_generator import PolicyGenerator
from src.risk_assessor import RiskAssessor

__all__ = [
    "ContractAnalyzer",
    "ComplianceChecker",
    "LegalQASystem",
    "ClauseExtractor",
    "PolicyGenerator",
    "RiskAssessor",
]
