use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

/// Virtual interface prefixes to EXCLUDE from fingerprint calculation.
/// These interfaces have random MACs that change on Docker/bridge recreation.
const VIRTUAL_PREFIXES: &[&str] = &[
    "docker", "br-", "veth", "virbr", "vnet", "tun", "tap", "wg",
    "flannel", "cni", "calico", "weave",
];

/// Generate a machine fingerprint from /etc/machine-id + primary physical MAC.
/// Returns `sha256:<64-char hex>`.
///
/// Only physical interfaces (eth*, en*, ens*, eno*, bond*) are considered.
/// Docker bridges and virtual interfaces are excluded for stability.
pub fn generate_fingerprint() -> Result<String, String> {
    let machine_id = read_machine_id()?;
    let mac = get_primary_mac()?;

    let mut hasher = Sha256::new();
    hasher.update(machine_id.as_bytes());
    hasher.update(b":");
    hasher.update(mac.as_bytes());
    let hash = hasher.finalize();

    let hex: String = hash.iter().map(|b| format!("{:02x}", b)).collect();
    Ok(format!("sha256:{}", hex))
}

fn read_machine_id() -> Result<String, String> {
    let path = "/etc/machine-id";
    fs::read_to_string(path)
        .map(|s| s.trim().to_string())
        .map_err(|e| format!("Cannot read {}: {}", path, e))
}

fn is_virtual(name: &str) -> bool {
    VIRTUAL_PREFIXES.iter().any(|prefix| name.starts_with(prefix))
}

fn get_primary_mac() -> Result<String, String> {
    let net_dir = Path::new("/sys/class/net");
    if !net_dir.exists() {
        return Err("/sys/class/net not found".to_string());
    }

    let mut entries: Vec<String> = fs::read_dir(net_dir)
        .map_err(|e| format!("Cannot read /sys/class/net: {}", e))?
        .filter_map(|e| e.ok())
        .map(|e| e.file_name().to_string_lossy().to_string())
        .filter(|name| name != "lo" && !is_virtual(name))
        .collect();

    entries.sort(); // deterministic order

    for iface in &entries {
        let mac_path = format!("/sys/class/net/{}/address", iface);
        if let Ok(mac) = fs::read_to_string(&mac_path) {
            let mac = mac.trim().to_lowercase();
            if !mac.is_empty() && mac != "00:00:00:00:00:00" {
                return Ok(mac);
            }
        }
    }

    Err("No physical network interface with valid MAC found".to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fingerprint_has_sha256_prefix() {
        if Path::new("/etc/machine-id").exists() {
            let fp = generate_fingerprint().unwrap();
            assert!(fp.starts_with("sha256:"));
            assert_eq!(fp.len(), 7 + 64); // "sha256:" + 64 hex chars
        }
    }

    #[test]
    fn virtual_interfaces_excluded() {
        assert!(is_virtual("docker0"));
        assert!(is_virtual("br-abc123"));
        assert!(is_virtual("veth1234"));
        assert!(is_virtual("virbr0"));
        assert!(!is_virtual("eth0"));
        assert!(!is_virtual("ens3"));
        assert!(!is_virtual("enp0s3"));
    }
}
