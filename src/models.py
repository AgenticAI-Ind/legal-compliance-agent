"""
Pydantic models and database schemas for Legal & Compliance Agent.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks."""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    CCPA = "ccpa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"


class ClauseType(str, Enum):
    """Types of contract clauses."""
    CONFIDENTIALITY = "confidentiality"
    TERMINATION = "termination"
    PAYMENT = "payment"
    LIABILITY = "liability"
    INDEMNIFICATION = "indemnification"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    GOVERNING_LAW = "governing_law"
    DISPUTE_RESOLUTION = "dispute_resolution"
    WARRANTY = "warranty"
    FORCE_MAJEURE = "force_majeure"
    NON_COMPETE = "non_compete"
    DATA_PROTECTION = "data_protection"


class RiskLevel(str, Enum):
    """Risk severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DocumentType(str, Enum):
    """Types of legal documents."""
    CONTRACT = "contract"
    PRIVACY_POLICY = "privacy_policy"
    TERMS_OF_SERVICE = "terms_of_service"
    NDA = "nda"
    EMPLOYMENT_AGREEMENT = "employment_agreement"
    LICENSE_AGREEMENT = "license_agreement"
    GDPR_POLICY = "gdpr_policy"
    OTHER = "other"


# Request Models
class ContractAnalysisRequest(BaseModel):
    """Request model for contract analysis."""
    document_text: Optional[str] = Field(None, description="Raw text of the contract")
    document_url: Optional[str] = Field(None, description="URL to the contract document")
    extract_parties: bool = Field(True, description="Extract party information")
    extract_dates: bool = Field(True, description="Extract important dates")
    extract_financial: bool = Field(True, description="Extract financial terms")
    detect_risks: bool = Field(True, description="Detect potential legal risks")

    @validator('document_text', 'document_url')
    def validate_document_source(cls, v, values):
        """Ensure at least one document source is provided."""
        if not v and 'document_text' not in values and 'document_url' not in values:
            raise ValueError("Either document_text or document_url must be provided")
        return v


class ComplianceCheckRequest(BaseModel):
    """Request model for compliance checking."""
    document_text: str = Field(..., description="Document text to check")
    frameworks: List[ComplianceFramework] = Field(
        ...,
        description="Compliance frameworks to check against"
    )
    document_type: DocumentType = Field(
        DocumentType.OTHER,
        description="Type of document being checked"
    )
    detailed_analysis: bool = Field(
        True,
        description="Include detailed analysis and recommendations"
    )


class LegalQARequest(BaseModel):
    """Request model for legal document Q&A."""
    question: str = Field(..., min_length=3, description="Legal question to answer")
    document_text: Optional[str] = Field(None, description="Document context")
    document_ids: Optional[List[str]] = Field(
        None,
        description="IDs of previously uploaded documents to query"
    )
    max_sources: int = Field(5, ge=1, le=20, description="Maximum number of sources")
    include_citations: bool = Field(True, description="Include source citations")


class ClauseExtractionRequest(BaseModel):
    """Request model for clause extraction."""
    document_text: str = Field(..., description="Contract text")
    clause_types: Optional[List[ClauseType]] = Field(
        None,
        description="Specific clause types to extract (None = all types)"
    )
    min_confidence: float = Field(
        0.6,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold"
    )


class PolicyGenerationRequest(BaseModel):
    """Request model for privacy policy generation."""
    company_name: str = Field(..., min_length=1)
    company_type: str = Field(..., description="Type of business")
    data_collected: List[str] = Field(..., description="Types of data collected")
    data_usage: List[str] = Field(..., description="How data is used")
    third_party_sharing: bool = Field(False)
    cookies_used: bool = Field(True)
    user_rights: List[str] = Field(
        default_factory=lambda: ["access", "deletion", "portability"]
    )
    contact_email: str = Field(..., description="Contact email for privacy inquiries")
    jurisdiction: str = Field("EU", description="Primary jurisdiction")
    frameworks: List[ComplianceFramework] = Field(
        default_factory=lambda: [ComplianceFramework.GDPR]
    )


class RiskAssessmentRequest(BaseModel):
    """Request model for legal risk assessment."""
    document_text: str = Field(..., description="Document to assess")
    document_type: DocumentType = Field(DocumentType.CONTRACT)
    risk_categories: Optional[List[str]] = Field(
        None,
        description="Specific risk categories to assess"
    )
    include_remediation: bool = Field(
        True,
        description="Include remediation suggestions"
    )


# Response Models
class ExtractedClause(BaseModel):
    """Model for an extracted clause."""
    clause_type: ClauseType
    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    start_position: int
    end_position: int
    key_terms: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)


class LegalRisk(BaseModel):
    """Model for a legal risk."""
    risk_id: str
    risk_level: RiskLevel
    category: str
    description: str
    affected_clause: Optional[str] = None
    recommendation: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class ContractParty(BaseModel):
    """Model for a contract party."""
    name: str
    role: str  # e.g., "vendor", "client", "employee"
    contact_info: Optional[Dict[str, str]] = None


class FinancialTerm(BaseModel):
    """Model for financial terms."""
    amount: Optional[float] = None
    currency: str = "USD"
    frequency: Optional[str] = None  # e.g., "monthly", "one-time"
    description: str
    conditions: Optional[str] = None


class ContractAnalysisResponse(BaseModel):
    """Response model for contract analysis."""
    document_id: str
    document_type: DocumentType
    summary: str
    parties: List[ContractParty] = Field(default_factory=list)
    key_dates: Dict[str, str] = Field(default_factory=dict)
    financial_terms: List[FinancialTerm] = Field(default_factory=list)
    extracted_clauses: List[ExtractedClause] = Field(default_factory=list)
    risks: List[LegalRisk] = Field(default_factory=list)
    overall_risk_score: float = Field(..., ge=0.0, le=10.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time: float


class ComplianceIssue(BaseModel):
    """Model for a compliance issue."""
    issue_id: str
    framework: ComplianceFramework
    severity: RiskLevel
    requirement: str
    current_status: str  # "compliant", "non-compliant", "partial", "unknown"
    description: str
    evidence: Optional[str] = None
    recommendation: str
    regulation_reference: Optional[str] = None


class ComplianceCheckResponse(BaseModel):
    """Response model for compliance checking."""
    document_id: str
    frameworks_checked: List[ComplianceFramework]
    overall_compliance_score: float = Field(..., ge=0.0, le=100.0)
    issues: List[ComplianceIssue] = Field(default_factory=list)
    compliant_requirements: List[str] = Field(default_factory=list)
    summary: str
    recommendations: List[str] = Field(default_factory=list)
    processing_time: float


class SourceCitation(BaseModel):
    """Model for a source citation."""
    document_id: str
    document_name: str
    excerpt: str
    page_number: Optional[int] = None
    relevance_score: float = Field(..., ge=0.0, le=1.0)


class LegalQAResponse(BaseModel):
    """Response model for legal Q&A."""
    question: str
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    citations: List[SourceCitation] = Field(default_factory=list)
    related_questions: List[str] = Field(default_factory=list)
    disclaimer: str = Field(
        default="This response is for informational purposes only and does not "
                "constitute legal advice. Consult a qualified attorney for legal matters."
    )
    processing_time: float


class ClauseExtractionResponse(BaseModel):
    """Response model for clause extraction."""
    document_id: str
    extracted_clauses: List[ExtractedClause]
    total_clauses: int
    coverage_percentage: float = Field(..., ge=0.0, le=100.0)
    processing_time: float


class GeneratedPolicy(BaseModel):
    """Model for a generated policy document."""
    policy_id: str
    policy_type: str
    content: str
    sections: Dict[str, str] = Field(default_factory=dict)
    compliance_frameworks: List[ComplianceFramework]
    last_updated: datetime
    version: str = "1.0"


class PolicyGenerationResponse(BaseModel):
    """Response model for policy generation."""
    policy: GeneratedPolicy
    compliance_score: float = Field(..., ge=0.0, le=100.0)
    recommendations: List[str] = Field(default_factory=list)
    processing_time: float


class RiskAssessmentResponse(BaseModel):
    """Response model for risk assessment."""
    document_id: str
    overall_risk_score: float = Field(..., ge=0.0, le=10.0)
    risk_level: RiskLevel
    risks: List[LegalRisk]
    risk_distribution: Dict[RiskLevel, int] = Field(default_factory=dict)
    key_concerns: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    processing_time: float


# Database Models
class DocumentRecord(Base):
    """Database model for stored documents."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), unique=True, index=True, nullable=False)
    document_type = Column(String(50), nullable=False)
    title = Column(String(500))
    content_hash = Column(String(64), index=True)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnalysisRecord(Base):
    """Database model for analysis results."""
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String(255), unique=True, index=True, nullable=False)
    document_id = Column(String(255), index=True, nullable=False)
    analysis_type = Column(String(50), nullable=False)
    results = Column(JSON, nullable=False)
    risk_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class ComplianceCheckRecord(Base):
    """Database model for compliance checks."""
    __tablename__ = "compliance_checks"

    id = Column(Integer, primary_key=True, index=True)
    check_id = Column(String(255), unique=True, index=True, nullable=False)
    document_id = Column(String(255), index=True, nullable=False)
    framework = Column(String(50), nullable=False)
    compliance_score = Column(Float, nullable=False)
    issues = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class ClauseRecord(Base):
    """Database model for extracted clauses."""
    __tablename__ = "clauses"

    id = Column(Integer, primary_key=True, index=True)
    clause_id = Column(String(255), unique=True, index=True, nullable=False)
    document_id = Column(String(255), index=True, nullable=False)
    clause_type = Column(String(50), nullable=False)
    text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    start_position = Column(Integer)
    end_position = Column(Integer)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class RiskRecord(Base):
    """Database model for identified risks."""
    __tablename__ = "risks"

    id = Column(Integer, primary_key=True, index=True)
    risk_id = Column(String(255), unique=True, index=True, nullable=False)
    document_id = Column(String(255), index=True, nullable=False)
    analysis_id = Column(String(255), index=True)
    risk_level = Column(String(20), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    recommendation = Column(Text)
    confidence = Column(Float, nullable=False)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Health Check Model
class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, bool] = Field(default_factory=dict)
