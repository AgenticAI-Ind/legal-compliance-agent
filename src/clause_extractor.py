"""
ML-based clause extraction and classification from contracts.
"""

import logging
import re
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from src.models import ExtractedClause, ClauseType


logger = logging.getLogger(__name__)


class ClauseExtractor:
    """Extracts and classifies clauses from legal contracts."""

    def __init__(self):
        """Initialize clause extractor."""
        self.clause_patterns = self._build_clause_patterns()
        logger.info("ClauseExtractor initialized")

    def _build_clause_patterns(self) -> Dict[ClauseType, List[Dict]]:
        """Build regex patterns for each clause type."""
        return {
            ClauseType.CONFIDENTIALITY: [
                {
                    "pattern": r'(?:confidential(?:ity)?|non-disclosure|proprietary\s+information).*?(?:\.|;|\n\n)',
                    "keywords": ["confidential", "proprietary", "secret", "disclose"],
                },
            ],
            ClauseType.TERMINATION: [
                {
                    "pattern": r'(?:terminat(?:e|ion)|cancellation|expir(?:e|ation)).*?(?:\.|;|\n\n)',
                    "keywords": ["terminate", "cancel", "expire", "end", "notice"],
                },
            ],
            ClauseType.PAYMENT: [
                {
                    "pattern": r'(?:payment|compensation|fee|price|remuneration).*?(?:\.|;|\n\n)',
                    "keywords": ["payment", "pay", "fee", "price", "compensation", "$"],
                },
            ],
            ClauseType.LIABILITY: [
                {
                    "pattern": r'(?:liabilit(?:y|ies)|limitation\s+of\s+liability|damages).*?(?:\.|;|\n\n)',
                    "keywords": ["liability", "liable", "damages", "limitation", "cap"],
                },
            ],
            ClauseType.INDEMNIFICATION: [
                {
                    "pattern": r'(?:indemnif(?:y|ication)|hold\s+harmless|defend).*?(?:\.|;|\n\n)',
                    "keywords": ["indemnify", "hold harmless", "defend", "reimburse"],
                },
            ],
            ClauseType.INTELLECTUAL_PROPERTY: [
                {
                    "pattern": r'(?:intellectual\s+property|copyright|patent|trademark|trade\s+secret|ip\s+rights).*?(?:\.|;|\n\n)',
                    "keywords": ["intellectual property", "copyright", "patent", "trademark", "ip"],
                },
            ],
            ClauseType.GOVERNING_LAW: [
                {
                    "pattern": r'(?:governing\s+law|choice\s+of\s+law|jurisdiction|venue).*?(?:\.|;|\n\n)',
                    "keywords": ["governing law", "jurisdiction", "laws of", "courts of"],
                },
            ],
            ClauseType.DISPUTE_RESOLUTION: [
                {
                    "pattern": r'(?:dispute\s+resolution|arbitration|mediation|litigation).*?(?:\.|;|\n\n)',
                    "keywords": ["arbitration", "mediation", "dispute", "resolution", "litigation"],
                },
            ],
            ClauseType.WARRANTY: [
                {
                    "pattern": r'(?:warrant(?:y|ies)|representation|guarantee).*?(?:\.|;|\n\n)',
                    "keywords": ["warranty", "warrant", "represent", "guarantee"],
                },
            ],
            ClauseType.FORCE_MAJEURE: [
                {
                    "pattern": r'(?:force\s+majeure|act\s+of\s+god|unavoidable\s+circumstance).*?(?:\.|;|\n\n)',
                    "keywords": ["force majeure", "act of god", "unforeseeable", "beyond control"],
                },
            ],
            ClauseType.NON_COMPETE: [
                {
                    "pattern": r'(?:non-compete|non-competition|covenant\s+not\s+to\s+compete).*?(?:\.|;|\n\n)',
                    "keywords": ["non-compete", "compete", "competing business", "competitive"],
                },
            ],
            ClauseType.DATA_PROTECTION: [
                {
                    "pattern": r'(?:data\s+protection|privacy|personal\s+(?:data|information)|gdpr|hipaa).*?(?:\.|;|\n\n)',
                    "keywords": ["data protection", "privacy", "personal data", "gdpr", "hipaa"],
                },
            ],
        }

    def extract_clauses(
        self,
        contract_text: str,
        clause_types: Optional[List[ClauseType]] = None,
        min_confidence: float = 0.6,
    ) -> Dict:
        """
        Extract clauses from contract text.

        Args:
            contract_text: Text of the contract
            clause_types: Specific clause types to extract (None = all types)
            min_confidence: Minimum confidence threshold

        Returns:
            Dictionary with extracted clauses and metadata
        """
        logger.info("Starting clause extraction")
        start_time = datetime.now()

        # Determine which clause types to extract
        types_to_extract = clause_types if clause_types else list(ClauseType)

        extracted_clauses = []
        seen_texts = set()  # To avoid duplicates

        # Extract each clause type
        for clause_type in types_to_extract:
            if clause_type not in self.clause_patterns:
                logger.warning(f"No patterns defined for clause type: {clause_type}")
                continue

            clauses = self._extract_clause_type(
                contract_text,
                clause_type,
                min_confidence
            )

            # Filter duplicates
            for clause in clauses:
                clause_text_normalized = clause.text.strip().lower()
                if clause_text_normalized not in seen_texts:
                    extracted_clauses.append(clause)
                    seen_texts.add(clause_text_normalized)

        # Sort by position in document
        extracted_clauses.sort(key=lambda c: c.start_position)

        # Calculate coverage
        total_length = len(contract_text)
        covered_length = sum(
            clause.end_position - clause.start_position
            for clause in extracted_clauses
        )
        coverage_percentage = (covered_length / total_length * 100) if total_length > 0 else 0.0

        processing_time = (datetime.now() - start_time).total_seconds()

        logger.info(
            f"Extracted {len(extracted_clauses)} clauses in {processing_time:.2f}s. "
            f"Coverage: {coverage_percentage:.1f}%"
        )

        return {
            "extracted_clauses": extracted_clauses,
            "total_clauses": len(extracted_clauses),
            "coverage_percentage": coverage_percentage,
            "processing_time": processing_time,
        }

    def _extract_clause_type(
        self,
        contract_text: str,
        clause_type: ClauseType,
        min_confidence: float,
    ) -> List[ExtractedClause]:
        """Extract clauses of a specific type."""
        clauses = []
        patterns = self.clause_patterns[clause_type]

        for pattern_dict in patterns:
            pattern = pattern_dict["pattern"]
            keywords = pattern_dict["keywords"]

            # Find all matches
            for match in re.finditer(pattern, contract_text, re.IGNORECASE | re.DOTALL):
                clause_text = match.group(0)

                # Expand to full sentence/paragraph if needed
                expanded_text, start_pos, end_pos = self._expand_to_clause(
                    contract_text,
                    match.start(),
                    match.end()
                )

                # Calculate confidence
                confidence = self._calculate_confidence(
                    expanded_text,
                    clause_type,
                    keywords
                )

                if confidence >= min_confidence:
                    # Extract key terms
                    key_terms = self._extract_key_terms(expanded_text, keywords)

                    # Identify risks
                    risks = self._identify_clause_risks(expanded_text, clause_type)

                    clause = ExtractedClause(
                        clause_type=clause_type,
                        text=expanded_text,
                        confidence=confidence,
                        start_position=start_pos,
                        end_position=end_pos,
                        key_terms=key_terms,
                        risks=risks,
                    )
                    clauses.append(clause)

        logger.debug(f"Found {len(clauses)} {clause_type.value} clauses")
        return clauses

    def _expand_to_clause(
        self,
        text: str,
        start: int,
        end: int
    ) -> tuple[str, int, int]:
        """
        Expand match to include full clause/paragraph.

        Returns:
            Tuple of (expanded_text, new_start, new_end)
        """
        # Find the start of the clause (beginning of paragraph or sentence)
        new_start = start
        while new_start > 0 and text[new_start - 1] not in ['\n', '.', ';']:
            new_start -= 1
            if start - new_start > 200:  # Limit backward expansion
                break

        # Find the end of the clause
        new_end = end
        while new_end < len(text) and text[new_end] not in ['\n\n', '.', ';']:
            new_end += 1
            if new_end - end > 500:  # Limit forward expansion
                break

        # Include the ending punctuation
        if new_end < len(text):
            new_end += 1

        expanded_text = text[new_start:new_end].strip()
        return expanded_text, new_start, new_end

    def _calculate_confidence(
        self,
        clause_text: str,
        clause_type: ClauseType,
        keywords: List[str]
    ) -> float:
        """Calculate confidence score for extracted clause."""
        text_lower = clause_text.lower()

        # Base confidence
        confidence = 0.5

        # Count keyword matches
        keyword_matches = sum(
            1 for keyword in keywords
            if keyword.lower() in text_lower
        )

        # Increase confidence based on keyword density
        keyword_bonus = min(0.3, keyword_matches * 0.1)
        confidence += keyword_bonus

        # Check for section headers
        header_patterns = [
            rf'\b{clause_type.value.replace("_", " ")}\b',
            r'^\s*\d+\.\s*',
            r'^[A-Z\s]+:',
        ]
        for pattern in header_patterns:
            if re.search(pattern, clause_text[:100], re.IGNORECASE):
                confidence += 0.1
                break

        # Penalize if text is too short
        if len(clause_text) < 50:
            confidence *= 0.8

        # Penalize if text is too long (might be multiple clauses)
        if len(clause_text) > 2000:
            confidence *= 0.9

        # Ensure confidence is in valid range
        return max(0.0, min(1.0, confidence))

    def _extract_key_terms(self, clause_text: str, keywords: List[str]) -> List[str]:
        """Extract key terms from clause text."""
        key_terms = []
        text_lower = clause_text.lower()

        # Add matched keywords
        for keyword in keywords:
            if keyword.lower() in text_lower:
                key_terms.append(keyword)

        # Extract quoted terms
        quoted_terms = re.findall(r'"([^"]+)"', clause_text)
        key_terms.extend(quoted_terms[:5])  # Limit to prevent noise

        # Extract capitalized terms (potential defined terms)
        capitalized = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', clause_text)
        key_terms.extend(list(set(capitalized))[:5])

        # Remove duplicates and limit
        key_terms = list(set(key_terms))[:10]

        return key_terms

    def _identify_clause_risks(self, clause_text: str, clause_type: ClauseType) -> List[str]:
        """Identify potential risks in the clause."""
        risks = []
        text_lower = clause_text.lower()

        # Risk patterns by clause type
        risk_patterns = {
            ClauseType.LIABILITY: [
                (r'unlimited', "Unlimited liability exposure"),
                (r'no\s+(?:cap|limit)', "No liability cap"),
                (r'consequential\s+damages', "Consequential damages included"),
            ],
            ClauseType.TERMINATION: [
                (r'without\s+(?:cause|notice)', "Termination without cause"),
                (r'immediate(?:ly)?.*terminat', "Immediate termination possible"),
                (r'at\s+(?:will|any\s+time)', "At-will termination"),
            ],
            ClauseType.CONFIDENTIALITY: [
                (r'perpetual', "Perpetual confidentiality obligation"),
                (r'indefinite', "Indefinite confidentiality period"),
            ],
            ClauseType.INTELLECTUAL_PROPERTY: [
                (r'all\s+(?:ip|intellectual\s+property|rights)', "Broad IP assignment"),
                (r'work\s+for\s+hire', "Work for hire provision"),
            ],
            ClauseType.PAYMENT: [
                (r'sole\s+discretion', "Payment at sole discretion"),
                (r'non-refundable', "Non-refundable payment"),
            ],
            ClauseType.DISPUTE_RESOLUTION: [
                (r'binding\s+arbitration', "Mandatory binding arbitration"),
                (r'waive.*class\s+action', "Class action waiver"),
                (r'waive.*jury', "Jury trial waiver"),
            ],
            ClauseType.NON_COMPETE: [
                (r'indefinite', "Indefinite non-compete period"),
                (r'geographic(?:al)?\s+(?:area|scope).*worldwide', "Worldwide geographic scope"),
            ],
        }

        if clause_type in risk_patterns:
            for pattern, risk_description in risk_patterns[clause_type]:
                if re.search(pattern, text_lower):
                    risks.append(risk_description)

        return risks

    def classify_clause(self, clause_text: str) -> Dict[ClauseType, float]:
        """
        Classify a clause into potential clause types with confidence scores.

        Args:
            clause_text: Text of the clause to classify

        Returns:
            Dictionary mapping clause types to confidence scores
        """
        scores = {}

        for clause_type in ClauseType:
            if clause_type not in self.clause_patterns:
                continue

            patterns = self.clause_patterns[clause_type]
            max_confidence = 0.0

            for pattern_dict in patterns:
                keywords = pattern_dict["keywords"]
                confidence = self._calculate_confidence(
                    clause_text,
                    clause_type,
                    keywords
                )
                max_confidence = max(max_confidence, confidence)

            if max_confidence > 0.3:  # Only include plausible classifications
                scores[clause_type] = max_confidence

        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))

    def compare_clauses(
        self,
        clause1: ExtractedClause,
        clause2: ExtractedClause
    ) -> Dict:
        """
        Compare two clauses and identify differences.

        Args:
            clause1: First clause
            clause2: Second clause

        Returns:
            Dictionary with comparison results
        """
        comparison = {
            "same_type": clause1.clause_type == clause2.clause_type,
            "text_similarity": self._calculate_text_similarity(clause1.text, clause2.text),
            "key_differences": [],
            "risk_differences": [],
        }

        # Compare key terms
        terms1 = set(clause1.key_terms)
        terms2 = set(clause2.key_terms)
        unique_to_1 = terms1 - terms2
        unique_to_2 = terms2 - terms1

        if unique_to_1:
            comparison["key_differences"].append(
                f"Clause 1 unique terms: {', '.join(unique_to_1)}"
            )
        if unique_to_2:
            comparison["key_differences"].append(
                f"Clause 2 unique terms: {', '.join(unique_to_2)}"
            )

        # Compare risks
        risks1 = set(clause1.risks)
        risks2 = set(clause2.risks)
        unique_risks_1 = risks1 - risks2
        unique_risks_2 = risks2 - risks1

        if unique_risks_1:
            comparison["risk_differences"].append(
                f"Clause 1 unique risks: {', '.join(unique_risks_1)}"
            )
        if unique_risks_2:
            comparison["risk_differences"].append(
                f"Clause 2 unique risks: {', '.join(unique_risks_2)}"
            )

        return comparison

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity score."""
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0
