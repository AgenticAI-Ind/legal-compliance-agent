"""
FastAPI application for Legal & Compliance Agent.
"""

import logging
import os
import uuid
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import PyPDF2
import io

from src.models import (
    ContractAnalysisRequest,
    ContractAnalysisResponse,
    ComplianceCheckRequest,
    ComplianceCheckResponse,
    LegalQARequest,
    LegalQAResponse,
    ClauseExtractionRequest,
    ClauseExtractionResponse,
    PolicyGenerationRequest,
    PolicyGenerationResponse,
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    HealthCheckResponse,
    DocumentType,
)
from src.database import get_db, init_db, get_db_manager
from src.contract_analyzer import ContractAnalyzer
from src.compliance_checker import ComplianceChecker
from src.legal_qa import LegalQASystem
from src.clause_extractor import ClauseExtractor
from src.policy_generator import PolicyGenerator
from src.risk_assessor import RiskAssessor


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    logger.info("Starting Legal & Compliance Agent API")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # Initialize components
    app.state.contract_analyzer = ContractAnalyzer()
    app.state.compliance_checker = ComplianceChecker()
    app.state.legal_qa = LegalQASystem()
    app.state.clause_extractor = ClauseExtractor()
    app.state.policy_generator = PolicyGenerator()
    app.state.risk_assessor = RiskAssessor()

    logger.info("All components initialized")

    yield

    # Cleanup
    logger.info("Shutting down Legal & Compliance Agent API")


# Create FastAPI app
app = FastAPI(
    title="Legal & Compliance Agent",
    description="AI-powered legal document analysis and compliance checking",
    version="1.0.0",
    lifespan=lifespan,
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check API health status."""
    db_manager = get_db_manager()
    db_healthy = db_manager.health_check()

    return HealthCheckResponse(
        status="healthy" if db_healthy else "degraded",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        services={
            "database": db_healthy,
            "contract_analyzer": True,
            "compliance_checker": True,
            "legal_qa": True,
        }
    )


# Contract Analysis Endpoint
@app.post("/analyze-contract", response_model=ContractAnalysisResponse)
async def analyze_contract(
    request: ContractAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Analyze a contract and extract key information.

    Extracts parties, dates, financial terms, clauses, and identifies risks.
    """
    logger.info("Received contract analysis request")

    try:
        # Get document text
        if request.document_text:
            document_text = request.document_text
        elif request.document_url:
            # In production, implement document fetching from URL
            raise HTTPException(
                status_code=501,
                detail="Document URL fetching not yet implemented"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either document_text or document_url must be provided"
            )

        # Analyze contract
        analyzer = app.state.contract_analyzer
        results = analyzer.analyze_contract(
            contract_text=document_text,
            extract_parties=request.extract_parties,
            extract_dates=request.extract_dates,
            extract_financial=request.extract_financial,
            detect_risks=request.detect_risks,
        )

        # Create response
        document_id = str(uuid.uuid4())

        response = ContractAnalysisResponse(
            document_id=document_id,
            document_type=DocumentType.CONTRACT,
            summary=results["summary"],
            parties=results.get("parties", []),
            key_dates=results.get("key_dates", {}),
            financial_terms=results.get("financial_terms", []),
            extracted_clauses=[],  # Populated by clause extractor if needed
            risks=results.get("risks", []),
            overall_risk_score=results["overall_risk_score"],
            metadata={
                "word_count": results.get("word_count", 0),
                "sentence_count": results.get("sentence_count", 0),
                "document_hash": results.get("document_hash", ""),
            },
            processing_time=results["processing_time"],
        )

        logger.info(f"Contract analysis completed: {document_id}")
        return response

    except Exception as e:
        logger.error(f"Error analyzing contract: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Compliance Checking Endpoint
@app.post("/check-compliance", response_model=ComplianceCheckResponse)
async def check_compliance(
    request: ComplianceCheckRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Check document for regulatory compliance.

    Supports GDPR, HIPAA, SOC2, CCPA, PCI-DSS, and ISO 27001.
    """
    logger.info(f"Received compliance check request for {len(request.frameworks)} frameworks")

    try:
        checker = app.state.compliance_checker

        results = checker.check_compliance(
            document_text=request.document_text,
            frameworks=request.frameworks,
            document_type=request.document_type,
            detailed_analysis=request.detailed_analysis,
        )

        document_id = str(uuid.uuid4())

        response = ComplianceCheckResponse(
            document_id=document_id,
            frameworks_checked=results["frameworks_checked"],
            overall_compliance_score=results["overall_compliance_score"],
            issues=results["issues"],
            compliant_requirements=results["compliant_requirements"],
            summary=results["summary"],
            recommendations=results["recommendations"],
            processing_time=results["processing_time"],
        )

        logger.info(
            f"Compliance check completed: {document_id}, "
            f"Score: {response.overall_compliance_score:.1f}%"
        )
        return response

    except Exception as e:
        logger.error(f"Error checking compliance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Legal Q&A Endpoint
@app.post("/qa-legal-document", response_model=LegalQAResponse)
async def qa_legal_document(
    request: LegalQARequest,
    db: Session = Depends(get_db),
):
    """
    RAG-based Q&A over legal documents.

    Ask questions about uploaded legal documents.
    """
    logger.info(f"Received legal Q&A request: {request.question[:50]}...")

    try:
        qa_system = app.state.legal_qa

        # If document text provided, add it temporarily
        if request.document_text:
            temp_doc_id = f"temp_{uuid.uuid4().hex[:8]}"
            qa_system.add_document(
                document_text=request.document_text,
                document_id=temp_doc_id,
                document_name="User provided document",
            )
            document_ids = [temp_doc_id]
        else:
            document_ids = request.document_ids

        # Query the system
        results = qa_system.query(
            question=request.question,
            document_ids=document_ids,
            max_sources=request.max_sources,
            include_citations=request.include_citations,
        )

        response = LegalQAResponse(
            question=results["question"],
            answer=results["answer"],
            confidence=results["confidence"],
            citations=results["citations"],
            related_questions=results["related_questions"],
            processing_time=results["processing_time"],
        )

        logger.info(f"Legal Q&A completed with confidence {response.confidence:.2f}")
        return response

    except Exception as e:
        logger.error(f"Error processing legal Q&A: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Clause Extraction Endpoint
@app.post("/extract-clauses", response_model=ClauseExtractionResponse)
async def extract_clauses(
    request: ClauseExtractionRequest,
    db: Session = Depends(get_db),
):
    """
    Extract and classify clauses from contracts.

    Identifies clause types like confidentiality, termination, payment, etc.
    """
    logger.info("Received clause extraction request")

    try:
        extractor = app.state.clause_extractor

        results = extractor.extract_clauses(
            contract_text=request.document_text,
            clause_types=request.clause_types,
            min_confidence=request.min_confidence,
        )

        document_id = str(uuid.uuid4())

        response = ClauseExtractionResponse(
            document_id=document_id,
            extracted_clauses=results["extracted_clauses"],
            total_clauses=results["total_clauses"],
            coverage_percentage=results["coverage_percentage"],
            processing_time=results["processing_time"],
        )

        logger.info(
            f"Clause extraction completed: {response.total_clauses} clauses, "
            f"{response.coverage_percentage:.1f}% coverage"
        )
        return response

    except Exception as e:
        logger.error(f"Error extracting clauses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Policy Generation Endpoint
@app.post("/generate-privacy-policy", response_model=PolicyGenerationResponse)
async def generate_privacy_policy(
    request: PolicyGenerationRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a privacy policy document.

    Creates GDPR/CCPA compliant privacy policies based on your requirements.
    """
    logger.info(f"Received policy generation request for {request.company_name}")

    try:
        generator = app.state.policy_generator

        results = generator.generate_privacy_policy(
            company_name=request.company_name,
            company_type=request.company_type,
            data_collected=request.data_collected,
            data_usage=request.data_usage,
            third_party_sharing=request.third_party_sharing,
            cookies_used=request.cookies_used,
            user_rights=request.user_rights,
            contact_email=request.contact_email,
            jurisdiction=request.jurisdiction,
            frameworks=request.frameworks,
        )

        response = PolicyGenerationResponse(
            policy=results["policy"],
            compliance_score=results["compliance_score"],
            recommendations=results["recommendations"],
            processing_time=results["processing_time"],
        )

        logger.info(
            f"Privacy policy generated: {response.policy.policy_id}, "
            f"Compliance: {response.compliance_score:.1f}%"
        )
        return response

    except Exception as e:
        logger.error(f"Error generating privacy policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Risk Assessment Endpoint
@app.post("/risk-assessment", response_model=RiskAssessmentResponse)
async def assess_risk(
    request: RiskAssessmentRequest,
    db: Session = Depends(get_db),
):
    """
    Perform comprehensive legal risk assessment.

    Identifies and scores legal risks in contracts and agreements.
    """
    logger.info("Received risk assessment request")

    try:
        assessor = app.state.risk_assessor

        results = assessor.assess_risks(
            document_text=request.document_text,
            document_type=request.document_type,
            risk_categories=request.risk_categories,
            include_remediation=request.include_remediation,
        )

        document_id = str(uuid.uuid4())

        response = RiskAssessmentResponse(
            document_id=document_id,
            overall_risk_score=results["overall_risk_score"],
            risk_level=results["risk_level"],
            risks=results["risks"],
            risk_distribution=results["risk_distribution"],
            key_concerns=results["key_concerns"],
            recommendations=results["recommendations"],
            processing_time=results["processing_time"],
        )

        logger.info(
            f"Risk assessment completed: {document_id}, "
            f"Risk score: {response.overall_risk_score}/10, "
            f"Level: {response.risk_level.value}"
        )
        return response

    except Exception as e:
        logger.error(f"Error assessing risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# File upload endpoint for PDFs
@app.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF document for processing.

    Extracts text from PDF and stores for later analysis.
    """
    logger.info(f"Received PDF upload: {file.filename}")

    try:
        # Read PDF
        content = await file.read()
        pdf_file = io.BytesIO(content)

        # Extract text
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF"
            )

        # Store document
        document_id = str(uuid.uuid4())
        qa_system = app.state.legal_qa

        qa_system.add_document(
            document_text=text,
            document_id=document_id,
            document_name=file.filename,
            metadata={
                "file_size": len(content),
                "page_count": len(pdf_reader.pages),
            }
        )

        logger.info(f"PDF processed successfully: {document_id}")

        return JSONResponse(
            content={
                "document_id": document_id,
                "filename": file.filename,
                "page_count": len(pdf_reader.pages),
                "text_length": len(text),
                "message": "PDF uploaded and processed successfully"
            }
        )

    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Utility endpoint: Compare two contracts
@app.post("/compare-contracts")
async def compare_contracts(
    document1: str,
    document2: str,
    db: Session = Depends(get_db),
):
    """Compare two contracts and highlight differences in risk profiles."""
    logger.info("Received contract comparison request")

    try:
        assessor = app.state.risk_assessor

        # Assess both documents
        results1 = assessor.assess_risks(document1)
        results2 = assessor.assess_risks(document2)

        # Compare risk profiles
        comparison = assessor.compare_risk_profiles(
            results1["risks"],
            results2["risks"]
        )

        return JSONResponse(
            content={
                "document1": {
                    "risk_score": results1["overall_risk_score"],
                    "risk_level": results1["risk_level"].value,
                    "risk_count": len(results1["risks"]),
                },
                "document2": {
                    "risk_score": results2["overall_risk_score"],
                    "risk_level": results2["risk_level"].value,
                    "risk_count": len(results2["risks"]),
                },
                "comparison": comparison,
            }
        )

    except Exception as e:
        logger.error(f"Error comparing contracts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Legal & Compliance Agent API",
        "version": "1.0.0",
        "description": "AI-powered legal document analysis and compliance checking",
        "endpoints": {
            "health": "/health",
            "analyze_contract": "/analyze-contract",
            "check_compliance": "/check-compliance",
            "qa_legal_document": "/qa-legal-document",
            "extract_clauses": "/extract-clauses",
            "generate_privacy_policy": "/generate-privacy-policy",
            "risk_assessment": "/risk-assessment",
            "upload_pdf": "/upload-pdf",
            "compare_contracts": "/compare-contracts",
        },
        "documentation": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT", "development") == "development",
    )
