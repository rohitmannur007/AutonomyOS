"""
AI Diagnosis Service.

Produces a structured diagnosis for a ticket: intent, free-text diagnosis,
confidence, a proposed action, and supporting evidence. This is intentionally
the ONLY place the "AI" speaks — it never decides autonomy. The autonomy
engine (autonomy_engine.py) is the sole authority on execution rights.

Default provider is a deterministic mock, keyed off ticket text, so the
whole product works with zero API keys. If OPENAI_API_KEY is present and
AI_PROVIDER=openai, an OpenAI-backed provider can be used instead — but it
is never required.
"""

import os
from dataclasses import dataclass
from typing import List

AI_PROVIDER = os.getenv("AI_PROVIDER", "mock")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


@dataclass
class DiagnosisResult:
    intent: str
    diagnosis_text: str
    confidence: float
    proposed_action: str
    evidence: List[str]


# Ordered list of intent profiles. First keyword match wins, so more specific
# patterns are listed before more general ones.
INTENT_PROFILES = [
    {
        "id": "ACCOUNT_LOCKOUT",
        "keywords": ["locked out", "lockout", "too many failed attempts", "account is locked", "account got locked"],
        "diagnosis": "Multiple failed login attempts triggered the directory's automatic lockout policy.",
        "confidence": 0.95,
        "proposed_action": "UNLOCK_ACCOUNT",
        "evidence": [
            "Five consecutive failed login attempts within a 10 minute window",
            "Lockout policy threshold matched exactly",
        ],
    },
    {
        "id": "MFA_RESET",
        "keywords": ["mfa", "authenticator app", "multi-factor", "lost my phone", "new phone", "lost their phone"],
        "diagnosis": "User has lost access to their registered MFA device and needs their multi-factor binding reset.",
        "confidence": 0.91,
        "proposed_action": "RESET_AUTH_SESSION",
        "evidence": [
            "Identity verified through secondary helpdesk channel",
            "Matches standard MFA device-change workflow",
        ],
    },
    {
        "id": "M365_AUTH_FAILURE",
        "keywords": ["authentication", "auth session", "sign-in loop", "keeps signing", "m365 auth", "re-authenticate", "keeps prompting", "session expired"],
        "diagnosis": "The user's Microsoft 365 authentication session appears to have expired after a recent password change, causing repeated sign-in prompts.",
        "confidence": 0.96,
        "proposed_action": "RESET_AUTH_SESSION",
        "evidence": [
            "Repeated authentication failures logged in the last hour",
            "Pattern matches known post-password-change session workflow",
        ],
    },
    {
        "id": "PASSWORD_RESET",
        "keywords": ["forgot my password", "password reset", "can't remember", "reset her password", "reset his password", "forgot password"],
        "diagnosis": "User is unable to recall their current password and requires a supervised reset.",
        "confidence": 0.93,
        "proposed_action": "RESET_PASSWORD",
        "evidence": [
            "User verified identity via helpdesk challenge questions",
            "No suspicious sign-in activity found on the account",
        ],
    },
    {
        "id": "PRIVILEGED_ACCESS_REQUEST",
        "keywords": ["administrator", "admin rights", "admin permissions", "elevate", "grant admin", "global admin"],
        "diagnosis": "Request to grant elevated administrative rights to a standard employee account.",
        "confidence": 0.89,
        "proposed_action": "GRANT_ADMIN_PERMISSION",
        "evidence": [
            "Requested role sits outside the employee's current permission tier",
            "Elevation requires manager and security sign-off",
        ],
    },
    {
        "id": "LICENSE_ASSIGNMENT",
        "keywords": ["license", "m365 e3", "microsoft 365 license", "needs a license"],
        "diagnosis": "User account is missing the Microsoft 365 license required for their role.",
        "confidence": 0.93,
        "proposed_action": "ASSIGN_M365_LICENSE",
        "evidence": [
            "Role in the HR system requires a standard M365 E3 license",
            "License pool currently has available seats",
        ],
    },
    {
        "id": "OFFBOARDING_DISABLE",
        "keywords": ["terminated", "last day", "offboard", "disable the account", "disable his account", "disable her account", "employment has ended", "no longer employed"],
        "diagnosis": "Employee's termination has been confirmed by HR and the account requires deactivation to prevent unauthorized access.",
        "confidence": 0.94,
        "proposed_action": "DISABLE_USER",
        "evidence": [
            "HR termination record confirmed for this employee",
            "Standard offboarding checklist workflow matched",
        ],
    },
    {
        "id": "DEVICE_ENROLLMENT",
        "keywords": ["new laptop", "enroll", "mdm", "new device", "enrollment"],
        "diagnosis": "New device requires enrollment into the managed device profile before it can access company resources.",
        "confidence": 0.90,
        "proposed_action": "INSTALL_SOFTWARE",
        "evidence": [
            "Device serial number matches the procurement record",
            "Standard onboarding enrollment profile available",
        ],
    },
    {
        "id": "ONBOARDING_PROVISION",
        "keywords": ["new hire", "onboarding", "new employee", "starts monday", "first day"],
        "diagnosis": "New hire requires standard account provisioning ahead of their start date.",
        "confidence": 0.92,
        "proposed_action": "ASSIGN_M365_LICENSE",
        "evidence": [
            "New-hire record confirmed in the HR system",
            "Role maps to the standard onboarding license bundle",
        ],
    },
    {
        "id": "SOFTWARE_INSTALL",
        "keywords": ["install", "needs access to", "new software", "application request", "software request"],
        "diagnosis": "User is requesting a standard, pre-approved business application from the software catalog.",
        "confidence": 0.90,
        "proposed_action": "INSTALL_SOFTWARE",
        "evidence": [
            "Application is on the pre-approved standard catalog",
            "No elevated system permissions required for install",
        ],
    },
    {
        "id": "FIREWALL_CHANGE",
        "keywords": ["firewall", "production network", "open a port", "network rule", "vpn gateway", "inbound rule"],
        "diagnosis": "Requested change would modify an inbound rule on a production network firewall.",
        "confidence": 0.88,
        "proposed_action": "UPDATE_FIREWALL_RULE",
        "evidence": [
            "Rule targets a production-tagged firewall zone",
            "Change affects external-facing traffic policy",
        ],
    },
    {
        "id": "AMBIGUOUS_LOW_CONFIDENCE",
        "keywords": ["intermittent", "sometimes happens", "not sure why", "random error", "hard to reproduce", "comes and goes"],
        "diagnosis": "Symptoms are intermittent and do not clearly match a single known workflow. Further investigation is recommended before any action is taken.",
        "confidence": 0.58,
        "proposed_action": "RESET_AUTH_SESSION",
        "evidence": [
            "Symptom pattern partially overlaps two known workflows",
            "Insufficient log signal to confirm a single root cause",
        ],
    },
]

DEFAULT_PROFILE = INTENT_PROFILES[-1]  # ambiguous / low-confidence fallback


def _mock_diagnose(text: str) -> DiagnosisResult:
    lowered = text.lower()
    for profile in INTENT_PROFILES:
        if any(kw in lowered for kw in profile["keywords"]):
            return DiagnosisResult(
                intent=profile["id"],
                diagnosis_text=profile["diagnosis"],
                confidence=profile["confidence"],
                proposed_action=profile["proposed_action"],
                evidence=list(profile["evidence"]),
            )
    return DiagnosisResult(
        intent=DEFAULT_PROFILE["id"],
        diagnosis_text=DEFAULT_PROFILE["diagnosis"],
        confidence=DEFAULT_PROFILE["confidence"],
        proposed_action=DEFAULT_PROFILE["proposed_action"],
        evidence=list(DEFAULT_PROFILE["evidence"]),
    )


def _openai_diagnose(text: str) -> DiagnosisResult:
    """Optional OpenAI-backed diagnosis. Only used if AI_PROVIDER=openai and
    OPENAI_API_KEY is set. Falls back to the mock provider on any error so
    the product never hard-fails because of a missing/invalid key."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        allowed_actions = [
            "RESET_AUTH_SESSION",
            "RESET_PASSWORD",
            "UNLOCK_ACCOUNT",
            "ASSIGN_M365_LICENSE",
            "GRANT_ADMIN_PERMISSION",
            "INSTALL_SOFTWARE",
            "DISABLE_USER",
            "UPDATE_FIREWALL_RULE",
        ]
        prompt = (
            "You are an MSP support diagnosis assistant. Given the ticket text, "
            "return ONLY a JSON object with keys: intent (string), diagnosis "
            f"(string), confidence (0-1 float), proposed_action (one of {allowed_actions}), "
            "evidence (array of 2 short strings). No other text.\n\nTicket:\n" + text
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        import json

        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        return DiagnosisResult(
            intent=data["intent"],
            diagnosis_text=data["diagnosis"],
            confidence=float(data["confidence"]),
            proposed_action=data["proposed_action"],
            evidence=list(data["evidence"]),
        )
    except Exception:
        return _mock_diagnose(text)


def diagnose(ticket_title: str, ticket_description: str) -> DiagnosisResult:
    text = f"{ticket_title}. {ticket_description}"
    if AI_PROVIDER == "openai" and OPENAI_API_KEY:
        return _openai_diagnose(text)
    return _mock_diagnose(text)
