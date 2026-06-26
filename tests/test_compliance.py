"""
Tests for compliance checker.
"""

import pytest
from src.compliance_checker import ComplianceChecker
from src.models import ComplianceFramework, RiskLevel


@pytest.fixture
def checker():
    """Create compliance checker instance."""
    return ComplianceChecker()


@pytest.fixture
def gdpr_compliant_policy():
    """Sample GDPR compliant privacy policy."""
    return """
    PRIVACY POLICY

    1. Information We Collect
    We collect personal data including name, email, and usage information.

    2. Legal Basis for Processing
    We process your data based on your consent and our legitimate interests.

    3. Your Rights
    You have the right to access, rectification, erasure, and data portability
    of your personal information.

    4. Data Retention
    We retain your data for 3 years after account closure.

    5. Third-Party Sharing
    We may share your data with service providers under appropriate agreements.

    6. Data Protection Officer
    Contact our DPO at dpo@example.com for privacy concerns.

    7. International Transfers
    Data may be transferred outside the EU with appropriate safeguards.

    8. Automated Decision Making
    We do not use automated decision-making or profiling.
    """


@pytest.fixture
def hipaa_document():
    """Sample HIPAA-related document."""
    return """
    HEALTHCARE PRIVACY NOTICE

    This notice describes how Protected Health Information (PHI) about you
    may be used and disclosed and how you can access this information.

    Security Safeguards:
    We implement encryption, access controls, and audit logs to protect PHI.

    Breach Notification:
    We will notify you within 60 days of discovering a breach of your PHI.

    Your Rights:
    You have the right to access your medical records and request amendments.

    Business Associates:
    We require Business Associate Agreements with all vendors handling PHI.
    """


def test_checker_initialization(checker):
    """Test checker initializes correctly."""
    assert checker is not None
    assert checker.compliance_rules is not None
    assert ComplianceFramework.GDPR in checker.compliance_rules


def test_gdpr_compliance_check(checker, gdpr_compliant_policy):
    """Test GDPR compliance checking."""
    results = checker.check_compliance(
        document_text=gdpr_compliant_policy,
        frameworks=[ComplianceFramework.GDPR]
    )

    assert results["overall_compliance_score"] > 70.0
    assert len(results["frameworks_checked"]) == 1
    assert results["frameworks_checked"][0] == ComplianceFramework.GDPR


def test_hipaa_compliance_check(checker, hipaa_document):
    """Test HIPAA compliance checking."""
    results = checker.check_compliance(
        document_text=hipaa_document,
        frameworks=[ComplianceFramework.HIPAA]
    )

    assert len(results["frameworks_checked"]) == 1
    assert results["frameworks_checked"][0] == ComplianceFramework.HIPAA
    assert results["overall_compliance_score"] > 50.0


def test_multiple_frameworks(checker, gdpr_compliant_policy):
    """Test checking multiple frameworks."""
    results = checker.check_compliance(
        document_text=gdpr_compliant_policy,
        frameworks=[ComplianceFramework.GDPR, ComplianceFramework.CCPA]
    )

    assert len(results["frameworks_checked"]) == 2
    assert ComplianceFramework.GDPR in results["frameworks_checked"]
    assert ComplianceFramework.CCPA in results["frameworks_checked"]


def test_non_compliant_document(checker):
    """Test detection of non-compliance."""
    minimal_policy = "We collect data. Contact us at email@example.com."

    results = checker.check_compliance(
        document_text=minimal_policy,
        frameworks=[ComplianceFramework.GDPR]
    )

    assert results["overall_compliance_score"] < 50.0
    assert len(results["issues"]) > 0


def test_compliance_issues(checker):
    """Test that compliance issues are properly identified."""
    incomplete_policy = "We collect your information for our purposes."

    results = checker.check_compliance(
        document_text=incomplete_policy,
        frameworks=[ComplianceFramework.GDPR],
        detailed_analysis=True
    )

    issues = results["issues"]
    assert len(issues) > 0

    # Check issue structure
    for issue in issues:
        assert issue.issue_id is not None
        assert issue.framework == ComplianceFramework.GDPR
        assert issue.severity in [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]
        assert issue.requirement is not None
        assert issue.recommendation is not None


def test_compliance_recommendations(checker, gdpr_compliant_policy):
    """Test generation of recommendations."""
    results = checker.check_compliance(
        document_text=gdpr_compliant_policy,
        frameworks=[ComplianceFramework.GDPR]
    )

    assert "recommendations" in results
    assert len(results["recommendations"]) > 0


def test_compliance_summary(checker, gdpr_compliant_policy):
    """Test compliance summary generation."""
    results = checker.check_compliance(
        document_text=gdpr_compliant_policy,
        frameworks=[ComplianceFramework.GDPR]
    )

    summary = results["summary"]
    assert len(summary) > 0
    assert "compliant" in summary.lower() or "compliance" in summary.lower()


def test_soc2_compliance(checker):
    """Test SOC2 compliance checking."""
    soc2_policy = """
    SECURITY POLICY

    We implement security controls to protect your data.
    Our systems have 99.9% availability and uptime.
    Confidential information is encrypted and access-controlled.
    We ensure processing accuracy and completeness.
    Privacy of personal information is maintained through strict policies.
    Authentication and authorization controls are enforced.
    """

    results = checker.check_compliance(
        document_text=soc2_policy,
        frameworks=[ComplianceFramework.SOC2]
    )

    assert results["overall_compliance_score"] > 60.0


def test_ccpa_compliance(checker):
    """Test CCPA compliance checking."""
    ccpa_policy = """
    CALIFORNIA PRIVACY RIGHTS

    We collect the following categories of personal information from consumers.
    You have the right to know what information we collect.
    You have the right to delete your personal information.
    You have the right to opt-out of the sale of your personal information.
    We will not discriminate against you for exercising your privacy rights.
    """

    results = checker.check_compliance(
        document_text=ccpa_policy,
        frameworks=[ComplianceFramework.CCPA]
    )

    assert results["overall_compliance_score"] > 70.0


def test_pci_dss_compliance(checker):
    """Test PCI DSS compliance checking."""
    pci_policy = """
    PAYMENT CARD DATA PROTECTION

    We protect all cardholder data with industry-standard security measures.
    All payment information is encrypted during transmission using TLS.
    Access to credit card data is strictly controlled on a need-to-know basis.
    We do not store full card numbers after authorization.
    """

    results = checker.check_compliance(
        document_text=pci_policy,
        frameworks=[ComplianceFramework.PCI_DSS]
    )

    assert results["overall_compliance_score"] > 60.0


def test_critical_issues_detection(checker):
    """Test detection of critical compliance issues."""
    risky_policy = "We collect and use your data however we want."

    results = checker.check_compliance(
        document_text=risky_policy,
        frameworks=[ComplianceFramework.GDPR]
    )

    issues = results["issues"]
    # Should have multiple issues
    assert len(issues) >= 5


def test_compliant_requirements_tracking(checker, gdpr_compliant_policy):
    """Test tracking of compliant requirements."""
    results = checker.check_compliance(
        document_text=gdpr_compliant_policy,
        frameworks=[ComplianceFramework.GDPR]
    )

    compliant = results["compliant_requirements"]
    assert len(compliant) > 0


def test_framework_specific_recommendations(checker):
    """Test framework-specific recommendations."""
    minimal_policy = "Privacy policy."

    results = checker.check_compliance(
        document_text=minimal_policy,
        frameworks=[ComplianceFramework.GDPR, ComplianceFramework.HIPAA]
    )

    recommendations = results["recommendations"]
    # Should have recommendations for both frameworks
    assert len(recommendations) > 0


@pytest.mark.parametrize("framework", [
    ComplianceFramework.GDPR,
    ComplianceFramework.HIPAA,
    ComplianceFramework.SOC2,
    ComplianceFramework.CCPA,
    ComplianceFramework.PCI_DSS,
    ComplianceFramework.ISO27001,
])
def test_all_frameworks_have_rules(checker, framework):
    """Test that all frameworks have defined rules."""
    assert framework in checker.compliance_rules
    rules = checker.compliance_rules[framework]
    assert "requirements" in rules
    assert len(rules["requirements"]) > 0


def test_detailed_vs_basic_analysis(checker, gdpr_compliant_policy):
    """Test detailed vs basic analysis."""
    detailed = checker.check_compliance(
        document_text=gdpr_compliant_policy,
        frameworks=[ComplianceFramework.GDPR],
        detailed_analysis=True
    )

    basic = checker.check_compliance(
        document_text=gdpr_compliant_policy,
        frameworks=[ComplianceFramework.GDPR],
        detailed_analysis=False
    )

    # Both should return results
    assert detailed["overall_compliance_score"] > 0
    assert basic["overall_compliance_score"] > 0


def test_empty_document(checker):
    """Test handling of empty document."""
    results = checker.check_compliance(
        document_text="",
        frameworks=[ComplianceFramework.GDPR]
    )

    # Should have very low compliance score
    assert results["overall_compliance_score"] < 20.0
    assert len(results["issues"]) > 0


def test_processing_time(checker, gdpr_compliant_policy):
    """Test that processing time is tracked."""
    results = checker.check_compliance(
        document_text=gdpr_compliant_policy,
        frameworks=[ComplianceFramework.GDPR]
    )

    assert "processing_time" in results
    assert results["processing_time"] > 0
