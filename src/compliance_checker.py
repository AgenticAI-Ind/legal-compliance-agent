"""
Regulatory compliance checking for GDPR, HIPAA, SOC2, and other frameworks.
"""

import logging
import re
from typing import Dict, List, Tuple
from datetime import datetime
import uuid

from src.models import (
    ComplianceFramework,
    ComplianceIssue,
    RiskLevel,
    DocumentType,
)


logger = logging.getLogger(__name__)


class ComplianceChecker:
    """Checks documents for regulatory compliance."""

    def __init__(self):
        """Initialize compliance checker."""
        self.compliance_rules = self._load_compliance_rules()
        logger.info("ComplianceChecker initialized")

    def _load_compliance_rules(self) -> Dict[ComplianceFramework, Dict]:
        """Load compliance rules for each framework."""
        return {
            ComplianceFramework.GDPR: self._get_gdpr_rules(),
            ComplianceFramework.HIPAA: self._get_hipaa_rules(),
            ComplianceFramework.SOC2: self._get_soc2_rules(),
            ComplianceFramework.CCPA: self._get_ccpa_rules(),
            ComplianceFramework.PCI_DSS: self._get_pci_dss_rules(),
            ComplianceFramework.ISO27001: self._get_iso27001_rules(),
        }

    def _get_gdpr_rules(self) -> Dict:
        """Get GDPR compliance rules."""
        return {
            "name": "General Data Protection Regulation",
            "requirements": [
                {
                    "id": "GDPR-1",
                    "name": "Lawful Basis for Processing",
                    "description": "Must specify lawful basis for data processing",
                    "keywords": ["consent", "legitimate interest", "legal obligation", "contract"],
                    "severity": RiskLevel.HIGH,
                    "article": "Article 6",
                },
                {
                    "id": "GDPR-2",
                    "name": "Data Subject Rights",
                    "description": "Must inform users of their rights (access, rectification, erasure, portability)",
                    "keywords": ["right to access", "right to erasure", "right to portability", "right to rectification"],
                    "severity": RiskLevel.HIGH,
                    "article": "Articles 15-20",
                },
                {
                    "id": "GDPR-3",
                    "name": "Purpose Limitation",
                    "description": "Must specify purpose of data collection",
                    "keywords": ["purpose", "collected for", "used for", "process.*for"],
                    "severity": RiskLevel.MEDIUM,
                    "article": "Article 5(1)(b)",
                },
                {
                    "id": "GDPR-4",
                    "name": "Data Retention",
                    "description": "Must specify data retention periods",
                    "keywords": ["retention", "delete", "remove", "keep.*data", "store.*data"],
                    "severity": RiskLevel.MEDIUM,
                    "article": "Article 5(1)(e)",
                },
                {
                    "id": "GDPR-5",
                    "name": "Third-Party Data Sharing",
                    "description": "Must disclose data sharing with third parties",
                    "keywords": ["third party", "share.*data", "disclose", "transfer"],
                    "severity": RiskLevel.HIGH,
                    "article": "Article 13(1)(e)",
                },
                {
                    "id": "GDPR-6",
                    "name": "Data Protection Officer",
                    "description": "Must provide DPO contact information (if applicable)",
                    "keywords": ["data protection officer", "dpo", "privacy officer"],
                    "severity": RiskLevel.MEDIUM,
                    "article": "Articles 37-39",
                },
                {
                    "id": "GDPR-7",
                    "name": "International Data Transfers",
                    "description": "Must address international data transfers",
                    "keywords": ["transfer.*outside", "international transfer", "third country"],
                    "severity": RiskLevel.HIGH,
                    "article": "Chapter V",
                },
                {
                    "id": "GDPR-8",
                    "name": "Automated Decision Making",
                    "description": "Must disclose automated decision-making and profiling",
                    "keywords": ["automated", "profiling", "algorithmic"],
                    "severity": RiskLevel.MEDIUM,
                    "article": "Article 22",
                },
            ]
        }

    def _get_hipaa_rules(self) -> Dict:
        """Get HIPAA compliance rules."""
        return {
            "name": "Health Insurance Portability and Accountability Act",
            "requirements": [
                {
                    "id": "HIPAA-1",
                    "name": "Protected Health Information (PHI)",
                    "description": "Must specify handling of PHI",
                    "keywords": ["protected health information", "phi", "medical records", "health data"],
                    "severity": RiskLevel.CRITICAL,
                    "article": "45 CFR 160.103",
                },
                {
                    "id": "HIPAA-2",
                    "name": "Privacy Rule Compliance",
                    "description": "Must comply with HIPAA Privacy Rule",
                    "keywords": ["hipaa", "privacy rule", "minimum necessary"],
                    "severity": RiskLevel.HIGH,
                    "article": "45 CFR Part 160 and Part 164",
                },
                {
                    "id": "HIPAA-3",
                    "name": "Security Safeguards",
                    "description": "Must implement administrative, physical, and technical safeguards",
                    "keywords": ["encryption", "access control", "audit", "security"],
                    "severity": RiskLevel.HIGH,
                    "article": "45 CFR 164.308-312",
                },
                {
                    "id": "HIPAA-4",
                    "name": "Breach Notification",
                    "description": "Must have breach notification procedures",
                    "keywords": ["breach", "notification", "incident"],
                    "severity": RiskLevel.HIGH,
                    "article": "45 CFR 164.400-414",
                },
                {
                    "id": "HIPAA-5",
                    "name": "Business Associate Agreement",
                    "description": "Must have BAA with service providers handling PHI",
                    "keywords": ["business associate", "baa", "subcontractor"],
                    "severity": RiskLevel.CRITICAL,
                    "article": "45 CFR 164.502(e)",
                },
                {
                    "id": "HIPAA-6",
                    "name": "Patient Rights",
                    "description": "Must inform patients of their rights",
                    "keywords": ["patient rights", "access.*records", "amend"],
                    "severity": RiskLevel.MEDIUM,
                    "article": "45 CFR 164.520",
                },
            ]
        }

    def _get_soc2_rules(self) -> Dict:
        """Get SOC2 compliance rules."""
        return {
            "name": "Service Organization Control 2",
            "requirements": [
                {
                    "id": "SOC2-1",
                    "name": "Security Principle",
                    "description": "Must address system security",
                    "keywords": ["security", "protect", "safeguard", "secure"],
                    "severity": RiskLevel.HIGH,
                    "article": "TSC CC6",
                },
                {
                    "id": "SOC2-2",
                    "name": "Availability Principle",
                    "description": "Must address system availability",
                    "keywords": ["availability", "uptime", "accessible", "operational"],
                    "severity": RiskLevel.MEDIUM,
                    "article": "TSC A1",
                },
                {
                    "id": "SOC2-3",
                    "name": "Confidentiality Principle",
                    "description": "Must protect confidential information",
                    "keywords": ["confidential", "proprietary", "secret"],
                    "severity": RiskLevel.HIGH,
                    "article": "TSC C1",
                },
                {
                    "id": "SOC2-4",
                    "name": "Processing Integrity",
                    "description": "Must ensure system processing is complete, accurate, and timely",
                    "keywords": ["accuracy", "complete", "valid", "authorized"],
                    "severity": RiskLevel.MEDIUM,
                    "article": "TSC PI1",
                },
                {
                    "id": "SOC2-5",
                    "name": "Privacy Principle",
                    "description": "Must address personal information privacy",
                    "keywords": ["privacy", "personal information", "data protection"],
                    "severity": RiskLevel.HIGH,
                    "article": "TSC P1-P8",
                },
                {
                    "id": "SOC2-6",
                    "name": "Access Controls",
                    "description": "Must implement proper access controls",
                    "keywords": ["access control", "authentication", "authorization"],
                    "severity": RiskLevel.HIGH,
                    "article": "TSC CC6.1-CC6.3",
                },
            ]
        }

    def _get_ccpa_rules(self) -> Dict:
        """Get CCPA compliance rules."""
        return {
            "name": "California Consumer Privacy Act",
            "requirements": [
                {
                    "id": "CCPA-1",
                    "name": "Right to Know",
                    "description": "Must inform consumers about data collection",
                    "keywords": ["collect", "categories.*information", "source"],
                    "severity": RiskLevel.HIGH,
                    "article": "Section 1798.100",
                },
                {
                    "id": "CCPA-2",
                    "name": "Right to Delete",
                    "description": "Must provide right to delete personal information",
                    "keywords": ["delete", "remove", "erase"],
                    "severity": RiskLevel.HIGH,
                    "article": "Section 1798.105",
                },
                {
                    "id": "CCPA-3",
                    "name": "Right to Opt-Out",
                    "description": "Must provide opt-out of sale of personal information",
                    "keywords": ["opt.?out", "do not sell", "sale.*information"],
                    "severity": RiskLevel.HIGH,
                    "article": "Section 1798.120",
                },
                {
                    "id": "CCPA-4",
                    "name": "Non-Discrimination",
                    "description": "Must not discriminate against consumers exercising their rights",
                    "keywords": ["discriminate", "deny.*service", "different price"],
                    "severity": RiskLevel.MEDIUM,
                    "article": "Section 1798.125",
                },
            ]
        }

    def _get_pci_dss_rules(self) -> Dict:
        """Get PCI DSS compliance rules."""
        return {
            "name": "Payment Card Industry Data Security Standard",
            "requirements": [
                {
                    "id": "PCI-1",
                    "name": "Cardholder Data Protection",
                    "description": "Must protect cardholder data",
                    "keywords": ["card.*data", "payment.*information", "credit card"],
                    "severity": RiskLevel.CRITICAL,
                    "article": "Requirement 3",
                },
                {
                    "id": "PCI-2",
                    "name": "Encryption",
                    "description": "Must encrypt transmission of cardholder data",
                    "keywords": ["encrypt", "ssl", "tls", "secure.*transmission"],
                    "severity": RiskLevel.CRITICAL,
                    "article": "Requirement 4",
                },
                {
                    "id": "PCI-3",
                    "name": "Access Control",
                    "description": "Must restrict access to cardholder data",
                    "keywords": ["access control", "restrict.*access", "need.?to.?know"],
                    "severity": RiskLevel.HIGH,
                    "article": "Requirement 7",
                },
            ]
        }

    def _get_iso27001_rules(self) -> Dict:
        """Get ISO 27001 compliance rules."""
        return {
            "name": "ISO/IEC 27001 Information Security Management",
            "requirements": [
                {
                    "id": "ISO-1",
                    "name": "Information Security Policy",
                    "description": "Must have information security policies",
                    "keywords": ["information security", "security policy"],
                    "severity": RiskLevel.HIGH,
                    "article": "A.5.1",
                },
                {
                    "id": "ISO-2",
                    "name": "Asset Management",
                    "description": "Must manage information assets",
                    "keywords": ["asset", "inventory", "ownership"],
                    "severity": RiskLevel.MEDIUM,
                    "article": "A.8",
                },
                {
                    "id": "ISO-3",
                    "name": "Access Control",
                    "description": "Must control access to information",
                    "keywords": ["access control", "authentication", "authorization"],
                    "severity": RiskLevel.HIGH,
                    "article": "A.9",
                },
            ]
        }

    def check_compliance(
        self,
        document_text: str,
        frameworks: List[ComplianceFramework],
        document_type: DocumentType = DocumentType.OTHER,
        detailed_analysis: bool = True,
    ) -> Dict:
        """
        Check document for compliance with specified frameworks.

        Args:
            document_text: Text to check
            frameworks: List of compliance frameworks to check against
            document_type: Type of document being checked
            detailed_analysis: Whether to include detailed analysis

        Returns:
            Dictionary with compliance results
        """
        logger.info(f"Checking compliance for {len(frameworks)} frameworks")
        start_time = datetime.now()

        results = {
            "frameworks_checked": frameworks,
            "issues": [],
            "compliant_requirements": [],
            "recommendations": [],
        }

        text_lower = document_text.lower()

        for framework in frameworks:
            if framework not in self.compliance_rules:
                logger.warning(f"Unknown framework: {framework}")
                continue

            framework_rules = self.compliance_rules[framework]
            logger.debug(f"Checking {framework_rules['name']}")

            for requirement in framework_rules["requirements"]:
                issue = self._check_requirement(
                    document_text,
                    text_lower,
                    requirement,
                    framework,
                    detailed_analysis
                )

                if issue:
                    results["issues"].append(issue)
                else:
                    results["compliant_requirements"].append(
                        f"{requirement['id']}: {requirement['name']}"
                    )

        # Calculate overall compliance score
        total_requirements = sum(
            len(self.compliance_rules[fw]["requirements"])
            for fw in frameworks
            if fw in self.compliance_rules
        )

        if total_requirements > 0:
            compliant_count = len(results["compliant_requirements"])
            results["overall_compliance_score"] = (compliant_count / total_requirements) * 100
        else:
            results["overall_compliance_score"] = 0.0

        # Generate summary
        results["summary"] = self._generate_compliance_summary(results, frameworks)

        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(results)

        processing_time = (datetime.now() - start_time).total_seconds()
        results["processing_time"] = processing_time

        logger.info(
            f"Compliance check completed in {processing_time:.2f}s. "
            f"Score: {results['overall_compliance_score']:.1f}%"
        )

        return results

    def _check_requirement(
        self,
        document_text: str,
        text_lower: str,
        requirement: Dict,
        framework: ComplianceFramework,
        detailed_analysis: bool,
    ) -> Optional[ComplianceIssue]:
        """
        Check if a specific requirement is met.

        Returns:
            ComplianceIssue if non-compliant, None if compliant
        """
        # Check if any keywords are present
        found_keywords = []
        for keyword in requirement["keywords"]:
            if re.search(keyword, text_lower):
                found_keywords.append(keyword)

        # Determine compliance status
        if found_keywords:
            status = "compliant"
            evidence = f"Found indicators: {', '.join(found_keywords)}"
            return None  # Compliant, no issue to return
        else:
            status = "non-compliant"
            evidence = "Required information not found in document"

            # Create compliance issue
            issue = ComplianceIssue(
                issue_id=f"{requirement['id']}_{uuid.uuid4().hex[:8]}",
                framework=framework,
                severity=requirement["severity"],
                requirement=requirement["name"],
                current_status=status,
                description=requirement["description"],
                evidence=evidence if detailed_analysis else None,
                recommendation=self._get_requirement_recommendation(requirement, framework),
                regulation_reference=requirement.get("article"),
            )

            return issue

    def _get_requirement_recommendation(self, requirement: Dict, framework: ComplianceFramework) -> str:
        """Get recommendation for addressing a compliance issue."""
        recommendations = {
            "GDPR-1": "Add a section explaining the lawful basis for processing personal data (e.g., consent, legitimate interest).",
            "GDPR-2": "Include information about data subject rights (access, rectification, erasure, portability) and how to exercise them.",
            "GDPR-3": "Clearly state the purposes for which personal data is collected and processed.",
            "GDPR-4": "Specify how long personal data will be retained and the criteria for determining retention periods.",
            "GDPR-5": "Disclose if and how personal data is shared with third parties, including the categories of recipients.",
            "GDPR-6": "Provide contact information for your Data Protection Officer or privacy contact.",
            "GDPR-7": "Address how personal data is transferred internationally and the safeguards in place.",
            "GDPR-8": "Disclose any automated decision-making or profiling activities.",
            "HIPAA-1": "Specify how Protected Health Information (PHI) is collected, used, and protected.",
            "HIPAA-2": "Ensure compliance with HIPAA Privacy Rule requirements for handling PHI.",
            "HIPAA-3": "Document administrative, physical, and technical safeguards for protecting PHI.",
            "HIPAA-4": "Include breach notification procedures and timelines.",
            "HIPAA-5": "Ensure Business Associate Agreements are in place with service providers.",
            "HIPAA-6": "Inform patients of their rights regarding their health information.",
        }

        recommendation = recommendations.get(
            requirement["id"],
            f"Address the {requirement['name']} requirement for {framework.value.upper()} compliance."
        )

        return recommendation

    def _generate_compliance_summary(self, results: Dict, frameworks: List[ComplianceFramework]) -> str:
        """Generate a summary of compliance check results."""
        score = results["overall_compliance_score"]
        issue_count = len(results["issues"])
        compliant_count = len(results["compliant_requirements"])

        framework_names = [fw.value.upper() for fw in frameworks]
        framework_str = ", ".join(framework_names)

        if score >= 90:
            status = "highly compliant"
        elif score >= 70:
            status = "mostly compliant"
        elif score >= 50:
            status = "partially compliant"
        else:
            status = "non-compliant"

        summary = (
            f"The document is {status} with {framework_str} requirements. "
            f"Compliance score: {score:.1f}%. "
            f"Found {issue_count} compliance issues and {compliant_count} compliant requirements. "
        )

        if issue_count > 0:
            critical_issues = sum(1 for issue in results["issues"] if issue.severity == RiskLevel.CRITICAL)
            high_issues = sum(1 for issue in results["issues"] if issue.severity == RiskLevel.HIGH)

            if critical_issues > 0:
                summary += f"ATTENTION: {critical_issues} critical issues require immediate attention. "
            if high_issues > 0:
                summary += f"{high_issues} high-severity issues should be addressed. "

        return summary

    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate actionable recommendations based on compliance issues."""
        recommendations = []

        # Group issues by severity
        critical_issues = [i for i in results["issues"] if i.severity == RiskLevel.CRITICAL]
        high_issues = [i for i in results["issues"] if i.severity == RiskLevel.HIGH]

        if critical_issues:
            recommendations.append(
                f"URGENT: Address {len(critical_issues)} critical compliance issues immediately to avoid legal exposure."
            )

        if high_issues:
            recommendations.append(
                f"Address {len(high_issues)} high-severity compliance issues as a priority."
            )

        # Add specific recommendations
        if results["overall_compliance_score"] < 70:
            recommendations.append(
                "Consider conducting a comprehensive compliance review with legal counsel."
            )

        if len(results["issues"]) > 5:
            recommendations.append(
                "Multiple compliance gaps detected. Consider using a compliance framework checklist."
            )

        # Add framework-specific recommendations
        frameworks = results.get("frameworks_checked", [])
        if ComplianceFramework.GDPR in frameworks:
            gdpr_issues = [i for i in results["issues"] if i.framework == ComplianceFramework.GDPR]
            if len(gdpr_issues) > 3:
                recommendations.append(
                    "Consider using a GDPR-compliant privacy policy template to ensure all requirements are met."
                )

        if ComplianceFramework.HIPAA in frameworks:
            hipaa_issues = [i for i in results["issues"] if i.framework == ComplianceFramework.HIPAA]
            if len(hipaa_issues) > 2:
                recommendations.append(
                    "Consult with a HIPAA compliance specialist to ensure proper handling of PHI."
                )

        if not recommendations:
            recommendations.append("Continue monitoring for compliance and update policies as regulations evolve.")

        return recommendations
