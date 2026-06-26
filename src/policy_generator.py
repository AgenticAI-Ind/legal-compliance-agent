"""
LLM-based policy document generation (privacy policies, terms of service, etc.).
"""

import logging
import os
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage

from src.models import ComplianceFramework, GeneratedPolicy


logger = logging.getLogger(__name__)


class PolicyGenerator:
    """Generates legal policy documents using LLMs."""

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize policy generator.

        Args:
            openai_api_key: OpenAI API key
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        if self.openai_api_key:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo-16k",
                temperature=0.3,
                openai_api_key=self.openai_api_key
            )
        else:
            logger.warning("OpenAI API key not provided, using fallback templates")
            self.llm = None

        logger.info("PolicyGenerator initialized")

    def generate_privacy_policy(
        self,
        company_name: str,
        company_type: str,
        data_collected: List[str],
        data_usage: List[str],
        third_party_sharing: bool,
        cookies_used: bool,
        user_rights: List[str],
        contact_email: str,
        jurisdiction: str = "EU",
        frameworks: List[ComplianceFramework] = None,
    ) -> Dict:
        """
        Generate a privacy policy document.

        Args:
            company_name: Name of the company
            company_type: Type of business
            data_collected: Types of data collected
            data_usage: How data is used
            third_party_sharing: Whether data is shared with third parties
            cookies_used: Whether cookies are used
            user_rights: List of user rights to include
            contact_email: Contact email for privacy inquiries
            jurisdiction: Primary jurisdiction
            frameworks: Compliance frameworks to address

        Returns:
            Dictionary with generated policy and metadata
        """
        logger.info(f"Generating privacy policy for {company_name}")
        start_time = datetime.now()

        if frameworks is None:
            frameworks = [ComplianceFramework.GDPR]

        if self.llm:
            policy_content = self._generate_policy_with_llm(
                company_name=company_name,
                company_type=company_type,
                data_collected=data_collected,
                data_usage=data_usage,
                third_party_sharing=third_party_sharing,
                cookies_used=cookies_used,
                user_rights=user_rights,
                contact_email=contact_email,
                jurisdiction=jurisdiction,
                frameworks=frameworks,
            )
        else:
            policy_content = self._generate_policy_with_template(
                company_name=company_name,
                company_type=company_type,
                data_collected=data_collected,
                data_usage=data_usage,
                third_party_sharing=third_party_sharing,
                cookies_used=cookies_used,
                user_rights=user_rights,
                contact_email=contact_email,
                jurisdiction=jurisdiction,
                frameworks=frameworks,
            )

        # Parse sections
        sections = self._parse_policy_sections(policy_content)

        # Create policy object
        policy = GeneratedPolicy(
            policy_id=str(uuid.uuid4()),
            policy_type="privacy_policy",
            content=policy_content,
            sections=sections,
            compliance_frameworks=frameworks,
            last_updated=datetime.utcnow(),
            version="1.0",
        )

        # Evaluate compliance
        compliance_score = self._evaluate_policy_compliance(policy_content, frameworks)

        # Generate recommendations
        recommendations = self._generate_policy_recommendations(
            policy_content,
            frameworks,
            compliance_score
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        logger.info(
            f"Privacy policy generated in {processing_time:.2f}s. "
            f"Compliance score: {compliance_score:.1f}%"
        )

        return {
            "policy": policy,
            "compliance_score": compliance_score,
            "recommendations": recommendations,
            "processing_time": processing_time,
        }

    def _generate_policy_with_llm(
        self,
        company_name: str,
        company_type: str,
        data_collected: List[str],
        data_usage: List[str],
        third_party_sharing: bool,
        cookies_used: bool,
        user_rights: List[str],
        contact_email: str,
        jurisdiction: str,
        frameworks: List[ComplianceFramework],
    ) -> str:
        """Generate policy using LLM."""
        frameworks_str = ", ".join([f.value.upper() for f in frameworks])

        system_prompt = f"""You are a legal AI assistant specialized in generating privacy policies.
Generate a comprehensive, legally sound privacy policy that complies with {frameworks_str}.
The policy should be clear, professional, and include all required sections.
Use formal legal language but ensure it's understandable to average users."""

        user_prompt = f"""Generate a comprehensive privacy policy with the following details:

Company: {company_name}
Business Type: {company_type}
Jurisdiction: {jurisdiction}
Compliance Frameworks: {frameworks_str}

Data Collection:
{chr(10).join('- ' + item for item in data_collected)}

Data Usage:
{chr(10).join('- ' + item for item in data_usage)}

Third-Party Sharing: {'Yes' if third_party_sharing else 'No'}
Cookies: {'Used' if cookies_used else 'Not used'}

User Rights to Include:
{chr(10).join('- ' + right for right in user_rights)}

Contact Email: {contact_email}

Please generate a complete privacy policy with the following sections:
1. Introduction
2. Information We Collect
3. How We Use Your Information
4. Data Sharing and Disclosure
5. Cookies and Tracking Technologies
6. Your Rights and Choices
7. Data Security
8. International Data Transfers
9. Children's Privacy
10. Changes to This Policy
11. Contact Information

Ensure the policy is compliant with {frameworks_str} requirements."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm(messages)
            return response.content

        except Exception as e:
            logger.error(f"Error generating policy with LLM: {e}")
            return self._generate_policy_with_template(
                company_name, company_type, data_collected, data_usage,
                third_party_sharing, cookies_used, user_rights, contact_email,
                jurisdiction, frameworks
            )

    def _generate_policy_with_template(
        self,
        company_name: str,
        company_type: str,
        data_collected: List[str],
        data_usage: List[str],
        third_party_sharing: bool,
        cookies_used: bool,
        user_rights: List[str],
        contact_email: str,
        jurisdiction: str,
        frameworks: List[ComplianceFramework],
    ) -> str:
        """Generate policy using template (fallback)."""
        date_str = datetime.utcnow().strftime("%B %d, %Y")
        frameworks_str = ", ".join([f.value.upper() for f in frameworks])

        policy = f"""PRIVACY POLICY

Last Updated: {date_str}

1. INTRODUCTION

{company_name} ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our services as a {company_type}.

This policy is designed to comply with {frameworks_str} and applicable privacy laws in {jurisdiction}.

2. INFORMATION WE COLLECT

We collect the following types of information:

{chr(10).join('- ' + item for item in data_collected)}

3. HOW WE USE YOUR INFORMATION

We use the information we collect for the following purposes:

{chr(10).join('- ' + item for item in data_usage)}

4. DATA SHARING AND DISCLOSURE

{"We may share your information with trusted third-party service providers who assist us in operating our services. These parties are obligated to protect your information and use it only for the purposes we specify." if third_party_sharing else "We do not share your personal information with third parties except as required by law."}

5. COOKIES AND TRACKING TECHNOLOGIES

{"We use cookies and similar tracking technologies to enhance your experience, analyze usage patterns, and improve our services. You can control cookie settings through your browser preferences." if cookies_used else "We do not use cookies or tracking technologies on our services."}

6. YOUR RIGHTS AND CHOICES

You have the following rights regarding your personal information:

{chr(10).join('- Right to ' + right for right in user_rights)}

To exercise these rights, please contact us at {contact_email}.

7. DATA SECURITY

We implement appropriate technical and organizational measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction. However, no method of transmission over the Internet or electronic storage is 100% secure.

8. INTERNATIONAL DATA TRANSFERS

{"If we transfer your data internationally, we ensure appropriate safeguards are in place, such as standard contractual clauses approved by relevant authorities." if jurisdiction == "EU" else "Your data may be transferred to and processed in countries other than your country of residence."}

9. DATA RETENTION

We retain your personal information only for as long as necessary to fulfill the purposes outlined in this policy, unless a longer retention period is required or permitted by law.

10. CHILDREN'S PRIVACY

Our services are not intended for children under the age of 16. We do not knowingly collect personal information from children. If you believe we have collected information from a child, please contact us immediately.

11. CHANGES TO THIS POLICY

We may update this Privacy Policy from time to time. We will notify you of any material changes by posting the new policy on our website and updating the "Last Updated" date.

12. CONTACT INFORMATION

If you have any questions about this Privacy Policy or our privacy practices, please contact us at:

Email: {contact_email}
Company: {company_name}

13. LEGAL BASIS FOR PROCESSING (GDPR)

If you are in the European Economic Area (EEA), our legal basis for collecting and using your personal information depends on the data collected and the specific context:

- Consent: Where you have given us explicit consent
- Contract: Where processing is necessary for a contract with you
- Legal Obligation: Where we must comply with legal requirements
- Legitimate Interests: Where processing is in our legitimate business interests

14. COMPLAINTS

If you are in the EEA and believe we have not handled your personal information properly, you have the right to lodge a complaint with your local supervisory authority.

---

This Privacy Policy was generated for informational purposes. {company_name} should review this policy with qualified legal counsel to ensure it meets all applicable legal requirements.
"""
        return policy

    def _parse_policy_sections(self, policy_content: str) -> Dict[str, str]:
        """Parse policy content into sections."""
        sections = {}

        # Split by numbered sections
        section_pattern = r'(\d+\.\s+[A-Z\s]+)\n'
        parts = []

        # Simple section extraction
        lines = policy_content.split('\n')
        current_section = None
        current_content = []

        for line in lines:
            # Check if line is a section header (starts with number)
            if line.strip() and line[0].isdigit() and '.' in line[:5]:
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                # Start new section
                current_section = line.strip()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    def _evaluate_policy_compliance(
        self,
        policy_content: str,
        frameworks: List[ComplianceFramework]
    ) -> float:
        """Evaluate policy compliance with frameworks."""
        policy_lower = policy_content.lower()
        total_score = 0.0
        checks_count = 0

        # GDPR compliance checks
        if ComplianceFramework.GDPR in frameworks:
            gdpr_requirements = [
                ("right to access", 10),
                ("right to erasure", 10),
                ("right to portability", 10),
                ("data protection", 10),
                ("consent", 10),
                ("legitimate interest", 5),
                ("data retention", 10),
                ("international transfer", 5),
                ("supervisory authority", 5),
            ]

            for requirement, weight in gdpr_requirements:
                checks_count += 1
                if requirement in policy_lower:
                    total_score += weight

        # HIPAA compliance checks
        if ComplianceFramework.HIPAA in frameworks:
            hipaa_requirements = [
                ("protected health information", 15),
                ("phi", 10),
                ("security", 10),
                ("breach", 10),
                ("business associate", 5),
            ]

            for requirement, weight in hipaa_requirements:
                checks_count += 1
                if requirement in policy_lower:
                    total_score += weight

        # CCPA compliance checks
        if ComplianceFramework.CCPA in frameworks:
            ccpa_requirements = [
                ("right to know", 10),
                ("right to delete", 10),
                ("opt-out", 10),
                ("sale of information", 10),
                ("non-discrimination", 5),
            ]

            for requirement, weight in ccpa_requirements:
                checks_count += 1
                if requirement in policy_lower:
                    total_score += weight

        # General best practices
        general_checks = [
            ("contact", 5),
            ("email", 5),
            ("security", 5),
            ("update", 5),
            ("cookie", 5),
        ]

        for requirement, weight in general_checks:
            checks_count += 1
            if requirement in policy_lower:
                total_score += weight

        # Calculate percentage
        max_score = checks_count * 10  # Normalize to percentage
        if max_score > 0:
            compliance_score = (total_score / max_score) * 100
        else:
            compliance_score = 0.0

        return min(100.0, compliance_score)

    def _generate_policy_recommendations(
        self,
        policy_content: str,
        frameworks: List[ComplianceFramework],
        compliance_score: float
    ) -> List[str]:
        """Generate recommendations for improving the policy."""
        recommendations = []
        policy_lower = policy_content.lower()

        # General recommendations based on score
        if compliance_score < 60:
            recommendations.append(
                "The policy has significant gaps. Consider consulting with a privacy attorney."
            )
        elif compliance_score < 80:
            recommendations.append(
                "The policy covers most requirements but could be more comprehensive."
            )

        # Framework-specific recommendations
        if ComplianceFramework.GDPR in frameworks:
            if "data protection officer" not in policy_lower and "dpo" not in policy_lower:
                recommendations.append(
                    "Consider adding information about your Data Protection Officer (if applicable)."
                )
            if "legal basis" not in policy_lower:
                recommendations.append(
                    "Add explicit information about the legal basis for processing under GDPR."
                )
            if "data retention" not in policy_lower:
                recommendations.append(
                    "Specify data retention periods to comply with GDPR Article 5(1)(e)."
                )

        if ComplianceFramework.HIPAA in frameworks:
            if "business associate" not in policy_lower:
                recommendations.append(
                    "Include information about Business Associate Agreements for HIPAA compliance."
                )
            if "breach notification" not in policy_lower:
                recommendations.append(
                    "Add breach notification procedures as required by HIPAA."
                )

        if ComplianceFramework.CCPA in frameworks:
            if "do not sell" not in policy_lower:
                recommendations.append(
                    "Include a 'Do Not Sell My Personal Information' link or mechanism for CCPA compliance."
                )

        # General best practices
        if "effective date" not in policy_lower and "last updated" not in policy_lower:
            recommendations.append(
                "Add an effective date or last updated date to the policy."
            )

        if len(policy_content) < 1000:
            recommendations.append(
                "The policy appears brief. Consider adding more detail to each section."
            )

        if "we may update" not in policy_lower and "we reserve the right" not in policy_lower:
            recommendations.append(
                "Include information about how policy updates will be communicated to users."
            )

        if not recommendations:
            recommendations.append(
                "The policy appears comprehensive. Have it reviewed by legal counsel before publication."
            )

        return recommendations

    def generate_terms_of_service(
        self,
        company_name: str,
        service_description: str,
        contact_email: str,
        jurisdiction: str = "United States",
    ) -> str:
        """Generate terms of service document."""
        logger.info(f"Generating terms of service for {company_name}")

        date_str = datetime.utcnow().strftime("%B %d, %Y")

        terms = f"""TERMS OF SERVICE

Last Updated: {date_str}

1. ACCEPTANCE OF TERMS

By accessing or using the services provided by {company_name} ("{service_description}"), you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our services.

2. DESCRIPTION OF SERVICE

{company_name} provides {service_description}. We reserve the right to modify, suspend, or discontinue any aspect of our services at any time.

3. USER OBLIGATIONS

You agree to:
- Provide accurate and complete information
- Maintain the security of your account credentials
- Use the services in compliance with all applicable laws
- Not engage in any activity that interferes with or disrupts the services

4. INTELLECTUAL PROPERTY

All content, features, and functionality of our services are owned by {company_name} and are protected by copyright, trademark, and other intellectual property laws.

5. LIMITATION OF LIABILITY

To the maximum extent permitted by law, {company_name} shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising out of or relating to your use of the services.

6. INDEMNIFICATION

You agree to indemnify and hold harmless {company_name} from any claims, damages, losses, liabilities, and expenses arising from your use of the services or violation of these terms.

7. GOVERNING LAW

These Terms shall be governed by the laws of {jurisdiction}, without regard to its conflict of law provisions.

8. DISPUTE RESOLUTION

Any disputes arising from these Terms shall be resolved through binding arbitration in accordance with the rules of the American Arbitration Association.

9. TERMINATION

We reserve the right to terminate or suspend your access to our services at any time, with or without cause or notice.

10. CHANGES TO TERMS

We may update these Terms from time to time. Continued use of our services after changes constitutes acceptance of the updated Terms.

11. CONTACT INFORMATION

For questions about these Terms, please contact us at: {contact_email}

---

This document is a template and should be reviewed by qualified legal counsel before use.
"""
        return terms
