"""
Example usage of Legal & Compliance Agent.

This script demonstrates all major features of the agent.
"""

import requests
import json
from typing import Dict, List


# API Base URL
BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60 + "\n")


def example_1_contract_analysis():
    """Example 1: Analyze an employment contract."""
    print_section("Example 1: Contract Analysis")

    contract_text = """
    EMPLOYMENT AGREEMENT

    This Employment Agreement is entered into as of January 15, 2024,
    between Tech Innovations Corp ("Company") and Jane Smith ("Employee").

    1. POSITION AND DUTIES
    Employee shall serve as Senior Software Engineer and shall perform
    duties as assigned by the Company.

    2. COMPENSATION
    Company shall pay Employee an annual salary of $150,000, payable
    in bi-weekly installments.

    3. BENEFITS
    Employee shall be entitled to standard company benefits including
    health insurance, 401(k), and 20 days paid vacation per year.

    4. TERMINATION
    Either party may terminate this agreement with 60 days written notice.
    Company may terminate immediately for cause.

    5. CONFIDENTIALITY
    Employee agrees to maintain confidentiality of all proprietary
    information during employment and for 3 years thereafter.

    6. INTELLECTUAL PROPERTY
    All work product created by Employee shall be the property of Company
    as work made for hire.

    7. NON-COMPETE
    Employee agrees not to engage in competing business within 50 miles
    for 1 year following termination.

    8. GOVERNING LAW
    This agreement shall be governed by the laws of California.
    """

    response = requests.post(
        f"{BASE_URL}/analyze-contract",
        json={
            "document_text": contract_text,
            "extract_parties": True,
            "extract_dates": True,
            "extract_financial": True,
            "detect_risks": True
        }
    )

    if response.status_code == 200:
        result = response.json()

        print("✓ Analysis Complete\n")
        print(f"Document ID: {result['document_id']}")
        print(f"Summary: {result['summary'][:200]}...\n")

        print("Parties:")
        for party in result['parties']:
            print(f"  • {party['name']} - {party['role']}")

        print("\nKey Dates:")
        for date_type, date_value in result['key_dates'].items():
            print(f"  • {date_type}: {date_value}")

        print("\nFinancial Terms:")
        for term in result['financial_terms']:
            print(f"  • {term['description']}: ${term['amount']:,.2f}")
            if term['frequency']:
                print(f"    Frequency: {term['frequency']}")

        print(f"\nRisk Assessment:")
        print(f"  Overall Risk Score: {result['overall_risk_score']}/10")
        print(f"  Risks Identified: {len(result['risks'])}")

        if result['risks']:
            print("\n  Top Risks:")
            for risk in result['risks'][:3]:
                print(f"    [{risk['risk_level'].upper()}] {risk['description']}")
                print(f"      → {risk['recommendation']}")

        print(f"\nProcessing Time: {result['processing_time']:.2f}s")

    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)


def example_2_compliance_checking():
    """Example 2: Check GDPR compliance of a privacy policy."""
    print_section("Example 2: Compliance Checking")

    privacy_policy = """
    PRIVACY POLICY

    Effective Date: January 1, 2024

    1. INTRODUCTION
    We at DataTech Inc respect your privacy and are committed to protecting
    your personal data. This privacy policy explains how we collect and use
    your information in compliance with GDPR and CCPA.

    2. DATA WE COLLECT
    We collect name, email address, usage data, and cookies. We collect this
    data with your consent and for our legitimate business interests.

    3. HOW WE USE YOUR DATA
    We use your data to provide services, improve our platform, and send
    marketing communications (with your consent).

    4. YOUR RIGHTS
    You have the right to access your data, request corrections, request
    deletion, and port your data to another service. You also have the right
    to object to processing and withdraw consent.

    5. DATA RETENTION
    We retain your personal data for 5 years after account closure, unless
    required by law to retain it longer.

    6. THIRD-PARTY SHARING
    We may share your data with service providers under strict confidentiality
    agreements. We do not sell your personal data.

    7. INTERNATIONAL TRANSFERS
    Your data may be transferred to countries outside the EU. We use Standard
    Contractual Clauses approved by the European Commission.

    8. SECURITY
    We implement appropriate technical and organizational measures including
    encryption, access controls, and regular security audits.

    9. COOKIES
    We use essential cookies and analytics cookies. You can manage cookie
    preferences in your browser settings.

    10. CHANGES TO THIS POLICY
    We may update this policy from time to time. We will notify you of
    material changes by email.

    11. CONTACT
    For privacy questions, contact us at privacy@datatech.com or our
    Data Protection Officer at dpo@datatech.com.
    """

    response = requests.post(
        f"{BASE_URL}/check-compliance",
        json={
            "document_text": privacy_policy,
            "frameworks": ["gdpr", "ccpa"],
            "document_type": "privacy_policy",
            "detailed_analysis": True
        }
    )

    if response.status_code == 200:
        result = response.json()

        print("✓ Compliance Check Complete\n")
        print(f"Frameworks Checked: {', '.join([f.upper() for f in result['frameworks_checked']])}")
        print(f"Overall Compliance Score: {result['overall_compliance_score']:.1f}%\n")

        if result['overall_compliance_score'] >= 80:
            print("✓ Highly Compliant")
        elif result['overall_compliance_score'] >= 60:
            print("⚠ Mostly Compliant")
        else:
            print("✗ Compliance Gaps Detected")

        print(f"\nCompliant Requirements: {len(result['compliant_requirements'])}")
        print(f"Issues Found: {len(result['issues'])}")

        if result['issues']:
            print("\nTop Compliance Issues:")
            for issue in result['issues'][:5]:
                print(f"\n  [{issue['severity'].upper()}] {issue['requirement']}")
                print(f"  Framework: {issue['framework'].upper()}")
                print(f"  Status: {issue['current_status']}")
                print(f"  → {issue['recommendation']}")
                if issue['regulation_reference']:
                    print(f"    Reference: {issue['regulation_reference']}")

        print("\nOverall Assessment:")
        print(f"  {result['summary']}")

        if result['recommendations']:
            print("\nRecommendations:")
            for i, rec in enumerate(result['recommendations'][:5], 1):
                print(f"  {i}. {rec}")

    else:
        print(f"✗ Error: {response.status_code}")


def example_3_legal_qa():
    """Example 3: Ask questions about a legal document."""
    print_section("Example 3: Legal Q&A")

    service_agreement = """
    SERVICE LEVEL AGREEMENT

    1. SERVICE DESCRIPTION
    Provider will deliver cloud hosting services with 99.9% uptime guarantee.

    2. TERM
    This agreement is for an initial term of 12 months, automatically renewing
    for successive 12-month periods unless either party provides 90 days notice.

    3. FEES
    Customer pays $5,000 per month, due on the first day of each month.
    Late payments incur 1.5% monthly interest.

    4. SERVICE LEVELS
    Provider guarantees 99.9% uptime. If uptime falls below 99.5%, Customer
    receives 10% credit. Below 99%, Customer receives 25% credit.

    5. SUPPORT
    24/7 support via email and phone. Response times: Critical (1 hour),
    High (4 hours), Medium (1 business day), Low (2 business days).

    6. TERMINATION
    Either party may terminate for convenience with 90 days notice.
    Customer may terminate immediately if uptime falls below 95% for 3
    consecutive months. Provider may terminate for non-payment after 30 days.

    7. LIABILITY
    Provider's liability is limited to fees paid in the 12 months prior to
    the claim, except for willful misconduct or gross negligence.

    8. DATA PROTECTION
    Provider will comply with GDPR and implement appropriate security measures.
    Customer retains ownership of all customer data.
    """

    questions = [
        "What is the uptime guarantee?",
        "How much does the service cost?",
        "How can the agreement be terminated?",
        "What happens if uptime falls below 99%?"
    ]

    for question in questions:
        print(f"\nQ: {question}")

        response = requests.post(
            f"{BASE_URL}/qa-legal-document",
            json={
                "question": question,
                "document_text": service_agreement,
                "max_sources": 3,
                "include_citations": True
            }
        )

        if response.status_code == 200:
            result = response.json()
            print(f"A: {result['answer']}")
            print(f"   Confidence: {result['confidence']:.0%}")

            if result['citations'] and len(result['citations']) > 0:
                print(f"   Source: \"{result['citations'][0]['excerpt'][:80]}...\"")
        else:
            print(f"   Error: {response.status_code}")


def example_4_clause_extraction():
    """Example 4: Extract specific clauses from a contract."""
    print_section("Example 4: Clause Extraction")

    contract_text = """
    MASTER SERVICES AGREEMENT

    CONFIDENTIALITY
    Each party agrees to keep confidential all information disclosed by the
    other party. This obligation survives for 5 years after termination.

    PAYMENT TERMS
    Client shall pay Consultant $150 per hour for services rendered. Invoices
    are due within 30 days. Late payments accrue 1.5% monthly interest.

    TERMINATION
    Either party may terminate this agreement with 60 days written notice.
    Immediate termination is permitted for material breach not cured within
    15 days of written notice.

    LIMITATION OF LIABILITY
    Neither party shall be liable for indirect, incidental, or consequential
    damages. Total liability is capped at the fees paid in the prior 12 months.

    INTELLECTUAL PROPERTY
    Client retains ownership of all pre-existing IP. Consultant retains
    ownership of general methodologies. Work product created specifically for
    Client shall be Client's property upon full payment.

    INDEMNIFICATION
    Each party shall indemnify the other against third-party claims arising
    from breach of this agreement or violation of applicable laws.

    GOVERNING LAW AND DISPUTES
    This agreement is governed by California law. Disputes shall be resolved
    through binding arbitration under AAA rules in San Francisco.

    WARRANTY DISCLAIMER
    Services are provided "as is" without warranties of any kind, express or
    implied, including merchantability or fitness for a particular purpose.
    """

    response = requests.post(
        f"{BASE_URL}/extract-clauses",
        json={
            "document_text": contract_text,
            "clause_types": [
                "confidentiality",
                "payment",
                "termination",
                "liability",
                "intellectual_property"
            ],
            "min_confidence": 0.6
        }
    )

    if response.status_code == 200:
        result = response.json()

        print("✓ Clause Extraction Complete\n")
        print(f"Total Clauses Found: {result['total_clauses']}")
        print(f"Document Coverage: {result['coverage_percentage']:.1f}%\n")

        for clause in result['extracted_clauses']:
            print(f"\n{clause['clause_type'].upper().replace('_', ' ')}")
            print(f"  Confidence: {clause['confidence']:.0%}")
            print(f"  Text: {clause['text'][:150]}...")

            if clause['key_terms']:
                print(f"  Key Terms: {', '.join(clause['key_terms'][:5])}")

            if clause['risks']:
                print(f"  ⚠ Risks: {', '.join(clause['risks'])}")

        print(f"\nProcessing Time: {result['processing_time']:.2f}s")

    else:
        print(f"✗ Error: {response.status_code}")


def example_5_policy_generation():
    """Example 5: Generate a privacy policy."""
    print_section("Example 5: Privacy Policy Generation")

    response = requests.post(
        f"{BASE_URL}/generate-privacy-policy",
        json={
            "company_name": "EcoShop Online",
            "company_type": "E-commerce Platform",
            "data_collected": [
                "name",
                "email address",
                "shipping address",
                "billing information",
                "purchase history",
                "browsing behavior"
            ],
            "data_usage": [
                "order processing and fulfillment",
                "customer service and support",
                "personalized recommendations",
                "marketing communications",
                "fraud prevention",
                "analytics and improvement"
            ],
            "third_party_sharing": True,
            "cookies_used": True,
            "user_rights": ["access", "deletion", "portability", "opt-out"],
            "contact_email": "privacy@ecoshop.com",
            "jurisdiction": "EU",
            "frameworks": ["gdpr", "ccpa"]
        }
    )

    if response.status_code == 200:
        result = response.json()

        print("✓ Privacy Policy Generated\n")
        print(f"Policy ID: {result['policy']['policy_id']}")
        print(f"Policy Type: {result['policy']['policy_type']}")
        print(f"Compliance Score: {result['compliance_score']:.1f}%")
        print(f"Frameworks: {', '.join([f.upper() for f in result['policy']['compliance_frameworks']])}")

        print("\nPolicy Preview:")
        print("-" * 60)
        # Show first 500 characters
        print(result['policy']['content'][:500] + "...")
        print("-" * 60)

        print(f"\nSections Included: {len(result['policy']['sections'])}")
        for section in list(result['policy']['sections'].keys())[:5]:
            print(f"  • {section}")

        if result['recommendations']:
            print("\nRecommendations for Improvement:")
            for i, rec in enumerate(result['recommendations'], 1):
                print(f"  {i}. {rec}")

        # Save to file
        with open("generated_privacy_policy.txt", "w") as f:
            f.write(result['policy']['content'])

        print("\n✓ Full policy saved to: generated_privacy_policy.txt")

    else:
        print(f"✗ Error: {response.status_code}")


def example_6_risk_assessment():
    """Example 6: Comprehensive risk assessment."""
    print_section("Example 6: Risk Assessment")

    risky_contract = """
    INDEPENDENT CONTRACTOR AGREEMENT

    1. SERVICES
    Contractor shall provide software development services as directed by Company.

    2. PAYMENT
    Payment is at Company's sole discretion based on satisfaction with work.

    3. TERMINATION
    Company may terminate this agreement immediately at any time without cause or notice.

    4. LIABILITY
    Contractor assumes unlimited liability for any and all claims, damages, or losses
    arising from the services, including indirect and consequential damages.

    5. INTELLECTUAL PROPERTY
    All intellectual property, including pre-existing IP and future inventions,
    shall automatically become Company's exclusive property.

    6. NON-COMPETE
    Contractor agrees not to engage in any competing business activities worldwide
    for a period of 5 years after termination.

    7. CONFIDENTIALITY
    Contractor shall maintain confidentiality of all information indefinitely.

    8. INDEMNIFICATION
    Contractor shall indemnify Company for any and all claims, including those
    arising from Company's own negligence.

    9. DISPUTE RESOLUTION
    All disputes shall be resolved through binding arbitration. Contractor waives
    all rights to jury trial and class action lawsuits.

    10. AMENDMENTS
    Company may modify this agreement at any time without notice to Contractor.
    """

    response = requests.post(
        f"{BASE_URL}/risk-assessment",
        json={
            "document_text": risky_contract,
            "document_type": "contract",
            "include_remediation": True
        }
    )

    if response.status_code == 200:
        result = response.json()

        print("✓ Risk Assessment Complete\n")
        print(f"Overall Risk Score: {result['overall_risk_score']:.1f}/10")
        print(f"Risk Level: {result['risk_level'].upper()}\n")

        # Risk distribution
        print("Risk Distribution:")
        for level, count in sorted(result['risk_distribution'].items(), reverse=True):
            bars = "█" * count
            print(f"  {level.upper():10} {bars} ({count})")

        # Key concerns
        if result['key_concerns']:
            print("\nKey Concerns:")
            for concern in result['key_concerns']:
                print(f"  ⚠ {concern}")

        # Detailed risks
        print(f"\nDetailed Risk Analysis ({len(result['risks'])} risks found):")
        for risk in result['risks'][:5]:  # Show top 5
            print(f"\n  [{risk['risk_level'].upper()}] {risk['category']}")
            print(f"  Description: {risk['description']}")
            print(f"  Confidence: {risk['confidence']:.0%}")
            print(f"  → Recommendation: {risk['recommendation']}")

        # Recommendations
        if result['recommendations']:
            print("\nActionable Recommendations:")
            for i, rec in enumerate(result['recommendations'][:5], 1):
                print(f"  {i}. {rec}")

        print(f"\nProcessing Time: {result['processing_time']:.2f}s")

    else:
        print(f"✗ Error: {response.status_code}")


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "    Legal & Compliance Agent - Usage Examples    ".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")

    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("\n✗ Error: API is not responding")
            print(f"  Make sure the API is running at {BASE_URL}")
            return
    except requests.exceptions.ConnectionError:
        print(f"\n✗ Error: Cannot connect to API at {BASE_URL}")
        print("  Please start the API first:")
        print("    docker-compose up -d")
        print("  or")
        print("    uvicorn src.main:app --reload")
        return

    print(f"\n✓ Connected to API at {BASE_URL}\n")

    # Run examples
    try:
        example_1_contract_analysis()
        example_2_compliance_checking()
        example_3_legal_qa()
        example_4_clause_extraction()
        example_5_policy_generation()
        example_6_risk_assessment()

        print("\n")
        print("=" * 60)
        print(" All Examples Completed Successfully!")
        print("=" * 60)
        print("\nNext Steps:")
        print("  • Check the API documentation: http://localhost:8000/docs")
        print("  • Try the interactive Swagger UI")
        print("  • Explore the source code in src/")
        print("  • Read the full documentation in docs/")
        print()

    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
