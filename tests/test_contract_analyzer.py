"""
Tests for contract analyzer.
"""

import pytest
from src.contract_analyzer import ContractAnalyzer
from src.models import RiskLevel


@pytest.fixture
def analyzer():
    """Create contract analyzer instance."""
    return ContractAnalyzer()


@pytest.fixture
def sample_contract():
    """Sample contract text for testing."""
    return """
    EMPLOYMENT AGREEMENT

    This Employment Agreement ("Agreement") is entered into as of January 1, 2024,
    between Tech Corp ("Company") and John Doe ("Employee").

    1. POSITION AND DUTIES
    Employee agrees to serve as Software Engineer.

    2. COMPENSATION
    Company shall pay Employee a salary of $120,000 per year, payable monthly.

    3. TERMINATION
    This Agreement may be terminated by either party at will, with or without cause,
    upon 30 days written notice.

    4. CONFIDENTIALITY
    Employee agrees to maintain confidentiality of all proprietary information
    for a period of 5 years following termination.

    5. INTELLECTUAL PROPERTY
    All work product and inventions created by Employee shall be work for hire
    and shall belong to the Company.

    6. GOVERNING LAW
    This Agreement shall be governed by the laws of the State of California.
    """


def test_analyzer_initialization(analyzer):
    """Test analyzer initializes correctly."""
    assert analyzer is not None
    assert analyzer.nlp is not None
    assert analyzer.matcher is not None


def test_analyze_contract_basic(analyzer, sample_contract):
    """Test basic contract analysis."""
    results = analyzer.analyze_contract(sample_contract)

    assert "document_hash" in results
    assert "summary" in results
    assert "overall_risk_score" in results
    assert "processing_time" in results
    assert results["word_count"] > 0


def test_extract_parties(analyzer, sample_contract):
    """Test party extraction."""
    results = analyzer.analyze_contract(
        sample_contract,
        extract_parties=True
    )

    parties = results.get("parties", [])
    assert len(parties) >= 1

    # Check for company and employee
    party_names = [p.name for p in parties]
    assert any("Tech Corp" in name or "Company" in name for name in party_names)


def test_extract_dates(analyzer, sample_contract):
    """Test date extraction."""
    results = analyzer.analyze_contract(
        sample_contract,
        extract_dates=True
    )

    dates = results.get("key_dates", {})
    # Should extract the January 1, 2024 date
    assert len(dates) > 0


def test_extract_financial_terms(analyzer, sample_contract):
    """Test financial term extraction."""
    results = analyzer.analyze_contract(
        sample_contract,
        extract_financial=True
    )

    financial_terms = results.get("financial_terms", [])
    assert len(financial_terms) > 0

    # Check for salary
    amounts = [term.amount for term in financial_terms]
    assert 120000.0 in amounts


def test_detect_risks(analyzer, sample_contract):
    """Test risk detection."""
    results = analyzer.analyze_contract(
        sample_contract,
        detect_risks=True
    )

    risks = results.get("risks", [])
    assert len(risks) > 0

    # Should detect at-will termination and work for hire risks
    risk_descriptions = [r.description.lower() for r in risks]
    assert any("terminat" in desc for desc in risk_descriptions)


def test_risk_score_calculation(analyzer, sample_contract):
    """Test risk score calculation."""
    results = analyzer.analyze_contract(sample_contract, detect_risks=True)

    risk_score = results["overall_risk_score"]
    assert 0.0 <= risk_score <= 10.0


def test_analyze_with_no_risks():
    """Test analysis of low-risk contract."""
    analyzer = ContractAnalyzer()

    safe_contract = """
    SERVICE AGREEMENT

    This agreement outlines the services to be provided.

    1. Services will be delivered by March 1, 2024.
    2. Payment of $5,000 upon completion.
    3. Either party may terminate with 90 days notice.
    4. Liability is limited to the contract value.
    5. Disputes will be resolved through good faith negotiation.
    """

    results = analyzer.analyze_contract(safe_contract, detect_risks=True)

    # Should have lower risk score
    assert results["overall_risk_score"] < 5.0


def test_high_risk_contract():
    """Test analysis of high-risk contract."""
    analyzer = ContractAnalyzer()

    risky_contract = """
    AGREEMENT

    1. The Company has unlimited liability for all claims and damages.
    2. This agreement may be terminated immediately without notice.
    3. All intellectual property, past, present and future, is assigned to Company.
    4. Employee will indemnify Company for any and all claims.
    5. Non-compete applies worldwide for 10 years.
    6. Payment is at the sole discretion of Company.
    """

    results = analyzer.analyze_contract(risky_contract, detect_risks=True)

    # Should have high risk score
    assert results["overall_risk_score"] > 5.0

    # Should detect multiple high/critical risks
    high_risks = [r for r in results["risks"] if r.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
    assert len(high_risks) >= 2


def test_summary_generation(analyzer, sample_contract):
    """Test contract summary generation."""
    results = analyzer.analyze_contract(sample_contract)

    summary = results["summary"]
    assert len(summary) > 0
    assert len(summary) <= 500  # Should be limited


def test_missing_clause_detection(analyzer):
    """Test detection of missing clauses."""
    minimal_contract = """
    Simple agreement between parties.
    Payment of $1,000.
    """

    results = analyzer.analyze_contract(minimal_contract, detect_risks=True)

    risks = results.get("risks", [])
    # Should detect missing clauses
    missing_risks = [r for r in risks if "missing" in r.description.lower()]
    assert len(missing_risks) > 0


def test_hash_content(analyzer):
    """Test content hashing."""
    text1 = "Sample contract text"
    text2 = "Sample contract text"
    text3 = "Different contract text"

    hash1 = analyzer._hash_content(text1)
    hash2 = analyzer._hash_content(text2)
    hash3 = analyzer._hash_content(text3)

    assert hash1 == hash2  # Same content
    assert hash1 != hash3  # Different content
    assert len(hash1) == 64  # SHA-256 hex length


def test_empty_contract():
    """Test handling of empty contract."""
    analyzer = ContractAnalyzer()

    results = analyzer.analyze_contract("")

    assert results["word_count"] == 0
    assert results["overall_risk_score"] >= 0


def test_very_long_contract(analyzer):
    """Test handling of very long contract."""
    long_contract = "This is a contract. " * 10000

    results = analyzer.analyze_contract(long_contract)

    assert results["word_count"] > 10000
    assert "processing_time" in results


@pytest.mark.parametrize("extract_parties,extract_dates,extract_financial,detect_risks", [
    (True, True, True, True),
    (False, False, False, False),
    (True, False, True, False),
    (False, True, False, True),
])
def test_selective_extraction(analyzer, sample_contract, extract_parties, extract_dates, extract_financial, detect_risks):
    """Test selective feature extraction."""
    results = analyzer.analyze_contract(
        sample_contract,
        extract_parties=extract_parties,
        extract_dates=extract_dates,
        extract_financial=extract_financial,
        detect_risks=detect_risks
    )

    if extract_parties:
        assert "parties" in results

    if extract_dates:
        assert "key_dates" in results

    if extract_financial:
        assert "financial_terms" in results

    if detect_risks:
        assert "risks" in results
