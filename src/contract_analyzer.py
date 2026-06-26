"""
Contract analysis with NLP and clause extraction.
"""

import logging
import re
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import spacy
from spacy.matcher import Matcher
from collections import defaultdict

from src.models import (
    ContractParty,
    FinancialTerm,
    ExtractedClause,
    ClauseType,
    LegalRisk,
    RiskLevel,
)


logger = logging.getLogger(__name__)


class ContractAnalyzer:
    """Analyzes legal contracts using NLP and pattern matching."""

    def __init__(self, spacy_model: str = "en_core_web_sm"):
        """
        Initialize contract analyzer.

        Args:
            spacy_model: Name of spaCy model to use
        """
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            logger.warning(f"spaCy model {spacy_model} not found, downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", spacy_model])
            self.nlp = spacy.load(spacy_model)

        self.matcher = Matcher(self.nlp.vocab)
        self._setup_patterns()

        logger.info("ContractAnalyzer initialized")

    def _setup_patterns(self):
        """Set up spaCy patterns for entity recognition."""
        # Date patterns
        date_pattern = [
            {"SHAPE": "dd"},
            {"TEXT": {"IN": ["/", "-", "."]}},
            {"SHAPE": "dd"},
            {"TEXT": {"IN": ["/", "-", "."]}},
            {"SHAPE": "dddd"}
        ]
        self.matcher.add("DATE_PATTERN", [date_pattern])

        # Payment patterns
        payment_pattern = [
            {"ORTH": "$"},
            {"LIKE_NUM": True}
        ]
        self.matcher.add("PAYMENT_PATTERN", [payment_pattern])

        # Party patterns
        party_pattern = [
            {"LOWER": {"IN": ["party", "contractor", "client", "vendor", "employee"]}},
            {"IS_PUNCT": True, "OP": "?"},
            {"ENT_TYPE": "ORG", "OP": "+"}
        ]
        self.matcher.add("PARTY_PATTERN", [party_pattern])

    def analyze_contract(
        self,
        contract_text: str,
        extract_parties: bool = True,
        extract_dates: bool = True,
        extract_financial: bool = True,
        detect_risks: bool = True,
    ) -> Dict:
        """
        Analyze a contract and extract key information.

        Args:
            contract_text: Text of the contract
            extract_parties: Whether to extract party information
            extract_dates: Whether to extract important dates
            extract_financial: Whether to extract financial terms
            detect_risks: Whether to detect legal risks

        Returns:
            Dictionary with analysis results
        """
        logger.info("Starting contract analysis")
        start_time = datetime.now()

        # Process with spaCy
        doc = self.nlp(contract_text)

        results = {
            "document_hash": self._hash_content(contract_text),
            "word_count": len(doc),
            "sentence_count": len(list(doc.sents)),
        }

        if extract_parties:
            results["parties"] = self._extract_parties(doc, contract_text)

        if extract_dates:
            results["key_dates"] = self._extract_dates(doc, contract_text)

        if extract_financial:
            results["financial_terms"] = self._extract_financial_terms(doc, contract_text)

        if detect_risks:
            results["risks"] = self._detect_risks(contract_text, doc)

        # Extract contract summary
        results["summary"] = self._generate_summary(doc, contract_text)

        # Calculate overall risk score
        if detect_risks:
            results["overall_risk_score"] = self._calculate_risk_score(results.get("risks", []))
        else:
            results["overall_risk_score"] = 0.0

        processing_time = (datetime.now() - start_time).total_seconds()
        results["processing_time"] = processing_time

        logger.info(f"Contract analysis completed in {processing_time:.2f}s")
        return results

    def _hash_content(self, content: str) -> str:
        """Generate SHA-256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _extract_parties(self, doc, contract_text: str) -> List[ContractParty]:
        """Extract parties from contract."""
        parties = []
        seen_names = set()

        # Look for organizations
        for ent in doc.ents:
            if ent.label_ == "ORG" and ent.text not in seen_names:
                # Determine role based on context
                role = self._determine_party_role(ent, contract_text)
                parties.append(
                    ContractParty(
                        name=ent.text,
                        role=role,
                        contact_info=None
                    )
                )
                seen_names.add(ent.text)

        # Look for explicit party definitions
        party_patterns = [
            r'(?:party|contractor|client|vendor|employee)[\s:]+([A-Z][A-Za-z\s&,\.]+?)(?:\(|,|\.|hereinafter)',
            r'"([A-Z][A-Za-z\s&,\.]+?)"[\s]+\((?:hereinafter|the)\s+(?:referred to as|called)',
        ]

        for pattern in party_patterns:
            for match in re.finditer(pattern, contract_text, re.IGNORECASE):
                name = match.group(1).strip()
                if name and name not in seen_names and len(name) > 2:
                    role = self._determine_party_role_from_context(match, contract_text)
                    parties.append(
                        ContractParty(
                            name=name,
                            role=role,
                            contact_info=None
                        )
                    )
                    seen_names.add(name)

        logger.debug(f"Extracted {len(parties)} parties")
        return parties[:10]  # Limit to prevent false positives

    def _determine_party_role(self, entity, contract_text: str) -> str:
        """Determine the role of a party based on context."""
        text_around = contract_text[max(0, entity.start_char - 100):entity.end_char + 100].lower()

        if any(word in text_around for word in ["vendor", "supplier", "seller", "contractor"]):
            return "vendor"
        elif any(word in text_around for word in ["client", "buyer", "customer", "purchaser"]):
            return "client"
        elif any(word in text_around for word in ["employee", "worker"]):
            return "employee"
        elif any(word in text_around for word in ["employer", "company"]):
            return "employer"
        else:
            return "party"

    def _determine_party_role_from_context(self, match, contract_text: str) -> str:
        """Determine party role from regex match context."""
        start = max(0, match.start() - 50)
        end = min(len(contract_text), match.end() + 50)
        context = contract_text[start:end].lower()

        if any(word in context for word in ["vendor", "seller"]):
            return "vendor"
        elif any(word in context for word in ["client", "buyer"]):
            return "client"
        else:
            return "party"

    def _extract_dates(self, doc, contract_text: str) -> Dict[str, str]:
        """Extract important dates from contract."""
        dates = {}

        # Date patterns
        date_patterns = [
            r'(?:effective date|start date|commencement date)[\s:]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:termination date|end date|expiration date)[\s:]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'dated[\s:]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})(?=.*(?:execution|signing))',
        ]

        for pattern in date_patterns:
            matches = re.finditer(pattern, contract_text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                # Determine date type from context
                context = contract_text[max(0, match.start() - 30):match.start()].lower()
                if "effective" in context or "start" in context or "commencement" in context:
                    dates["effective_date"] = date_str
                elif "termination" in context or "end" in context or "expiration" in context:
                    dates["termination_date"] = date_str
                elif "dated" in context or "execution" in context or "signing" in context:
                    dates["execution_date"] = date_str

        # Also extract dates using spaCy
        for ent in doc.ents:
            if ent.label_ == "DATE":
                # Store first few dates found
                if "document_date" not in dates:
                    dates["document_date"] = ent.text

        logger.debug(f"Extracted {len(dates)} dates")
        return dates

    def _extract_financial_terms(self, doc, contract_text: str) -> List[FinancialTerm]:
        """Extract financial terms from contract."""
        financial_terms = []

        # Money patterns
        money_patterns = [
            r'\$\s?([\d,]+(?:\.\d{2})?)',
            r'([\d,]+(?:\.\d{2})?)\s+(?:dollars|USD|EUR|GBP)',
            r'(?:sum of|amount of|payment of)\s+\$?\s?([\d,]+(?:\.\d{2})?)',
        ]

        for pattern in money_patterns:
            for match in re.finditer(pattern, contract_text, re.IGNORECASE):
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount = float(amount_str)

                    # Get context for description
                    start = max(0, match.start() - 100)
                    end = min(len(contract_text), match.end() + 100)
                    context = contract_text[start:end]

                    # Determine frequency
                    frequency = None
                    if re.search(r'\b(?:monthly|per month)\b', context, re.IGNORECASE):
                        frequency = "monthly"
                    elif re.search(r'\b(?:annually|per year|yearly)\b', context, re.IGNORECASE):
                        frequency = "annually"
                    elif re.search(r'\b(?:quarterly|per quarter)\b', context, re.IGNORECASE):
                        frequency = "quarterly"

                    # Extract description
                    description = self._extract_financial_description(context, match)

                    financial_terms.append(
                        FinancialTerm(
                            amount=amount,
                            currency="USD",
                            frequency=frequency,
                            description=description,
                            conditions=None
                        )
                    )
                except (ValueError, IndexError):
                    continue

        logger.debug(f"Extracted {len(financial_terms)} financial terms")
        return financial_terms[:10]  # Limit to prevent duplicates

    def _extract_financial_description(self, context: str, match) -> str:
        """Extract description for financial term."""
        # Get the sentence containing the amount
        sentences = context.split('.')
        for sent in sentences:
            if match.group(0) in sent:
                return sent.strip()[:200]  # Limit length
        return "Payment term"

    def _detect_risks(self, contract_text: str, doc) -> List[LegalRisk]:
        """Detect potential legal risks in contract."""
        risks = []
        risk_id_counter = 0

        # Risk patterns
        risk_indicators = {
            "liability": {
                "patterns": [
                    r'unlimited\s+liability',
                    r'no\s+(?:limitation|cap)\s+(?:of|on)\s+liability',
                    r'indemnif(?:y|ication).*(?:any|all)\s+(?:claims|damages)',
                ],
                "level": RiskLevel.HIGH,
                "category": "Liability"
            },
            "termination": {
                "patterns": [
                    r'terminat(?:e|ion)\s+(?:at\s+will|without\s+cause)',
                    r'no\s+notice.*terminat(?:e|ion)',
                ],
                "level": RiskLevel.MEDIUM,
                "category": "Termination"
            },
            "ip_assignment": {
                "patterns": [
                    r'(?:all|any)\s+intellectual\s+property.*(?:assigned|belongs)',
                    r'work\s+for\s+hire',
                ],
                "level": RiskLevel.MEDIUM,
                "category": "Intellectual Property"
            },
            "confidentiality": {
                "patterns": [
                    r'perpetual.*confidentiality',
                    r'confidential(?:ity)?.*indefinite',
                ],
                "level": RiskLevel.LOW,
                "category": "Confidentiality"
            },
            "payment": {
                "patterns": [
                    r'payment.*(?:discretion|sole\s+discretion)',
                    r'no\s+refund',
                ],
                "level": RiskLevel.MEDIUM,
                "category": "Payment"
            },
            "arbitration": {
                "patterns": [
                    r'binding\s+arbitration',
                    r'waive.*(?:jury\s+trial|class\s+action)',
                ],
                "level": RiskLevel.MEDIUM,
                "category": "Dispute Resolution"
            },
        }

        for risk_type, risk_data in risk_indicators.items():
            for pattern in risk_data["patterns"]:
                matches = list(re.finditer(pattern, contract_text, re.IGNORECASE))
                for match in matches:
                    risk_id_counter += 1
                    affected_clause = contract_text[
                        max(0, match.start() - 50):min(len(contract_text), match.end() + 50)
                    ]

                    risks.append(
                        LegalRisk(
                            risk_id=f"RISK_{risk_id_counter:03d}",
                            risk_level=risk_data["level"],
                            category=risk_data["category"],
                            description=self._generate_risk_description(risk_type, match.group(0)),
                            affected_clause=affected_clause,
                            recommendation=self._generate_risk_recommendation(risk_type),
                            confidence=0.75
                        )
                    )

        # Check for missing clauses (absence risks)
        missing_clause_risks = self._check_missing_clauses(contract_text)
        risks.extend(missing_clause_risks)

        logger.debug(f"Detected {len(risks)} potential risks")
        return risks

    def _generate_risk_description(self, risk_type: str, matched_text: str) -> str:
        """Generate description for detected risk."""
        descriptions = {
            "liability": f"Potentially unfavorable liability terms detected: '{matched_text}'. This may expose your organization to unlimited financial risk.",
            "termination": f"Termination clause detected: '{matched_text}'. This may allow the other party to terminate without adequate notice.",
            "ip_assignment": f"Intellectual property assignment clause detected: '{matched_text}'. Verify if this aligns with your IP strategy.",
            "confidentiality": f"Perpetual confidentiality obligation detected: '{matched_text}'. Consider negotiating a time limit.",
            "payment": f"Payment term detected: '{matched_text}'. This may create uncertainty around payment obligations.",
            "arbitration": f"Dispute resolution clause detected: '{matched_text}'. This may limit your legal options.",
        }
        return descriptions.get(risk_type, f"Potential risk detected: {matched_text}")

    def _generate_risk_recommendation(self, risk_type: str) -> str:
        """Generate recommendation for detected risk."""
        recommendations = {
            "liability": "Consider negotiating a liability cap or limitations on liability exposure.",
            "termination": "Negotiate for reasonable notice periods and termination for cause only.",
            "ip_assignment": "Clarify which IP is covered and consider retaining rights to pre-existing IP.",
            "confidentiality": "Negotiate a reasonable time limit (e.g., 3-5 years) for confidentiality obligations.",
            "payment": "Clarify payment terms and ensure they are objective and measurable.",
            "arbitration": "Consider the implications of binding arbitration and class action waivers.",
        }
        return recommendations.get(risk_type, "Review this clause with legal counsel.")

    def _check_missing_clauses(self, contract_text: str) -> List[LegalRisk]:
        """Check for important missing clauses."""
        risks = []
        text_lower = contract_text.lower()

        missing_clauses = []

        if "force majeure" not in text_lower:
            missing_clauses.append(("Force Majeure", "Consider adding a force majeure clause to protect against unforeseen circumstances."))

        if "warranty" not in text_lower and "represent" not in text_lower:
            missing_clauses.append(("Warranties", "Consider adding warranty provisions to clarify representations and guarantees."))

        if "governing law" not in text_lower and "jurisdiction" not in text_lower:
            missing_clauses.append(("Governing Law", "Add a governing law clause to specify which jurisdiction's laws apply."))

        for idx, (clause_name, recommendation) in enumerate(missing_clauses):
            risks.append(
                LegalRisk(
                    risk_id=f"MISSING_{idx + 1:03d}",
                    risk_level=RiskLevel.LOW,
                    category="Missing Clause",
                    description=f"The contract appears to lack a {clause_name} clause.",
                    affected_clause=None,
                    recommendation=recommendation,
                    confidence=0.6
                )
            )

        return risks

    def _generate_summary(self, doc, contract_text: str) -> str:
        """Generate a summary of the contract."""
        # Extract first few sentences as summary
        sentences = list(doc.sents)
        if len(sentences) < 3:
            return contract_text[:500]

        # Try to find a summary section or introduction
        summary_patterns = [
            r'(?:whereas|recitals?|background).*?(?=\n\n|\Z)',
            r'(?:this\s+agreement|this\s+contract).*?(?:\.|$)',
        ]

        for pattern in summary_patterns:
            match = re.search(pattern, contract_text, re.IGNORECASE | re.DOTALL)
            if match:
                summary = match.group(0)[:500]
                return summary

        # Fallback: first 3 sentences
        summary = ' '.join([sent.text for sent in sentences[:3]])
        return summary[:500]

    def _calculate_risk_score(self, risks: List[LegalRisk]) -> float:
        """
        Calculate overall risk score based on detected risks.

        Args:
            risks: List of detected risks

        Returns:
            Risk score from 0.0 (low risk) to 10.0 (high risk)
        """
        if not risks:
            return 0.0

        risk_weights = {
            RiskLevel.CRITICAL: 4.0,
            RiskLevel.HIGH: 3.0,
            RiskLevel.MEDIUM: 2.0,
            RiskLevel.LOW: 1.0,
            RiskLevel.INFO: 0.5,
        }

        total_weight = sum(risk_weights.get(risk.risk_level, 1.0) * risk.confidence for risk in risks)
        max_possible = len(risks) * 4.0  # Maximum if all were critical with confidence 1.0

        # Normalize to 0-10 scale
        if max_possible > 0:
            score = (total_weight / max_possible) * 10.0
            return min(10.0, score)

        return 0.0
