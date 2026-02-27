use base64::engine::general_purpose::STANDARD as BASE64;
use base64::Engine;
use ed25519_dalek::{Signature, VerifyingKey, Verifier};
use serde::{Deserialize, Serialize};
use std::fmt;

// -- Data structures --

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LicensePayload {
    pub version: u32,
    pub tenant_id: String,
    pub customer: String,
    pub plan: String,
    pub max_hosts: u32,
    pub issued_at: String,
    pub expires_at: String,
    pub fingerprint: String,
    #[serde(default)]
    pub features: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SignedLicense {
    pub payload: LicensePayload,
    pub signature: String,
}

#[derive(Debug, Serialize)]
pub struct ValidationResult {
    pub status: String,
    pub plan: String,
    pub max_hosts: u32,
    pub expires_at: String,
    pub tenant_id: String,
    pub customer: String,
}

// -- Error type --

#[derive(Debug)]
pub enum LicenseError {
    InvalidSignature(String),
    Expired(String),
    FingerprintMismatch(String),
    ParseError(String),
}

impl LicenseError {
    pub fn exit_code(&self) -> i32 {
        match self {
            LicenseError::InvalidSignature(_) => 1,
            LicenseError::Expired(_) => 2,
            LicenseError::FingerprintMismatch(_) => 3,
            LicenseError::ParseError(_) => 4,
        }
    }
    pub fn reason(&self) -> String {
        match self {
            LicenseError::InvalidSignature(s) => s.clone(),
            LicenseError::Expired(s) => s.clone(),
            LicenseError::FingerprintMismatch(s) => s.clone(),
            LicenseError::ParseError(s) => s.clone(),
        }
    }
}

impl fmt::Display for LicenseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.reason())
    }
}

// -- Functions --

/// Produce a deterministic canonical JSON for the payload (for signing).
pub fn canonical_payload(payload: &LicensePayload) -> Result<String, String> {
    serde_json::to_string(payload).map_err(|e| format!("canonical_payload: {}", e))
}

/// Sign a payload with an Ed25519 signing key. Returns base64 signature.
pub fn sign_payload(
    payload: &LicensePayload,
    signing_key: &ed25519_dalek::SigningKey,
) -> Result<String, String> {
    use ed25519_dalek::Signer;
    let canonical = canonical_payload(payload)?;
    let signature = signing_key.sign(canonical.as_bytes());
    Ok(BASE64.encode(signature.to_bytes()))
}

/// Validate a signed license against a public key and (optionally) a machine fingerprint.
pub fn validate_license(
    license: &SignedLicense,
    verifying_key: &VerifyingKey,
    machine_fingerprint: &str,
) -> Result<ValidationResult, LicenseError> {
    // 1. Verify Ed25519 signature
    let canonical = canonical_payload(&license.payload)
        .map_err(|e| LicenseError::ParseError(e))?;

    let sig_bytes = BASE64
        .decode(&license.signature)
        .map_err(|e| LicenseError::ParseError(format!("bad base64 signature: {}", e)))?;

    let signature = Signature::from_slice(&sig_bytes)
        .map_err(|e| LicenseError::InvalidSignature(format!("malformed signature: {}", e)))?;

    verifying_key
        .verify(canonical.as_bytes(), &signature)
        .map_err(|_| LicenseError::InvalidSignature("Ed25519 signature verification failed".into()))?;

    // 2. Check expiry
    if let Ok(expires) = chrono::DateTime::parse_from_rfc3339(&license.payload.expires_at) {
        if expires < chrono::Utc::now() {
            return Err(LicenseError::Expired(format!(
                "License expired on {}",
                license.payload.expires_at
            )));
        }
    }

    // 3. Check fingerprint (empty machine_fingerprint means skip)
    if !machine_fingerprint.is_empty()
        && !license.payload.fingerprint.is_empty()
        && license.payload.fingerprint != "any"
        && license.payload.fingerprint != machine_fingerprint
    {
        return Err(LicenseError::FingerprintMismatch(format!(
            "expected {} got {}",
            license.payload.fingerprint, machine_fingerprint
        )));
    }

    Ok(ValidationResult {
        status: "valid".into(),
        plan: license.payload.plan.clone(),
        max_hosts: license.payload.max_hosts,
        expires_at: license.payload.expires_at.clone(),
        tenant_id: license.payload.tenant_id.clone(),
        customer: license.payload.customer.clone(),
    })
}
