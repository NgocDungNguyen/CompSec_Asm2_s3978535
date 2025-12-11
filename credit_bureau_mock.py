"""
RMIT NeoBank - Mock Credit Bureau Integration

This module simulates integration with an external credit bureau (e.g., CIC, Experian).

Educational Purpose:
Demonstrates how banking systems integrate with third-party data providers
for credit risk assessment. In real implementations, this would involve:
- Secure API calls over HTTPS with mutual TLS
- Digital signatures and encryption
- Rate limiting and caching
- Error handling and retry logic
- Compliance with data protection regulations

Real-World Context (Banking Loan Origination):
When a loan application reaches the credit assessment stage, banks query
credit bureaus to obtain:
1. Credit score (FICO, VantageScore, or local equivalent)
2. Credit history (past loans, repayment behavior, defaults)
3. Outstanding debt and credit utilization
4. Public records (bankruptcies, liens, judgments)

This data drives automated decisioning rules, e.g.:
- Score >= 750: Auto-approve up to certain limit
- 650-749: Manual review required
- < 650: Auto-reject or require collateral

Security Considerations for External Integrations:
- STRIDE Threat: Tampering (validate response signatures)
- STRIDE Threat: Information Disclosure (encrypt sensitive PII in transit)
- STRIDE Threat: Denial of Service (rate limiting, circuit breaker pattern)
- Audit logging (regulatory requirement for credit checks)
"""

import random
from datetime import datetime


def perform_credit_check(applicant_name: str, national_id: str, dob) -> dict:
    """
    Mock implementation of a credit bureau API call.

    In a real banking system, this function would:

    1. **Construct Signed Request:**
       - API credentials (OAuth2 token or API key)
       - Request payload with applicant PII (encrypted)
       - Digital signature (HMAC-SHA256 or RSA)
       - Timestamp and nonce (prevent replay attacks)

    2. **Make HTTPS API Call:**
       - POST to bureau endpoint (e.g., https://api.cic.vn/creditreport)
       - Mutual TLS (client certificate authentication)
       - Timeout configuration (e.g., 30 seconds)
       - Retry logic with exponential backoff

    3. **Parse and Validate Response:**
       - Verify response signature (detect tampering)
       - Parse XML/JSON response
       - Extract score, risk factors, trade lines
       - Handle errors (bureau unavailable, applicant not found)

    4. **Audit and Logging:**
       - Log request/response for compliance (regulatory requirement)
       - Store bureau reference ID for dispute resolution
       - Alert on suspicious patterns (rate limiting, unusual queries)

    5. **Cost Management:**
       - Each bureau query costs money (e.g., $1-5 per query)
       - Caching strategies to avoid duplicate queries
       - Rate limiting per user/branch to prevent abuse

    Security Best Practices (Real Implementation):
    - Encrypt PII in transit (TLS 1.3)
    - Encrypt PII at rest in logs
    - Implement circuit breaker (if bureau is down, fail gracefully)
    - Rate limiting (prevent abuse, control costs)
    - Input validation (prevent injection into bureau request)
    - Output validation (detect malicious/malformed responses)

    Regulatory Compliance:
    - Fair Credit Reporting Act (FCRA) in USA
    - GDPR in Europe (explicit consent, right to access)
    - Basel III (credit risk management standards)
    - PCI DSS (if handling payment card data)

    Args:
        applicant_name: Full name of loan applicant
        national_id: National ID / SSN (PII - handle securely)
        dob: Date of birth (for identity verification)

    Returns:
        Dictionary containing:
        - bureau_reference: Unique reference ID from bureau
        - score: Credit score (300-900 range, FICO-like)
        - risk_band: HIGH / MEDIUM / LOW (simplified risk categorization)
        - raw_response: Full bureau response (for audit trail)

    Example Real Bureau Response (simplified):
    {
        "bureau_reference": "CIC-VN-2024-123456789",
        "score": 720,
        "score_factors": [
            "Payment history: 98% on-time",
            "Credit utilization: 35%",
            "Credit age: 7 years",
            "Recent inquiries: 2 in last 6 months"
        ],
        "trade_lines": [
            {
                "creditor": "Bank ABC",
                "type": "Credit Card",
                "balance": 5000000,
                "status": "Current"
            },
            {
                "creditor": "Bank XYZ",
                "type": "Personal Loan",
                "balance": 50000000,
                "status": "30 days late"
            }
        ],
        "public_records": [],
        "inquiries": [
            {"date": "2024-11-15", "creditor": "Bank DEF"},
            {"date": "2024-10-20", "creditor": "Fintech GHI"}
        ]
    }
    """

    # MOCK IMPLEMENTATION: Generate random score
    # Real implementation would make HTTPS API call here
    score = random.randint(300, 900)

    # Derive risk band from score (simplified decisioning logic)
    # Real banks use more complex models with multiple factors
    if score >= 750:
        risk_band = "LOW"
        recommendation = "Strong creditworthiness. Approve up to standard limits."
    elif score >= 600:
        risk_band = "MEDIUM"
        recommendation = "Moderate risk. Manual review recommended. Consider reduced limit or collateral."
    else:
        risk_band = "HIGH"
        recommendation = (
            "High credit risk. Reject or require substantial collateral and guarantor."
        )

    # Generate mock bureau reference (format similar to real systems)
    bureau_reference = f"CIC-VN-{datetime.utcnow().strftime('%Y%m%d')}-{national_id}-{int(datetime.utcnow().timestamp())}"

    # Mock response payload (simulates what bureau would return)
    raw_response = f"""
    === CREDIT BUREAU REPORT ===
    Bureau: Credit Information Center (CIC) - Vietnam
    Report Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
    
    APPLICANT INFORMATION:
    Name: {applicant_name}
    National ID: {national_id}
    Date of Birth: {dob}
    
    CREDIT SCORE: {score} / 900
    Risk Band: {risk_band}
    
    SCORE FACTORS:
    - Payment History: {random.randint(70, 100)}% on-time
    - Credit Utilization: {random.randint(10, 80)}%
    - Credit Age: {random.randint(1, 15)} years
    - Recent Inquiries: {random.randint(0, 10)} in last 6 months
    - Total Accounts: {random.randint(1, 8)}
    
    RECOMMENDATION: {recommendation}
    
    DISCLAIMER: This is a simulated report for educational purposes.
    Real credit bureau reports contain detailed trade lines, payment history,
    public records, and inquiries.
    
    Bureau Reference: {bureau_reference}
    ===========================
    """

    # In production, also log this query for audit trail
    # logger.info(f"Credit check performed for {national_id}, score: {score}, ref: {bureau_reference}")

    return {
        "bureau_reference": bureau_reference,
        "score": score,
        "risk_band": risk_band,
        "raw_response": raw_response.strip(),
    }


def validate_bureau_response(response: dict) -> bool:
    """
    Validate credit bureau response to detect tampering or malformed data.

    Security Defense: STRIDE Threat - Tampering
    In real implementation, this would:
    - Verify digital signature (RSA or HMAC)
    - Check response structure against schema
    - Validate score range and other field constraints
    - Detect anomalies (e.g., score of 9999)

    Args:
        response: Dictionary containing bureau response

    Returns:
        True if response is valid, False otherwise
    """
    # Basic validation checks
    required_fields = ["bureau_reference", "score", "risk_band", "raw_response"]

    # Check all required fields present
    if not all(field in response for field in required_fields):
        return False

    # Validate score range
    score = response.get("score")
    if not isinstance(score, int) or not (300 <= score <= 900):
        return False

    # Validate risk band
    risk_band = response.get("risk_band")
    if risk_band not in ["LOW", "MEDIUM", "HIGH"]:
        return False

    # In production: also verify digital signature
    # signature_valid = verify_signature(
    #     data=response["raw_response"],
    #     signature=response.get("signature"),
    #     public_key=BUREAU_PUBLIC_KEY
    # )
    # if not signature_valid:
    #     return False

    return True


def get_decisioning_recommendation(score: int, requested_amount: float) -> dict:
    """
    Apply automated credit decisioning rules based on score and loan amount.

    Real Banking Context:
    Banks use complex decision engines with hundreds of rules, e.g.:
    - Score-based tiering
    - Debt-to-income ratio checks
    - Industry risk factors
    - Geopolitical risk adjustments
    - Internal behavior scoring (existing customer relationship)

    This is a simplified version for educational purposes.

    Args:
        score: Credit bureau score
        requested_amount: Loan amount requested by applicant

    Returns:
        Dictionary with decision, max_approved_amount, and conditions
    """
    # Example decision matrix (simplified)
    if score >= 800:
        return {
            "decision": "AUTO_APPROVE",
            "max_approved_amount": requested_amount * 1.2,  # Can offer more
            "conditions": [],
            "interest_rate_tier": "PRIME",
        }
    elif score >= 700:
        return {
            "decision": "AUTO_APPROVE",
            "max_approved_amount": requested_amount,
            "conditions": ["Standard terms"],
            "interest_rate_tier": "STANDARD",
        }
    elif score >= 600:
        return {
            "decision": "MANUAL_REVIEW",
            "max_approved_amount": requested_amount * 0.8,
            "conditions": [
                "Require additional documentation",
                "Employment verification",
            ],
            "interest_rate_tier": "SUBPRIME",
        }
    else:
        return {
            "decision": "AUTO_REJECT",
            "max_approved_amount": 0,
            "conditions": ["Credit score below minimum threshold"],
            "interest_rate_tier": "N/A",
        }
