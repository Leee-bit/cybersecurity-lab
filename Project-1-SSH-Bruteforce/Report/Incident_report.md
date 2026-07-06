# Incident Report — SSH Brute Force Attack

**Report ID:** IR-2026-001
**Date:** 06 July 2026
**Analyst:** Sreelakshmi Chandran
**Severity:** High
**Status:** Contained (Lab Simulation)

---

## 1. Executive Summary

A SSH brute force attack was detected against the internal lab server (192.168.248.4) originating from IP address 192.168.248.3. The attack generated 197 failed authentication attempts over approximately 3 minutes using an automated password spraying tool. The attack was detected via Splunk SIEM using threshold-based detection logic. No successful authentication was observed during the attack window.

---

## 2. Incident Timeline

| Time (UTC+12) | Event |
|--------------|-------|
| 23:01:24 | First failed SSH login attempt detected |
| 23:01:24–23:04:00 | 197 failed login attempts recorded |
| 23:04:00 | Attack stopped (Ctrl+C) |
| 23:15:47 | Splunk detection query confirmed 197 events |
| 23:30:28 | Automated alert configured in Splunk |

---

## 3. Attack Details

| Field | Value |
|-------|-------|
| Attack Type | SSH Brute Force |
| Source IP | 192.168.248.3 (Kali Linux) |
| Target IP | 192.168.248.4 (Metasploitable2) |
| Target Port | 22 (SSH) |
| Target Username | msfadmin |
| Tool Used | Hydra v9.7 |
| Wordlist | rockyou.txt (14,344,399 entries) |
| Total Attempts | 197 |
| Duration | ~3 minutes |
| Threads | 4 parallel |
| Successful Logins | 0 |

---

## 4. Detection Method

**Detection Tool:** Splunk Enterprise SIEM
**Log Source:** /var/log/auth.log (Metasploitable2) via rsyslog UDP 514
**Detection Query:**
```spl
index=lab_logs "Failed password"
| rex "Failed password for \w+ from (?P<src_ip>\d+\.\d+\.\d+\.\d+)"
| stats count by src_ip
| where count > 10
```
**Detection Logic:** Any source IP generating more than 10 failed SSH authentication attempts within the search window is flagged as a potential brute force attack.

**Why this threshold?**
A legitimate user failing to remember their password will typically generate 3-5 failed attempts before resetting their credentials or seeking help. 197 attempts from a single IP in 3 minutes is statistically impossible for a human user and conclusively indicates automated attack tooling.

---

## 5. Evidence

**Log Sample (raw):**
```
Jul 6 23:01:28 metasploitable sshd[7457]: Failed password for msfadmin from 192.168.248.3 port 57262 ssh2
Jul 6 23:01:26 metasploitable sshd[7461]: Failed password for msfadmin from 192.168.248.3 port 57276 ssh2
Jul 6 23:01:26 metasploitable sshd[7459]: Failed password for msfadmin from 192.168.248.3 port 57266 ssh2
```

**Splunk Finding:**
| src_ip | count |
|--------|-------|
| 192.168.248.3 | 197 |

---

## 6. Impact Assessment

| Category | Assessment |
|----------|-----------|
| Confidentiality | No impact — no successful authentication |
| Integrity | No impact — no system access gained |
| Availability | Low impact — minor SSH service load during attack |
| Overall Severity | High (potential for account compromise if weak password) |

---

## 7. Root Cause Analysis

The attack was possible due to:
1. SSH service exposed on default port 22
2. Known default username (`msfadmin`) in use
3. No account lockout policy configured
4. No rate limiting on SSH authentication attempts
5. Weak/default password in use on target system

---

## 8. Recommendations

| Priority | Recommendation |
|----------|---------------|
| Critical | Change default credentials immediately |
| High | Implement account lockout after 5 failed attempts |
| High | Disable password authentication — use SSH key pairs only |
| Medium | Move SSH to non-standard port (e.g. 2222) |
| Medium | Implement IP-based rate limiting (fail2ban) |
| Low | Consider VPN requirement before SSH access |

---

## 9. Lessons Learned

**Detection Engineering:**
The `rex` command was required to extract the attacker IP from unstructured syslog format. Production environments should use structured logging (JSON) or properly configured sourcetypes to avoid manual field extraction.

**Threshold Tuning:**
The threshold of >10 failed attempts works well for this lab. In production, the threshold should be tuned based on baseline normal authentication failure rates to minimise false positives while maintaining detection sensitivity.

**Attack Pattern Recognition:**
The timechart visualisation clearly showed the attack signature — a flat baseline followed by a sudden spike in failed authentications. This pattern recognition is fundamental to SOC analyst work.

---

## 10. MITRE ATT&CK Mapping

| Tactic | Technique | ID |
|--------|-----------|-----|
| Credential Access | Brute Force: Password Spraying | T1110.003 |
| Credential Access | Brute Force: Password Guessing | T1110.001 |
| Initial Access | Valid Accounts | T1078 |

---

*Report prepared as part of SOC Home Lab training — simulated environment only*
*Analyst: Sreelakshmi Chandran | github.com/Leee-bit*
