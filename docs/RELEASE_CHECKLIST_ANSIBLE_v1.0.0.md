# Release Checklist v1.0.0 — Ansible Installer

**Objective:** Validate that the Ansible installer deploys Rhinometric reproducibly on a fresh VM and leaves evidence (logs/debug bundle) when something fails.

---

## 0) Pre-flight — Control Node (machine running Ansible)

- [ ] Ansible installed (>= 2.15 recommended).
- [ ] SSH access to target (ideally key-based) as a user with sudo.
- [ ] Inventory prepared (\nsible/inventories/<env>.ini\) with:
  \\\ini
  ansible_host=<IP>
  ansible_user=<user>
  ansible_ssh_private_key_file=<path>   # if applicable
  \\\

---

## 1) Pre-flight — Target VM (fresh)

- [ ] Ubuntu 24.04 (or the version supported by the playbook).
- [ ] Free ports: 80 (and internal ports used by the stack, routed through Nginx).
- [ ] Sufficient disk space (practical minimum: 30–40 GB free; ideally more).
- [ ] Acceptable RAM (document real threshold; if recommending 8 GB, flag warning if < 8).

---

## 2) Release Artifacts

- [ ] Correct tarball available (path/URL/sha256 documented):
  \\\
  rhinometric-vX.Y.Z.tar.gz
  \\\
- [ ] Ansible Installer version tagged:
  \\\
  Tag: ansible-installer-v1.0.0
  \\\
- [ ] Docs present:
  - \docs/ansible-installer.md\
  - \docs/RELEASE_CHECKLIST_ANSIBLE_v1.0.0.md\ (this checklist)

---

## 3) Deploy — Main Playbook

### Command

- [ ] Execute:
  \\\ash
  cd ansible
  ansible-playbook -i inventories/<env>.ini playbooks/deploy.yml
  \\\

### Success Criteria

- [ ] Docker installed/verified (no reinstall if already present).
- [ ] Docker Compose v2 operational.
- [ ] Files copied to \/opt/rhinometric\ (or the standard path).
- [ ] \.env\ generated/updated without exposing secrets in output.
- [ ] \docker compose up -d\ executed OK.
- [ ] No unexpected " changed\ on immediate re-run (basic idempotency):
 - [ ] Run \deploy.yml\ a second time and confirm it does not break or reconfigure unnecessarily.

---

## 4) Functional Validation — Validate Playbook

### Command

- [ ] Execute:
 \\\ash
 ansible-playbook -i inventories/<env>.ini playbooks/validate.yml
 \\\

### Criteria

- [ ] \docker compose ps\ shows services \Up\.
- [ ] Critical healthchecks in \healthy\ (define which are critical).
- [ ] Nginx responds at \http://<IP>/\ (HTTP 200).
- [ ] Console responds behind Nginx (HTTP 200).
- [ ] Backend health endpoint:
 - [ ] If \/api/health\ should return 200, confirm it.
 - [ ] If it returns 404 by design today, document it and validate another real endpoint (e.g., \/api/version\, \/api/status\, etc.). This is key to prevent the validator from passing with a false OK.

---

## 5) Minimal UX Validation (manual, 5–8 min)

- [ ] Open Console in browser: \http://<IP>/\
- [ ] Login with generated credentials (from \install-info.txt\ or controlled output).
- [ ] Load Dashboards / Grafana proxy page: \http://<IP>/grafana\
- [ ] Confirm at least 1 dashboard loads without visible errors.
- [ ] Confirm Alerts / Logs / Traces do not crash (even if empty).

---

## 6) Licensing Flow (most important)

Define and test two paths: **offline-first** (sovereign) and **optional online**.

### 6A) Offline Bundle (recommended for sovereignty)

- [ ] Installer generates fingerprint automatically on target:
 - Location: \/opt/rhinometric/fingerprint.txt\ (or defined by roles).
- [ ] Generates a \license request bundle\ (JSON or tar.gz):
 - Example: \/opt/rhinometric/license-request.bundle.tar.gz\
 - Contains: fingerprint + minimal metadata (version, date, non-sensitive instance ID).
- [ ] Documented flow for the client:
 1. \Send this bundle / fingerprint to the vendor.\
 2. \Receive \license.key\.\
 3. \Place \license.key\ in \/opt/rhinometric/license.key\.\
 4. \Restart required services.\
- [ ] Apply license without reinstalling:
 - [ ] \nsible-playbook ... playbooks/deploy.yml --tags license\ (if exists), or a specific \license.yml\ playbook.
- [ ] Confirm in UI that it transitions to \licensed\.

### 6B) Online Activation (only if maintained)

- [ ] Installer can activate with a token/activation code without asking the user for a fingerprint.
- [ ] If no internet, falls back to offline without breaking the installation.
- [ ] No sensitive token is stored in logs.

---

## 7) Installer Observability — Debug Bundle

### On Failure

- [ ] A debug bundle is generated on the target with:
 - \docker compose ps\
 - \docker compose logs --tail ...\
 - \df -h\, \ree -m\, \uname -a\
 - Relevant configs (without secrets)
- [ ] Bundle path documented, e.g.:
 \\\
 /opt/rhinometric/debug/install-debug-bundle.tar.gz
 \\\

---

## 8) Uninstall / Cleanup (reproducibility)

- [ ] Execute:
 \\\ash
 ansible-playbook -i inventories/<env>.ini playbooks/uninstall.yml
 \\\
- [ ] Criteria:
 - Stack down, volumes deleted (if applicable), \/opt/rhinometric\ clean (per policy).
- [ ] Reinstall from scratch on the same VM and confirm no residual artifacts remain.

---

## 9) Release Sign-off

- [ ] PR merged to \main\ (if applicable).
- [ ] Tag \nsible-installer-v1.0.0\ created.
- [ ] Note in docs: \Bash installer v3.0.4 frozen/deprecated.\
- [ ] Evidence attached (copy/paste):
 - Output of \deploy.yml\
 - Output of \alidate.yml\
 - Basic screenshots (Console home + Grafana health)

---

*Checklist version: 1.0.0 | Created: 2026-03-05 | Installer: Ansible v1.0.0*
