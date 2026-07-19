# Incident Report — Network Port Scan Reconnaissance

**Report ID:** IR-2026-002
**Date:** 19 July 2026
**Analyst:** Sreelakshmi Chandran
**Severity:** High
**Status:** Contained (Lab Simulation)

---

## 1. Executive Summary

A series of network port scans were detected against the internal lab server (192.168.248.4) originating from IP address 192.168.248.3. The attacker conducted four distinct scan types over multiple sessions, probing 1047 unique ports and identifying 23 open services including several with known critical vulnerabilities. The reconnaissance was detected via Splunk SIEM using iptables firewall logs and rate-based detection logic. No exploitation was observed during this incident.

---

## 2. Incident Timeline

| Time (UTC+12) | Event |
|--------------|-------|
| 22:21:00 | First scan burst detected — 950 ports/min (Version scan) |
| 22:24:00 | Low activity scan — 21 ports/min |
| 22:26:00 | Peak scan rate — 1018 ports/min (SYN scan) |
| 22:35:00 | Third burst — 908 ports/min (Aggressive scan) |
| 22:37:00 | Fourth burst — 724 ports/min (UDP scan) |
| 22:41:00 | Scanning activity ceased |

---

## 3. Attack Details

| Field | Value |
|-------|-------|
| Attack Type | Network Port Scan Reconnaissance |
| Source IP | 192.168.248.3 (Kali Linux) |
| Target IP | 192.168.248.4 (Metasploitable2) |
| Tool Used | Nmap 7.99 |
| Scan Types | SYN (-sS), Version (-sV), UDP (-sU), Aggressive (-A) |
| Total Unique Ports Scanned | 1047 |
| Peak Scan Rate | 1018 ports/minute |
| Total Packets | 9,314 |
| Open Ports Discovered | 23 |
| Duration | ~20 minutes |

---

## 4. Open Ports Discovered by Attacker

| Port | Service | Version | Risk |
|------|---------|---------|------|
| 21 | FTP | vsftpd 2.3.4 | Critical — contains backdoor (CVE-2011-2523) |
| 22 | SSH | OpenSSH 4.7p1 | High — target of brute force |
| 23 | Telnet | Linux telnetd | Critical — plaintext credentials |
| 80 | HTTP | Apache 2.2.8 | High — multiple web vulnerabilities |
| 445 | SMB | Samba 3.0.20 | Critical — EternalBlue vulnerable |
| 1524 | Bindshell | Metasploitable root shell | Critical — literal backdoor |
| 3306 | MySQL | 5.0.51a | Critical — no root password |
| 5432 | PostgreSQL | 8.3.0-8.3.7 | High |
| 6667 | IRC | UnrealIRCd | Critical — contains backdoor (CVE-2010-2075) |

---

## 5. Detection Method

**Detection Tool:** Splunk Enterprise SIEM
**Log Source:** iptables kernel logs via rsyslog UDP 514
**Primary Detection Query:**
```spl
index=lab_logs "IPTABLE"
| rex "SRC=(?P<src_ip>\d+\.\d+\.\d+\.\d+)"
| rex "DPT=(?P<dest_port>\d+)"
| bin _time span=1m
| stats dc(dest_port) as ports_per_min by _time, src_ip
| where ports_per_min > 10
```

**Detection Logic:**
Any source IP scanning more than 10 unique destination ports per minute is flagged as potential reconnaissance. This threshold eliminates false positives from legitimate monitoring tools while catching all port scanner activity.

---

## 6. Attacker Intent Analysis

Based on the ports targeted with highest frequency:

| Priority | Ports | Service | Likely Intent |
|----------|-------|---------|--------------|
| 1st | 8180, 80 | Web servers | Web application exploitation |
| 2nd | 21, 2121 | FTP | Data exfiltration / anonymous access |
| 3rd | 445, 139 | SMB | Lateral movement / ransomware deployment |
| 4th | 3306, 5432 | Databases | Sensitive data theft |
| 5th | 22 | SSH | Credential brute force (already attempted) |

---

## 7. Impact Assessment

| Category | Assessment |
|----------|-----------|
| Confidentiality | Medium — attacker now knows all open services and versions |
| Integrity | No impact — no exploitation observed |
| Availability | Low — minor network load during scans |
| Overall Severity | High — complete attack surface mapped |

**Critical concern:** Attacker has identified 5 services with known backdoors or critical vulnerabilities. Exploitation is likely imminent based on reconnaissance findings.

---

## 8. Root Cause Analysis

The reconnaissance was possible due to:
1. Multiple services exposed on default ports
2. No network-level rate limiting or scan detection in place
3. No IDS/IPS blocking scanning activity
4. Services running with known vulnerable versions from 2008
5. Critical misconfigurations (anonymous FTP, no MySQL password, literal backdoors)

---

## 9. Recommendations

| Priority | Recommendation |
|----------|---------------|
| Critical | Immediately patch or disable vsftpd 2.3.4 (backdoor) |
| Critical | Remove Metasploitable root shell service (port 1524) |
| Critical | Set MySQL root password |
| Critical | Disable Telnet — use SSH only |
| High | Implement fail2ban for rate limiting |
| High | Deploy IDS (Snort/Suricata) for real-time scan detection |
| High | Close all unnecessary ports |
| Medium | Implement network segmentation |
| Medium | Deploy honeypot to detect future reconnaissance |
| Low | Move SSH to non-standard port |

---

## 10. Lessons Learned

**Detection Engineering:**
Rate-based detection (`ports_per_min > 10`) is more effective than simple count detection for port scans. It distinguishes between legitimate monitoring tools and actual scanners based on speed rather than volume.

**iptables as Detection Source:**
Linux's built-in firewall provides packet-level visibility that application logs cannot. Logging ALL incoming traffic (including to closed ports) is essential for detecting reconnaissance that never reaches application layer.

**Scan Type Differentiation:**
Different scan types leave different log signatures:
- SYN scan: SYN flag only, no full connection
- Version scan: Full TCP handshake + banner grabbing
- UDP scan: Fewer logs due to connectionless nature
- Aggressive: Mix of all above plus ICMP

**Reconnaissance Precedes Exploitation:**
In every real-world attack, port scanning precedes exploitation. Detecting and blocking at this stage prevents the attacker from reaching the exploitation phase.

---

## 11. MITRE ATT&CK Mapping

| Tactic | Technique | ID |
|--------|-----------|-----|
| Reconnaissance | Active Scanning: Scanning IP Blocks | T1595.001 |
| Reconnaissance | Active Scanning: Vulnerability Scanning | T1595.002 |
| Discovery | Network Service Discovery | T1046 |
| Discovery | System Service Discovery | T1007 |
| Discovery | System Network Configuration Discovery | T1016 |

---

*Report prepared as part of SOC Home Lab training — simulated environment only*
*Analyst: Sreelakshmi Chandran | github.com/Leee-bit*
