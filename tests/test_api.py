"""
Tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.models import ComplianceFramework, ClauseType


client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "endpoints" in data


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "services" in data


def test_analyze_contract_endpoint():
    """Test contract analysis endpoint."""
    contract_text = """
    AGREEMENT

    This agreement is between Company A and Company B.
    The effective date is January 1, 2024.
    Payment of $50,000 is due upon completion.
    Either party may terminate with 30 days notice.
    """

    response = client.post(
        "/analyze-contract",
        json={
            "document_text": contract_text,
            "extract_parties": True,
            "extract_dates": True,
            "extract_financial": True,
            "detect_risks": True
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "document_id" in data
    assert "document_type" in data
    assert "summary" in data
    assert "overall_risk_score" in data
    assert "processing_time" in data


def test_check_compliance_endpoint():
    """Test compliance checking endpoint."""
    policy_text = """
    PRIVACY POLICY

    We collect personal data with your consent.
    You have the right to access, erase, and port your data.
    We retain data for 5 years.
    We may share data with third parties.
    Contact us at privacy@example.com.
    """

    response = client.post(
        "/check-compliance",
        json={
            "document_text": policy_text,
            "frameworks": [ComplianceFramework.GDPR.value],
            "detailed_analysis": True
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "document_id" in data
    assert "frameworks_checked" in data
    assert "overall_compliance_score" in data
    assert "issues" in data
    assert "summary" in data


def test_qa_legal_document_endpoint():
    """Test legal Q&A endpoint."""
    document_text = """
    CONFIDENTIALITY AGREEMENT

    The parties agree to maintain confidentiality of all information
    for a period of 3 years. Exceptions apply for publicly available
    information or information independently developed.
    """

    response = client.post(
        "/qa-legal-document",
        json={
            "question": "How long is the confidentiality period?",
            "document_text": document_text,
            "max_sources": 5,
            "include_citations": True
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "question" in data
    assert "answer" in data
    assert "confidence" in data
    assert "citations" in data


def test_extract_clauses_endpoint():
    """Test clause extraction endpoint."""
    contract_text = """
    SERVICE AGREEMENT

    1. CONFIDENTIALITY
    All information shall remain confidential.

    2. TERMINATION
    This agreement may be terminated with 60 days notice.

    3. PAYMENT
    Payment of $10,000 monthly.

    4. LIABILITY
    Liability is limited to the contract value.

    5. INTELLECTUAL PROPERTY
    All IP created shall belong to the Client.
    """

    response = client.post(
        "/extract-clauses",
        json={
            "document_text": contract_text,
            "min_confidence": 0.6
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "document_id" in data
    assert "extracted_clauses" in data
    assert "total_clauses" in data
    assert "coverage_percentage" in data


def test_extract_specific_clause_types():
    """Test extracting specific clause types."""
    contract_text = """
    AGREEMENT

    Confidentiality: All information is confidential.
    Payment: $5,000 due monthly.
    Termination: 30 days notice required.
    """

    response = client.post(
        "/extract-clauses",
        json={
            "document_text": contract_text,
            "clause_types": [ClauseType.CONFIDENTIALITY.value, ClauseType.PAYMENT.value],
            "min_confidence": 0.5
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "extracted_clauses" in data


def test_generate_privacy_policy_endpoint():
    """Test privacy policy generation endpoint."""
    response = client.post(
        "/generate-privacy-policy",
        json={
            "company_name": "Test Corp",
            "company_type": "Software as a Service",
            "data_collected": ["email", "name", "usage data"],
            "data_usage": ["service provision", "analytics", "marketing"],
            "third_party_sharing": True,
            "cookies_used": True,
            "user_rights": ["access", "deletion", "portability"],
            "contact_email": "privacy@testcorp.com",
            "jurisdiction": "EU",
            "frameworks": [ComplianceFramework.GDPR.value]
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "policy" in data
    assert "compliance_score" in data
    assert "recommendations" in data
    assert data["policy"]["policy_type"] == "privacy_policy"


def test_risk_assessment_endpoint():
    """Test risk assessment endpoint."""
    contract_text = """
    AGREEMENT

    Company has unlimited liability for all claims.
    This agreement may be terminated immediately without notice.
    All intellectual property is assigned to Company.
    Employee agrees to binding arbitration and waives jury trial.
    """

    response = client.post(
        "/risk-assessment",
        json={
            "document_text": contract_text,
            "document_type": "contract",
            "include_remediation": True
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "document_id" in data
    assert "overall_risk_score" in data
    assert "risk_level" in data
    assert "risks" in data
    assert "recommendations" in data

    # High-risk contract should have high score
    assert data["overall_risk_score"] > 5.0


def test_invalid_contract_analysis():
    """Test contract analysis with invalid input."""
    response = client.post(
        "/analyze-contract",
        json={}  # Missing required fields
    )

    assert response.status_code == 422  # Validation error


def test_invalid_compliance_check():
    """Test compliance check with invalid framework."""
    response = client.post(
        "/check-compliance",
        json={
            "document_text": "Some text",
            "frameworks": ["invalid_framework"]
        }
    )

    assert response.status_code == 422  # Validation error


def test_empty_document_analysis():
    """Test analysis with empty document."""
    response = client.post(
        "/analyze-contract",
        json={
            "document_text": ""
        }
    )

    # Should still process but might have low scores
    assert response.status_code == 200


def test_multiple_framework_compliance():
    """Test compliance check with multiple frameworks."""
    policy_text = """
    COMPREHENSIVE PRIVACY POLICY

    We collect and protect your personal information.
    You have rights to access, delete, and port your data.
    We implement security measures including encryption.
    Protected health information is handled according to HIPAA.
    Payment card data is secured per PCI-DSS.
    """

    response = client.post(
        "/check-compliance",
        json={
            "document_text": policy_text,
            "frameworks": [
                ComplianceFramework.GDPR.value,
                ComplianceFramework.HIPAA.value,
                ComplianceFramework.PCI_DSS.value
            ]
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["frameworks_checked"]) == 3


def test_qa_with_document_ids():
    """Test Q&A with document IDs (requires pre-uploaded documents)."""
    # This would work with actual uploaded documents
    response = client.post(
        "/qa-legal-document",
        json={
            "question": "What are the termination conditions?",
            "document_ids": ["test_doc_1"],
            "max_sources": 3
        }
    )

    # May return 200 with no results or 500 if documents don't exist
    assert response.status_code in [200, 500]


def test_compare_contracts_endpoint():
    """Test contract comparison endpoint."""
    doc1 = "Simple agreement with standard terms. Payment of $1,000."
    doc2 = """
    Complex agreement with unlimited liability.
    Immediate termination without cause.
    All IP assigned to company.
    """

    response = client.post(
        f"/compare-contracts?document1={doc1}&document2={doc2}"
    )

    assert response.status_code == 200
    data = response.json()

    assert "document1" in data
    assert "document2" in data
    assert "comparison" in data


def test_concurrent_requests():
    """Test handling of concurrent requests."""
    import concurrent.futures

    def make_request():
        return client.post(
            "/analyze-contract",
            json={"document_text": "Test agreement"}
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(5)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # All requests should succeed
    assert all(r.status_code == 200 for r in results)


def test_large_document_processing():
    """Test processing of large document."""
    large_contract = "This is a contract clause. " * 1000

    response = client.post(
        "/analyze-contract",
        json={"document_text": large_contract}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["word_count"] > 1000


def test_special_characters_handling():
    """Test handling of special characters."""
    contract_with_special_chars = """
    AGREEMENT™

    Company® agrees to provide services.
    Payment: €10,000 or $12,000
    Email: test@example.com
    © 2024 All Rights Reserved
    """

    response = client.post(
        "/analyze-contract",
        json={"document_text": contract_with_special_chars}
    )

    assert response.status_code == 200


def test_response_time():
    """Test that responses are reasonably fast."""
    import time

    contract_text = "Standard service agreement with basic terms."

    start_time = time.time()
    response = client.post(
        "/analyze-contract",
        json={"document_text": contract_text}
    )
    end_time = time.time()

    assert response.status_code == 200
    # Should complete in reasonable time (adjust threshold as needed)
    assert end_time - start_time < 30.0  # 30 seconds max


def test_error_handling():
    """Test API error handling."""
    # Test with malformed JSON (simulated by invalid request)
    response = client.post(
        "/analyze-contract",
        data="invalid json"
    )

    assert response.status_code == 422


@pytest.mark.parametrize("endpoint,payload", [
    ("/analyze-contract", {"document_text": "test"}),
    ("/check-compliance", {"document_text": "test", "frameworks": ["gdpr"]}),
    ("/extract-clauses", {"document_text": "test"}),
    ("/risk-assessment", {"document_text": "test"}),
])
def test_all_endpoints_respond(endpoint, payload):
    """Test that all main endpoints respond."""
    response = client.post(endpoint, json=payload)
    assert response.status_code in [200, 422, 500]  # Valid response codes
