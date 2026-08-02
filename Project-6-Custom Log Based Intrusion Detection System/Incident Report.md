# Incident Report — SSH Brute Force Detected via Custom Python IDS

**Report ID:** IR-2026-005
**Date:** 01 August 2026
**Analyst:** Sreelakshmi Chandran
**Severity:** High
**Status:** Contained (Lab Simulation)

---

## 1. Executive Summary

A sustained SSH brute-force attack was detected against internal lab server 192.168.248.4, originating from 192.168.248.3. The attack was identified using a custom-built Python detection tool rather than the Splunk SIEM used in a prior related incident (IR-2026-001), demonstrating that the same brute-force detection outcome can be achieved independently of any specific SIEM platform. The detection logic applied sliding-window threshold analysis directly against the raw authentication log, flagging a burst of 120 failed login attempts within a single 60-second window, out of 392 total failed attempts recorded during the attack. The detection tool was subsequently upgraded from a one-shot script into a continuously-running monitoring system, and re-validated against a second, independently generated burst of synthetic attack traffic to confirm real-time detection capability.

---

## 2. Incident Timeline

| Time | Event |
|------|-------|
| 20:48:00 | Peak attack window begins — 120 failed attempts recorded within 60 seconds |
| 20:48:00–20:51:13 | Sustained failed login attempts continue against user `msfadmin` |
| 21:00 | Log file (`/var/log/auth.log`) retrieved from target via netcat transfer |
| 21:39:47 | Custom Python IDS run — alert generated and written to `alerts.log` |
| 21:40:51 | Script re-run with explicit log file argument — identical alert confirmed |
| 22:05–22:08 | Detection tool upgraded to continuous monitoring mode (`ids_system.py`) and validated against a second, synthetic burst of 15 injected "Failed password" log lines — alert generated within ~1-2 seconds with no manual re-triggering |

---

## 3. Attack Details

| Field | Value |
|-------|-------|
| Attack Type | SSH Brute Force |
| Source IP | 192.168.248.3 (Kali Linux) |
| Target IP | 192.168.248.4 (Metasploitable2) |
| Target Username | msfadmin |
| Tool Used | Hydra |
| Wordlist | rockyou.txt |
| Total Failed Attempts | 392 |
| Peak Rate | 120 attempts / 60 seconds |
| Detection Threshold | ≥10 attempts / 60 seconds |

---

## 4. Detection Method

**Detection Tool:** Custom Python script (`ids_detector.py`) — no SIEM involved
**Log Source:** `/var/log/auth.log`, retrieved directly from the target via netcat file transfer (Metasploitable2 has no GUI/clipboard access)

**Detection Logic:**
```python
LOG_PATTERN = re.compile(
    r"^(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2}).*Failed password for \w+ from (\d+\.\d+\.\d+\.\d+)"
)
```
For each source IP, the script collects all failed-login timestamps and checks, for every attempt, how many other attempts from the same IP occur within the following 60 seconds. If that count reaches or exceeds 10, the IP is flagged.

**Result:**
```
[ALERT] Brute force suspected from 192.168.248.3
        120 failed attempts within 60s starting at 2026-08-01 20:48:00
```
Alert was written to a persistent `alerts.log` file, confirmed to append (not overwrite) across multiple script executions.

---

## 5. Detection Method Comparison

| Aspect | Splunk (IR-2026-001) | Custom Python IDS (this incident) |
|---|---|---|
| Detection logic | SPL: `bin _time span=1m \| stats count by src_ip \| where count > 10` | Python: manual sliding-window loop over timestamped events |
| Log ingestion | rsyslog → UDP 514 → Splunk index | Direct file read via netcat-transferred log file |
| Total attempts detected | 197 | 392 (longer attack duration in this run) |
| Alerting mechanism | Scheduled Splunk alert | Local `alerts.log` file, appended per run |
| Dependency | Requires Splunk Enterprise | Requires only Python 3, no external service |

Both methods correctly identified the same attack pattern using equivalent underlying logic, confirming that the *detection logic* — not the specific tool — is what matters for correctly identifying this attack class.

---

## 6. Attacker Intent Analysis

| Indicator | Assessment |
|---|---|
| Single username (`msfadmin`) targeted repeatedly | Attacker had prior knowledge or a guess of a likely valid username, focusing effort on password guessing rather than username enumeration |
| Use of `rockyou.txt` | Standard, widely available wordlist — consistent with an opportunistic or training-level attack rather than a highly targeted one |
| Sustained rate (120 attempts/60s) | Automated tooling (Hydra), not manual login attempts — consistent with brute-force rather than a legitimate user repeatedly mistyping a password |

---

## 7. Impact Assessment

| Category | Assessment |
|----------|-----------|
| Confidentiality | Low observed impact — no evidence a valid credential was found during this run |
| Integrity | No impact observed |
| Availability | Low — minor load from repeated authentication attempts |
| Overall Severity | High — sustained, automated credential attack against a live service; success would have granted full account access |

---

## 8. Root Cause Analysis

The brute force was possible due to:
1. SSH service exposed without rate limiting or account lockout policies
2. No fail2ban or equivalent brute-force mitigation in place on the target
3. Weak/default credentials in use (`msfadmin` account, matching a well-known default), making the attack surface realistic for this class of tool

---

## 9. Recommendations

| Priority | Recommendation |
|----------|---------------|
| Critical | Implement account lockout or rate limiting (e.g., fail2ban) after repeated failed attempts |
| High | Enforce strong, non-default credentials for all accounts |
| High | Continue running both SIEM-based (Splunk) and standalone (Python) detection in parallel as a redundancy check |
| Medium | Extend the custom Python IDS with configurable thresholds (`--threshold`, `--window` flags) to tune sensitivity without editing source code |
| Low | Add automated alert delivery (email/webhook) to the custom script for real-time notification rather than requiring manual log review |

---

## 10. Lessons Learned

**Detection Logic Is Portable**
The same brute-force detection outcome was achieved through two structurally different implementations — SPL query language and raw Python — reinforcing that understanding the underlying logic (count of events per entity per time window) matters more than mastery of any single tool.

**GUI-less Targets Require Alternative Workflows**
Metasploitable2's lack of clipboard support required using netcat as a file-transfer mechanism rather than simple copy-paste — a good reminder that real-world log collection often requires similar workarounds (e.g., scp, rsync, or centralized log forwarding) rather than manual methods.

**Custom Tooling Builds Deeper Understanding**
Writing the detection logic manually (regex extraction, sliding time window, threshold comparison) clarified exactly what a SIEM abstracts away — valuable both for troubleshooting SIEM detections and for operating effectively in environments without one.

**Continuous Monitoring Is Achievable Without Heavy Resource Cost**
Upgrading from a one-shot script to a continuously-running monitor required only a sleep-based polling loop, file-position tracking, and periodic cleanup of old data — resulting in negligible CPU/RAM usage, in contrast to resource-intensive tools like live packet capture GUIs used in earlier projects.

**User Context Affects File Paths**
Initial validation testing of the continuous monitor appeared to fail silently. Root cause was tracked to the monitoring process and the test-traffic-generation command running under different user accounts (`root` vs. a non-privileged user), each resolving `~` to a different home directory and therefore operating on two separate files that happened to share the same name. This is a realistic and transferable troubleshooting lesson applicable to any multi-user system.

---

## 11. MITRE ATT&CK Mapping

| Tactic | Technique | ID |
|--------|-----------|-----|
| Credential Access | Brute Force: Password Guessing | T1110.001 |
| Initial Access | Valid Accounts (attempted) | T1078 |

---

*Report prepared as part of SOC Home Lab training — simulated environment only*
*Analyst: Sreelakshmi Chandran | github.com/Leee-bit*
