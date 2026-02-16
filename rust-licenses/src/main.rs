mod fingerprint;
mod license;

use base64::engine::general_purpose::STANDARD as BASE64;
use base64::Engine;
use chrono::Utc;
use clap::{Parser, Subcommand};
use ed25519_dalek::{SigningKey, VerifyingKey};
use rand::rngs::OsRng;
use std::fs;
use std::process;

use crate::fingerprint::generate_fingerprint;
use crate::license::{
    canonical_payload, sign_payload, validate_license, LicensePayload, SignedLicense,
};

// ---------------------------------------------------------------------------
// Embedded development public key (Ed25519, 32 bytes)
// Generated 2026-02-14 — DO NOT commit the corresponding private key.
// base64: 5s5Hj5t0FeSRhQC3BGdmmEj5voWyB1/PZeJdArj3NNQ=
// ---------------------------------------------------------------------------
pub const LICENSE_PUBKEY: [u8; 32] = [
    0xe6, 0xce, 0x47, 0x8f, 0x9b, 0x74, 0x15, 0xe4, 0x91, 0x85, 0x00, 0xb7, 0x04, 0x67, 0x66,
    0x98, 0x48, 0xf9, 0xbe, 0x85, 0xb2, 0x07, 0x5f, 0xcf, 0x65, 0xe2, 0x5d, 0x02, 0xb8, 0xf7,
    0x34, 0xd4,
];

// ───────────────────────────────────────── CLI ───────────────────────────

/// Rhinometric License Core — Ed25519 license tool
#[derive(Parser)]
#[command(name = "rhino-lic", version, about)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Generate a new Ed25519 keypair for license signing
    Keygen {
        /// Output directory for key files
        #[arg(short, long, default_value = ".")]
        output: String,
    },

    /// Show version, crypto info and machine fingerprint
    Info,

    /// Print only the machine fingerprint (sha256:<hex>)
    Fingerprint,

    /// Sign a license payload JSON file with a private key (low-level)
    Sign {
        /// Path to the payload JSON file
        #[arg(short = 'p', long)]
        payload: String,

        /// Path to the Ed25519 private key (base64 file)
        #[arg(short = 'k', long)]
        privkey: String,

        /// Output file (omit for stdout)
        #[arg(short = 'o', long)]
        output: Option<String>,
    },

    /// Issue a signed license from CLI parameters (issuer-side)
    Issue {
        /// Tenant identifier
        #[arg(long)]
        tenant_id: String,

        /// Customer display name
        #[arg(long)]
        customer: String,

        /// Plan name (e.g. starter, professional, enterprise)
        #[arg(long)]
        plan: String,

        /// Maximum number of monitored hosts
        #[arg(long)]
        max_hosts: u32,

        /// Expiration date in ISO 8601 / RFC 3339 (e.g. 2027-02-13T00:00:00Z)
        #[arg(long)]
        expires_at: String,

        /// Machine fingerprint of the target host (sha256:<hex>)
        #[arg(long)]
        fingerprint_value: String,

        /// Comma-separated feature list (e.g. monitoring,alerting)
        #[arg(long, default_value = "monitoring")]
        features: String,

        /// Path to the Ed25519 private key file (base64).
        /// Can also be set via RHINO_LICENSE_PRIVKEY_PATH env var.
        #[arg(long, env = "RHINO_LICENSE_PRIVKEY_PATH")]
        privkey: String,

        /// Output file path for the signed license JSON
        #[arg(long)]
        out: String,
    },

    /// Validate a signed license file against the embedded public key
    Validate {
        /// Path to the signed license JSON file
        file: String,

        /// Override: path to an Ed25519 public key file (base64).
        /// If omitted, the embedded development public key is used.
        #[arg(short = 'k', long)]
        pubkey: Option<String>,

        /// Skip the machine-fingerprint check
        #[arg(long, default_value_t = false)]
        skip_fingerprint: bool,
    },
}

// ───────────────────────────────────────── Helpers ────────────────────────

fn load_signing_key(path: &str) -> SigningKey {
    let b64 = fs::read_to_string(path).unwrap_or_else(|e| {
        eprintln!("Error reading private key {}: {}", path, e);
        process::exit(4);
    });

    let bytes = BASE64.decode(b64.trim()).unwrap_or_else(|e| {
        eprintln!("Invalid private key base64: {}", e);
        process::exit(4);
    });

    let arr: [u8; 32] = bytes.try_into().unwrap_or_else(|_| {
        eprintln!("Private key must be exactly 32 bytes");
        process::exit(4);
    });

    SigningKey::from_bytes(&arr)
}

fn load_verifying_key(path: &str) -> VerifyingKey {
    let b64 = fs::read_to_string(path).unwrap_or_else(|e| {
        eprintln!("Error reading public key {}: {}", path, e);
        process::exit(4);
    });

    let bytes = BASE64.decode(b64.trim()).unwrap_or_else(|e| {
        eprintln!("Invalid public key base64: {}", e);
        process::exit(4);
    });

    let arr: [u8; 32] = bytes.try_into().unwrap_or_else(|_| {
        eprintln!("Public key must be exactly 32 bytes");
        process::exit(4);
    });

    VerifyingKey::from_bytes(&arr).unwrap_or_else(|e| {
        eprintln!("Invalid Ed25519 public key: {}", e);
        process::exit(4);
    })
}

fn embedded_verifying_key() -> VerifyingKey {
    VerifyingKey::from_bytes(&LICENSE_PUBKEY).unwrap_or_else(|e| {
        eprintln!("BUG: embedded public key is invalid: {}", e);
        process::exit(4);
    })
}

// ───────────────────────────────────────── Subcommands ────────────────────

fn cmd_keygen(output_dir: &str) {
    let signing_key = SigningKey::generate(&mut OsRng);
    let verifying_key = signing_key.verifying_key();

    let priv_b64 = BASE64.encode(signing_key.to_bytes());
    let pub_b64 = BASE64.encode(verifying_key.to_bytes());

    let priv_path = format!("{}/license.key", output_dir);
    let pub_path = format!("{}/license.pub", output_dir);

    fs::write(&priv_path, &priv_b64).unwrap_or_else(|e| {
        eprintln!("Error writing {}: {}", priv_path, e);
        process::exit(1);
    });

    fs::write(&pub_path, &pub_b64).unwrap_or_else(|e| {
        eprintln!("Error writing {}: {}", pub_path, e);
        process::exit(1);
    });

    eprintln!("Keypair generated:");
    eprintln!("  Private key : {} (KEEP SECRET — do NOT commit)", priv_path);
    eprintln!("  Public  key : {}", pub_path);
    eprintln!();
    // Print the public key to stdout so it can be captured
    println!("{}", pub_b64);
}

fn cmd_info() {
    println!("rhino-lic v{}", env!("CARGO_PKG_VERSION"));
    println!("Crypto : Ed25519 (ed25519-dalek 2.x)");
    println!("Hash   : SHA-256 (sha2 0.10)");
    println!("Pubkey : {} (embedded)", BASE64.encode(LICENSE_PUBKEY));
    println!();
    match generate_fingerprint() {
        Ok(fp) => println!("Machine fingerprint: {}", fp),
        Err(e) => println!("Machine fingerprint: unavailable ({})", e),
    }
}

fn cmd_fingerprint() {
    match generate_fingerprint() {
        Ok(fp) => println!("{}", fp),
        Err(e) => {
            eprintln!("Error: {}", e);
            process::exit(1);
        }
    }
}

fn cmd_sign(payload_path: &str, privkey_path: &str, output_path: Option<&str>) {
    let payload_json = fs::read_to_string(payload_path).unwrap_or_else(|e| {
        eprintln!("Error reading payload file: {}", e);
        process::exit(4);
    });

    let payload: LicensePayload = serde_json::from_str(&payload_json).unwrap_or_else(|e| {
        eprintln!("Invalid payload JSON: {}", e);
        process::exit(4);
    });

    let signing_key = load_signing_key(privkey_path);
    let signature = sign_payload(&payload, &signing_key).unwrap_or_else(|e| {
        eprintln!("Signing failed: {}", e);
        process::exit(4);
    });

    let signed = serde_json::json!({
        "payload": payload,
        "signature": signature
    });

    let output_json = serde_json::to_string_pretty(&signed).unwrap();

    match output_path {
        Some(path) => {
            fs::write(path, &output_json).unwrap_or_else(|e| {
                eprintln!("Error writing output: {}", e);
                process::exit(4);
            });
            eprintln!("Signed license written to {}", path);
        }
        None => println!("{}", output_json),
    }
}

fn cmd_issue(
    tenant_id: &str,
    customer: &str,
    plan: &str,
    max_hosts: u32,
    expires_at: &str,
    fingerprint_value: &str,
    features: &str,
    privkey_path: &str,
    out_path: &str,
) {
    // Validate expires_at is parseable
    chrono::DateTime::parse_from_rfc3339(expires_at).unwrap_or_else(|e| {
        eprintln!("Invalid --expires-at (must be RFC 3339): {}", e);
        process::exit(4);
    });

    let feature_list: Vec<String> = features.split(',').map(|s| s.trim().to_string()).collect();

    let payload = LicensePayload {
        version: 1,
        tenant_id: tenant_id.to_string(),
        customer: customer.to_string(),
        plan: plan.to_string(),
        max_hosts,
        issued_at: Utc::now().to_rfc3339(),
        expires_at: expires_at.to_string(),
        fingerprint: fingerprint_value.to_string(),
        features: feature_list,
    };

    let signing_key = load_signing_key(privkey_path);
    let signature = sign_payload(&payload, &signing_key).unwrap_or_else(|e| {
        eprintln!("Signing failed: {}", e);
        process::exit(4);
    });

    let signed = SignedLicense {
        payload,
        signature,
    };

    let output_json = serde_json::to_string_pretty(&signed).unwrap();

    fs::write(out_path, &output_json).unwrap_or_else(|e| {
        eprintln!("Error writing {}: {}", out_path, e);
        process::exit(4);
    });

    eprintln!("License issued successfully:");
    eprintln!("  File    : {}", out_path);
    eprintln!("  Tenant  : {}", signed.payload.tenant_id);
    eprintln!("  Customer: {}", signed.payload.customer);
    eprintln!("  Plan    : {}", signed.payload.plan);
    eprintln!("  Hosts   : {}", signed.payload.max_hosts);
    eprintln!("  Expires : {}", signed.payload.expires_at);
    eprintln!("  Fingerprint: {}", signed.payload.fingerprint);

    // Also print canonical payload hash for audit
    if let Ok(canonical) = canonical_payload(&signed.payload) {
        use sha2::{Digest, Sha256};
        let hash = Sha256::digest(canonical.as_bytes());
        let hex: String = hash.iter().map(|b| format!("{:02x}", b)).collect();
        eprintln!("  Payload SHA-256: {}", hex);
    }
}

fn cmd_validate(license_path: &str, pubkey_path: Option<&str>, skip_fingerprint: bool) {
    // 1. Read license file
    let license_json = fs::read_to_string(license_path).unwrap_or_else(|e| {
        let result = serde_json::json!({
            "status": "invalid",
            "reason": format!("Cannot read license file: {}", e)
        });
        println!("{}", serde_json::to_string_pretty(&result).unwrap());
        process::exit(4);
    });

    let license: SignedLicense = serde_json::from_str(&license_json).unwrap_or_else(|e| {
        let result = serde_json::json!({
            "status": "invalid",
            "reason": format!("Invalid license JSON: {}", e)
        });
        println!("{}", serde_json::to_string_pretty(&result).unwrap());
        process::exit(4);
    });

    // 2. Load verifying key: from file or embedded
    let verifying_key = match pubkey_path {
        Some(path) => load_verifying_key(path),
        None => embedded_verifying_key(),
    };

    // 3. Machine fingerprint
    let machine_fp = if skip_fingerprint {
        license.payload.fingerprint.clone()
    } else {
        generate_fingerprint().unwrap_or_else(|e| {
            let result = serde_json::json!({
                "status": "invalid",
                "reason": format!("Cannot compute machine fingerprint: {}", e)
            });
            println!("{}", serde_json::to_string_pretty(&result).unwrap());
            process::exit(4);
        })
    };

    // 4. Validate
    match validate_license(&license, &verifying_key, &machine_fp) {
        Ok(result) => {
            println!("{}", serde_json::to_string_pretty(&result).unwrap());
            process::exit(0);
        }
        Err(err) => {
            let code = err.exit_code();
            let result = serde_json::json!({
                "status": "invalid",
                "reason": err.reason()
            });
            println!("{}", serde_json::to_string_pretty(&result).unwrap());
            process::exit(code);
        }
    }
}

// ───────────────────────────────────────── main ──────────────────────────

fn main() {
    let cli = Cli::parse();

    match cli.command {
        Commands::Keygen { output } => cmd_keygen(&output),
        Commands::Info => cmd_info(),
        Commands::Fingerprint => cmd_fingerprint(),
        Commands::Sign {
            payload,
            privkey,
            output,
        } => cmd_sign(&payload, &privkey, output.as_deref()),
        Commands::Issue {
            tenant_id,
            customer,
            plan,
            max_hosts,
            expires_at,
            fingerprint_value,
            features,
            privkey,
            out,
        } => cmd_issue(
            &tenant_id,
            &customer,
            &plan,
            max_hosts,
            &expires_at,
            &fingerprint_value,
            &features,
            &privkey,
            &out,
        ),
        Commands::Validate {
            file,
            pubkey,
            skip_fingerprint,
        } => cmd_validate(&file, pubkey.as_deref(), skip_fingerprint),
    }
}
