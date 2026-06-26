"""
Legal risk identification and scoring system.
"""

import logging
import re
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict
import uuid

from src.models import (
    LegalRisk,
    RiskLevel,
    DocumentType,
)


logger = logging.getLogger(__name__)


class RiskAssessor:
    """Assesses legal risks in documents."""

    def __init__(self):
        """Initialize risk assessor."""
        self.risk_patterns = self._build_risk_patterns()
        logger.info("RiskAssessor initialized")

    def _build_risk_patterns(self) -> Dict[str, Dict]:
        """Build risk patterns and rules."""
        return {
            "unlimited_liability": {
                "patterns": [
                    r'unlimited\s+liabilit(?:y|ies)',
                    r'no\s+(?:limit|limitation|cap).*liabilit',
                    r'liabilit.*unlimited',
                ],
                "level": RiskLevel.CRITICAL,
                "category": "Liability",
                "description": "Unlimited liability exposure detected",
                "recommendation": "Negotiate a liability cap to limit financial exposure",
            },
            "termination_at_will": {
                "patterns": [
                    r'terminat(?:e|ion)\s+at\s+will',
                    r'terminat(?:e|ion)\s+without\s+cause',
                    r'(?:immediate|instant).*terminat',
                ],
                "level": RiskLevel.HIGH,
                "category": "Termination",
                "description": "At-will termination clause allows termination without cause",
                "recommendation": "Negotiate for reasonable notice period and termination for cause only",
            },
            "broad_ip_assignment": {
                "patterns": [
                    r'all\s+(?:intellectual\s+property|ip|rights).*(?:assigned|belongs|transferred)',
                    r'work\s+for\s+hire',
                    r'assign.*all.*intellectual\s+property',
                ],
                "level": RiskLevel.HIGH,
                "category": "Intellectual Property",
                "description": "Broad intellectual property assignment detected",
                "recommendation": "Clarify scope of IP assignment and retain rights to pre-existing IP",
            },
            "automatic_renewal": {
                "patterns": [
                    r'automat(?:ic|ically).*renew',
                    r'renew.*automat(?:ic|ically)',
                    r'perpetual.*unless.*terminated',
                ],
                "level": RiskLevel.MEDIUM,
                "category": "Term and Renewal",
                "description": "Automatic renewal clause may lock in commitment",
                "recommendation": "Ensure clear opt-out process and reasonable notice period for non-renewal",
            },
            "one_sided_modification": {
                "patterns": [
                    r'(?:we|company).*(?:may|can|reserve.*right).*(?:modify|change|amend).*at\s+(?:any\s+)?time',
                    r'sole\s+discretion.*(?:modify|change|amend)',
                ],
                "level": RiskLevel.MEDIUM,
                "category": "Amendment",
                "description": "One-sided modification rights detected",
                "recommendation": "Negotiate mutual consent requirement for material changes",
            },
            "binding_arbitration": {
                "patterns": [
                    r'binding\s+arbitration',
                    r'arbitration.*(?:sole|exclusive).*(?:remedy|forum)',
                    r'waive.*(?:right.*)?(?:jury\s+trial|litigation)',
                ],
                "level": RiskLevel.MEDIUM,
                "category": "Dispute Resolution",
                "description": "Mandatory binding arbitration limits legal options",
                "recommendation": "Evaluate impact of arbitration clause on your rights",
            },
            "class_action_waiver": {
                "patterns": [
                    r'waive.*class\s+action',
                    r'no\s+class\s+action',
                    r'individual\s+basis\s+only',
                ],
                "level": RiskLevel.MEDIUM,
                "category": "Dispute Resolution",
                "description": "Class action waiver restricts collective legal action",
                "recommendation": "Consider implications of waiving class action rights",
            },
            "broad_indemnification": {
                "patterns": [
                    r'indemnif.*(?:any|all).*(?:claims|losses|damages)',
                    r'indemnif.*(?:including|without\s+limitation)',
                    r'defend.*hold\s+harmless.*all',
                ],
                "level": RiskLevel.HIGH,
                "category": "Indemnification",
                "description": "Broad indemnification obligation detected",
                "recommendation": "Limit indemnification to claims arising from your negligence or breach",
            },
            "non_compete": {
                "patterns": [
                    r'(?:covenant|agree).*not.*compet',
                    r'non-compete',
                    r'refrain.*competing.*business',
                ],
                "level": RiskLevel.HIGH,
                "category": "Non-Compete",
                "description": "Non-compete clause restricts future business activities",
                "recommendation": "Ensure reasonable scope, duration, and geographic limitations",
            },
            "perpetual_confidentiality": {
                "patterns": [
                    r'perpetual.*confidential',
                    r'confidential.*perpetual',
                    r'confidential.*indefinite',
                ],
                "level": RiskLevel.MEDIUM,
                "category": "Confidentiality",
                "description": "Perpetual confidentiality obligation",
                "recommendation": "Negotiate time-limited confidentiality (typically 3-5 years)",
            },
            "payment_discretion": {
                "patterns": [
                    r'payment.*sole\s+discretion',
                    r'discretion.*payment',
                    r'(?:may|might).*(?:withhold|delay).*payment',
                ],
                "level": RiskLevel.HIGH,
                "category": "Payment",
                "description": "Payment subject to sole discretion creates uncertainty",
                "recommendation": "Establish objective criteria for payment obligations",
            },
            "warranty_disclaimer": {
                "patterns": [
                    r'as\s+is',
                    r'without\s+warrant(?:y|ies)',
                    r'no\s+warrant(?:y|ies)',
                    r'disclaim.*all.*warrant(?:y|ies)',
                ],
                "level": RiskLevel.MEDIUM,
                "category": "Warranties",
                "description": "Broad warranty disclaimer shifts risk to you",
                "recommendation": "Negotiate for basic warranties (title, authority, non-infringement)",
            },
            "missing_force_majeure": {
                "patterns": [],  # Absence pattern
                "level": RiskLevel.LOW,
                "category": "Force Majeure",
                "description": "Missing force majeure clause",
                "recommendation": "Add force majeure clause to protect against unforeseen events",
            },
            "data_breach_liability": {
                "patterns": [
                    r'(?:responsible|liable).*(?:data\s+breach|security\s+incident)',
                    r'indemnif.*data\s+breach',
                ],
                "level": RiskLevel.HIGH,
                "category": "Data Protection",
                "description": "Liability for data breaches beyond your control",
                "recommendation": "Limit liability to breaches caused by your negligence",
            },
            "regulatory_compliance": {
                "patterns": [
                    r'responsible.*(?:all|any).*compliance',
                    r'ensure.*compliance.*(?:laws|regulations)',
                ],
                "level": RiskLevel.MEDIUM,
                "category": "Compliance",
                "description": "Broad regulatory compliance obligations",
                "recommendation": "Clarify which party is responsible for specific compliance areas",
            },
        }

    def assess_risks(
        self,
        document_text: str,
        document_type: DocumentType = DocumentType.CONTRACT,
        risk_categories: Optional[List[str]] = None,
        include_remediation: bool = True,
    ) -> Dict:
        """
        Assess legal risks in a document.

        Args:
            document_text: Text of the document
            document_type: Type of document
            risk_categories: Specific risk categories to assess
            include_remediation: Include remediation suggestions

        Returns:
            Dictionary with risk assessment results
        """
        logger.info(f"Assessing risks in {document_type.value} document")
        start_time = datetime.now()

        risks = []
        text_lower = document_text.lower()

        # Assess pattern-based risks
        for risk_id, risk_data in self.risk_patterns.items():
            # Skip if specific categories requested and this isn't one
            if risk_categories and risk_data["category"] not in risk_categories:
                continue

            patterns = risk_data["patterns"]

            # Handle absence patterns (like missing force majeure)
            if not patterns:
                if risk_id == "missing_force_majeure" and "force majeure" not in text_lower:
                    risks.append(self._create_risk(risk_id, risk_data, None, document_text))
                continue

            # Check for pattern matches
            for pattern in patterns:
                matches = list(re.finditer(pattern, text_lower))
                if matches:
                    # Use first match for context
                    match = matches[0]
                    risks.append(self._create_risk(risk_id, risk_data, match, document_text))
                    break  # Only report once per risk type

        # Document type specific risks
        type_specific_risks = self._assess_document_type_risks(document_text, document_type)
        risks.extend(type_specific_risks)

        # Calculate overall risk score
        overall_risk_score = self._calculate_overall_risk_score(risks)

        # Determine overall risk level
        if overall_risk_score >= 7.5:
            overall_risk_level = RiskLevel.CRITICAL
        elif overall_risk_score >= 5.5:
            overall_risk_level = RiskLevel.HIGH
        elif overall_risk_score >= 3.5:
            overall_risk_level = RiskLevel.MEDIUM
        else:
            overall_risk_level = RiskLevel.LOW

        # Calculate risk distribution
        risk_distribution = defaultdict(int)
        for risk in risks:
            risk_distribution[risk.risk_level] += 1

        # Extract key concerns
        key_concerns = self._extract_key_concerns(risks)

        # Generate recommendations
        recommendations = self._generate_recommendations(risks) if include_remediation else []

        processing_time = (datetime.now() - start_time).total_seconds()

        logger.info(
            f"Risk assessment completed in {processing_time:.2f}s. "
            f"Overall risk score: {overall_risk_score:.1f}/10, "
            f"Level: {overall_risk_level.value}"
        )

        return {
            "overall_risk_score": overall_risk_score,
            "risk_level": overall_risk_level,
            "risks": risks,
            "risk_distribution": dict(risk_distribution),
            "key_concerns": key_concerns,
            "recommendations": recommendations,
            "processing_time": processing_time,
        }

    def _create_risk(
        self,
        risk_id: str,
        risk_data: Dict,
        match: Optional[re.Match],
        document_text: str,
    ) -> LegalRisk:
        """Create a LegalRisk object from pattern match."""
        if match:
            # Extract context around match
            start = max(0, match.start() - 100)
            end = min(len(document_text), match.end() + 100)
            affected_clause = document_text[start:end]
        else:
            affected_clause = None

        return LegalRisk(
            risk_id=f"{risk_id}_{uuid.uuid4().hex[:8]}",
            risk_level=risk_data["level"],
            category=risk_data["category"],
            description=risk_data["description"],
            affected_clause=affected_clause,
            recommendation=risk_data["recommendation"],
            confidence=0.85 if match else 0.60,
        )

    def _assess_document_type_risks(
        self,
        document_text: str,
        document_type: DocumentType,
    ) -> List[LegalRisk]:
        """Assess risks specific to document type."""
        risks = []
        text_lower = document_text.lower()

        if document_type == DocumentType.EMPLOYMENT_AGREEMENT:
            # Check for employment-specific risks
            if "at-will" in text_lower or "at will" in text_lower:
                risks.append(
                    LegalRisk(
                        risk_id=f"employment_at_will_{uuid.uuid4().hex[:8]}",
                        risk_level=RiskLevel.MEDIUM,
                        category="Employment",
                        description="At-will employment allows termination without cause",
                        affected_clause=None,
                        recommendation="Understand your rights and consider negotiating for cause requirements",
                        confidence=0.90,
                    )
                )

        elif document_type == DocumentType.NDA:
            # Check for NDA-specific risks
            if "unilateral" in text_lower or "one-way" in text_lower:
                risks.append(
                    LegalRisk(
                        risk_id=f"nda_unilateral_{uuid.uuid4().hex[:8]}",
                        risk_level=RiskLevel.LOW,
                        category="Confidentiality",
                        description="Unilateral NDA places obligations only on one party",
                        affected_clause=None,
                        recommendation="Consider mutual NDA if both parties will share confidential information",
                        confidence=0.80,
                    )
                )

        elif document_type == DocumentType.LICENSE_AGREEMENT:
            # Check for license-specific risks
            if "non-exclusive" not in text_lower:
                risks.append(
                    LegalRisk(
                        risk_id=f"license_exclusivity_{uuid.uuid4().hex[:8]}",
                        risk_level=RiskLevel.MEDIUM,
                        category="Licensing",
                        description="License exclusivity not clearly specified",
                        affected_clause=None,
                        recommendation="Clarify whether license is exclusive or non-exclusive",
                        confidence=0.70,
                    )
                )

        return risks

    def _calculate_overall_risk_score(self, risks: List[LegalRisk]) -> float:
        """Calculate overall risk score (0-10 scale)."""
        if not risks:
            return 0.0

        risk_weights = {
            RiskLevel.CRITICAL: 10.0,
            RiskLevel.HIGH: 7.0,
            RiskLevel.MEDIUM: 4.0,
            RiskLevel.LOW: 2.0,
            RiskLevel.INFO: 0.5,
        }

        # Calculate weighted average with confidence
        total_weight = 0.0
        for risk in risks:
            weight = risk_weights.get(risk.risk_level, 2.0)
            total_weight += weight * risk.confidence

        # Normalize to 0-10 scale
        if len(risks) > 0:
            # Average per risk, but cap at 10
            score = min(10.0, total_weight / len(risks))
        else:
            score = 0.0

        return round(score, 1)

    def _extract_key_concerns(self, risks: List[LegalRisk]) -> List[str]:
        """Extract key concerns from risks."""
        concerns = []

        # Group risks by category
        by_category = defaultdict(list)
        for risk in risks:
            by_category[risk.category].append(risk)

        # Highlight critical and high risks
        critical_risks = [r for r in risks if r.risk_level == RiskLevel.CRITICAL]
        high_risks = [r for r in risks if r.risk_level == RiskLevel.HIGH]

        if critical_risks:
            concerns.append(
                f"CRITICAL: {len(critical_risks)} critical risk(s) require immediate attention"
            )
            for risk in critical_risks[:3]:  # Top 3
                concerns.append(f"- {risk.description}")

        if high_risks:
            concerns.append(f"HIGH: {len(high_risks)} high-severity risk(s) identified")

        # Highlight categories with multiple risks
        for category, category_risks in by_category.items():
            if len(category_risks) >= 3:
                concerns.append(
                    f"Multiple risks in {category} category ({len(category_risks)} issues)"
                )

        return concerns[:10]  # Limit to top concerns

    def _generate_recommendations(self, risks: List[LegalRisk]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Prioritize by risk level
        critical_risks = [r for r in risks if r.risk_level == RiskLevel.CRITICAL]
        high_risks = [r for r in risks if r.risk_level == RiskLevel.HIGH]

        if critical_risks:
            recommendations.append(
                "URGENT: Address critical risks before signing. Consult with legal counsel immediately."
            )

        if high_risks:
            recommendations.append(
                "Negotiate high-severity risks or seek legal advice before proceeding."
            )

        # Add specific recommendations from risks
        for risk in sorted(risks, key=lambda r: (r.risk_level.value, -r.confidence)):
            if risk.recommendation and risk.recommendation not in recommendations:
                recommendations.append(risk.recommendation)

            if len(recommendations) >= 10:  # Limit recommendations
                break

        # General recommendations
        if len(risks) > 5:
            recommendations.append(
                "Consider comprehensive legal review given the number of identified risks."
            )

        if not recommendations:
            recommendations.append(
                "No major risks identified, but still recommend legal review before execution."
            )

        return recommendations

    def compare_risk_profiles(
        self,
        document1_risks: List[LegalRisk],
        document2_risks: List[LegalRisk],
    ) -> Dict:
        """Compare risk profiles of two documents."""
        score1 = self._calculate_overall_risk_score(document1_risks)
        score2 = self._calculate_overall_risk_score(document2_risks)

        # Compare by category
        categories1 = {r.category for r in document1_risks}
        categories2 = {r.category for r in document2_risks}

        unique_to_1 = categories1 - categories2
        unique_to_2 = categories2 - categories1
        common = categories1 & categories2

        return {
            "score_difference": score2 - score1,
            "lower_risk_document": "document1" if score1 < score2 else "document2",
            "risk_categories_unique_to_doc1": list(unique_to_1),
            "risk_categories_unique_to_doc2": list(unique_to_2),
            "common_risk_categories": list(common),
            "recommendation": self._generate_comparison_recommendation(score1, score2),
        }

    def _generate_comparison_recommendation(self, score1: float, score2: float) -> str:
        """Generate recommendation from risk comparison."""
        diff = abs(score2 - score1)

        if diff < 1.0:
            return "Both documents have similar risk profiles."
        elif diff < 3.0:
            lower = "first" if score1 < score2 else "second"
            return f"The {lower} document has moderately lower risk."
        else:
            lower = "first" if score1 < score2 else "second"
            return f"The {lower} document has significantly lower risk and is recommended."
