# API Documentation

Complete API reference for the Legal & Compliance Agent.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API is open. To enable authentication, set `ENABLE_API_KEY_AUTH=true` in your environment and provide an API key in the `X-API-Key` header.

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/analyze-contract
```

## Rate Limiting

Default rate limits:
- 60 requests per minute per IP
- 1000 requests per hour per IP

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time when limit resets

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message",
  "status_code": 400,
  "error_type": "ValidationError"
}
```

Common status codes:
- `200`: Success
- `400`: Bad Request (validation error)
- `401`: Unauthorized (missing/invalid API key)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `422`: Unprocessable Entity (invalid input)
- `429`: Too Many Requests (rate limit exceeded)
- `500`: Internal Server Error

## Endpoints

### Health Check

Check API health and service status.

**GET** `/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": true,
    "contract_analyzer": true,
    "compliance_checker": true,
    "legal_qa": true
  }
}
```

### Root

Get API information and available endpoints.

**GET** `/`

**Response:**
```json
{
  "name": "Legal & Compliance Agent API",
  "version": "1.0.0",
  "description": "AI-powered legal document analysis and compliance checking",
  "endpoints": {
    "health": "/health",
    "analyze_contract": "/analyze-contract",
    ...
  },
  "documentation": "/docs"
}
```

### Analyze Contract

Analyze contracts and extract key information.

**POST** `/analyze-contract`

**Request Body:**
```json
{
  "document_text": "string (required)",
  "document_url": "string (optional)",
  "extract_parties": "boolean (default: true)",
  "extract_dates": "boolean (default: true)",
  "extract_financial": "boolean (default: true)",
  "detect_risks": "boolean (default: true)"
}
```

**Response:**
```json
{
  "document_id": "uuid",
  "document_type": "contract",
  "summary": "string",
  "parties": [
    {
      "name": "string",
      "role": "string",
      "contact_info": {}
    }
  ],
  "key_dates": {
    "effective_date": "string",
    "termination_date": "string"
  },
  "financial_terms": [
    {
      "amount": 0.0,
      "currency": "USD",
      "frequency": "string",
      "description": "string",
      "conditions": "string"
    }
  ],
  "extracted_clauses": [],
  "risks": [
    {
      "risk_id": "string",
      "risk_level": "high",
      "category": "string",
      "description": "string",
      "affected_clause": "string",
      "recommendation": "string",
      "confidence": 0.85
    }
  ],
  "overall_risk_score": 6.5,
  "metadata": {},
  "processing_time": 1.23
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/analyze-contract \
  -H "Content-Type: application/json" \
  -d '{
    "document_text": "CONTRACT TEXT...",
    "extract_parties": true,
    "detect_risks": true
  }'
```

### Check Compliance

Check documents for regulatory compliance.

**POST** `/check-compliance`

**Request Body:**
```json
{
  "document_text": "string (required)",
  "frameworks": ["gdpr", "hipaa", "soc2", "ccpa", "pci_dss", "iso27001"],
  "document_type": "privacy_policy" | "contract" | "terms_of_service" | "nda" | "other",
  "detailed_analysis": "boolean (default: true)"
}
```

**Response:**
```json
{
  "document_id": "uuid",
  "frameworks_checked": ["gdpr"],
  "overall_compliance_score": 78.5,
  "issues": [
    {
      "issue_id": "string",
      "framework": "gdpr",
      "severity": "high",
      "requirement": "string",
      "current_status": "non-compliant",
      "description": "string",
      "evidence": "string",
      "recommendation": "string",
      "regulation_reference": "Article 6"
    }
  ],
  "compliant_requirements": ["GDPR-3: Purpose Limitation"],
  "summary": "string",
  "recommendations": ["string"],
  "processing_time": 0.85
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/check-compliance \
  -H "Content-Type: application/json" \
  -d '{
    "document_text": "PRIVACY POLICY...",
    "frameworks": ["gdpr", "ccpa"],
    "detailed_analysis": true
  }'
```

### Legal Q&A

Ask questions about legal documents using RAG.

**POST** `/qa-legal-document`

**Request Body:**
```json
{
  "question": "string (required)",
  "document_text": "string (optional)",
  "document_ids": ["string"] (optional),
  "max_sources": "integer (default: 5)",
  "include_citations": "boolean (default: true)"
}
```

**Response:**
```json
{
  "question": "string",
  "answer": "string",
  "confidence": 0.92,
  "citations": [
    {
      "document_id": "string",
      "document_name": "string",
      "excerpt": "string",
      "page_number": 1,
      "relevance_score": 0.95
    }
  ],
  "related_questions": ["string"],
  "disclaimer": "string",
  "processing_time": 2.1
}
```

### Extract Clauses

Extract and classify contract clauses.

**POST** `/extract-clauses`

**Request Body:**
```json
{
  "document_text": "string (required)",
  "clause_types": [
    "confidentiality",
    "termination",
    "payment",
    "liability",
    "indemnification",
    "intellectual_property",
    "governing_law",
    "dispute_resolution",
    "warranty",
    "force_majeure",
    "non_compete",
    "data_protection"
  ] (optional),
  "min_confidence": "float (default: 0.6)"
}
```

**Response:**
```json
{
  "document_id": "uuid",
  "extracted_clauses": [
    {
      "clause_type": "confidentiality",
      "text": "string",
      "confidence": 0.89,
      "start_position": 1250,
      "end_position": 1450,
      "key_terms": ["string"],
      "risks": ["string"]
    }
  ],
  "total_clauses": 8,
  "coverage_percentage": 45.2,
  "processing_time": 0.67
}
```

### Generate Privacy Policy

Generate privacy policies compliant with regulations.

**POST** `/generate-privacy-policy`

**Request Body:**
```json
{
  "company_name": "string (required)",
  "company_type": "string (required)",
  "data_collected": ["string"] (required),
  "data_usage": ["string"] (required),
  "third_party_sharing": "boolean (required)",
  "cookies_used": "boolean (required)",
  "user_rights": ["access", "deletion", "portability"] (required),
  "contact_email": "string (required)",
  "jurisdiction": "string (default: EU)",
  "frameworks": ["gdpr", "ccpa"] (default: ["gdpr"])
}
```

**Response:**
```json
{
  "policy": {
    "policy_id": "uuid",
    "policy_type": "privacy_policy",
    "content": "string",
    "sections": {},
    "compliance_frameworks": ["gdpr"],
    "last_updated": "2024-01-15T10:30:00Z",
    "version": "1.0"
  },
  "compliance_score": 87.5,
  "recommendations": ["string"],
  "processing_time": 3.2
}
```

### Risk Assessment

Perform comprehensive legal risk assessment.

**POST** `/risk-assessment`

**Request Body:**
```json
{
  "document_text": "string (required)",
  "document_type": "contract" | "privacy_policy" | "terms_of_service" | "nda" | "employment_agreement" | "license_agreement" | "other",
  "risk_categories": ["string"] (optional),
  "include_remediation": "boolean (default: true)"
}
```

**Response:**
```json
{
  "document_id": "uuid",
  "overall_risk_score": 7.2,
  "risk_level": "high",
  "risks": [
    {
      "risk_id": "string",
      "risk_level": "critical",
      "category": "Liability",
      "description": "string",
      "affected_clause": "string",
      "recommendation": "string",
      "confidence": 0.91
    }
  ],
  "risk_distribution": {
    "critical": 1,
    "high": 3,
    "medium": 5,
    "low": 2
  },
  "key_concerns": ["string"],
  "recommendations": ["string"],
  "processing_time": 0.92
}
```

### Upload PDF

Upload and process PDF documents.

**POST** `/upload-pdf`

**Content-Type:** `multipart/form-data`

**Form Data:**
- `file`: PDF file (required)

**Response:**
```json
{
  "document_id": "uuid",
  "filename": "contract.pdf",
  "page_count": 10,
  "text_length": 5000,
  "message": "PDF uploaded and processed successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/upload-pdf \
  -F "file=@/path/to/contract.pdf"
```

### Compare Contracts

Compare two contracts and their risk profiles.

**POST** `/compare-contracts`

**Query Parameters:**
- `document1`: Text of first contract (required)
- `document2`: Text of second contract (required)

**Response:**
```json
{
  "document1": {
    "risk_score": 5.2,
    "risk_level": "medium",
    "risk_count": 8
  },
  "document2": {
    "risk_score": 7.8,
    "risk_level": "high",
    "risk_count": 12
  },
  "comparison": {
    "score_difference": 2.6,
    "lower_risk_document": "document1",
    "risk_categories_unique_to_doc1": ["string"],
    "risk_categories_unique_to_doc2": ["string"],
    "common_risk_categories": ["string"],
    "recommendation": "string"
  }
}
```

## WebSocket Support (Future)

Future versions will support WebSocket connections for real-time analysis.

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Analysis result:', data);
};

ws.send(JSON.stringify({
  action: 'analyze',
  document_text: 'CONTRACT TEXT...'
}));
```

## Pagination

For endpoints that return lists, use pagination parameters:

```
GET /api/documents?limit=50&offset=0
```

Parameters:
- `limit`: Number of results (default: 100, max: 500)
- `offset`: Starting position (default: 0)

Response includes pagination metadata:
```json
{
  "data": [],
  "pagination": {
    "total": 250,
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
}
```

## Best Practices

1. **Use appropriate timeouts**: Some analyses may take 30+ seconds
2. **Handle rate limits**: Implement exponential backoff
3. **Cache results**: Store analysis results when possible
4. **Batch requests**: Use batch endpoints for multiple documents
5. **Validate inputs**: Check document size before uploading
6. **Monitor usage**: Track API calls and costs
7. **Error handling**: Implement retry logic for transient errors
8. **Security**: Never expose API keys in client-side code
