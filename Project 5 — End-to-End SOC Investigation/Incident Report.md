# Incident Report — VSFTPD 2.3.4 Backdoor Exploitation (Root Compromise)

**Report ID:** IR-2026-004
**Date:** 28 July 2026
**Analyst:** Sreelakshmi Chandran
**Severity:** Critical
**Status:** Contained (Lab Simulation)

---

## 1. Executive Summary

A critical remote code execution vulnerability in vsftpd 2.3.4 (CVE-2011-2523) was successfully exploited against internal lab server 192.168.248.4, resulting in full root-level compromise. The attack originated from 192.168.248.3 using the Metasploit Framework's `vsftpd_234_backdoor` exploit module. The attacker escalated from an initial backdoor shell into a full Meterpreter session, granting complete administrative control of the target. Post-exploitation evidence was corroborated across three independent layers — session, host process, and network connection state — confirming the compromise beyond the exploitation tool's own reporting. No data exfiltration or lateral movement was performed during this engagement, though a second network interface and a known-vulnerable IRC service were identified as viable next steps for an actual attacker.

---

## 2. Incident Timeline

| Time (session elapsed) | Event |
|--------------|-------|
| T+0:00 | Target re-confirmed vulnerable — vsftpd 2.3.4 banner present on port 21 |
| T+0:45 | Metasploit module `vsftpd_234_backdoor` selected and configured |
| T+1:10 | Vulnerability check confirmed target exploitable |
| T+1:20 | First exploitation attempt — failed ("Unable to connect to backdoor on 6200/TCP. Cooldown?") |
| T+1:35 | Second exploitation attempt — failed (port 6200 already open from attempt 1, safety check blocked retry) |
| T+1:50 | Exploitation forced (`ForceExploit true`) — backdoor successfully spawned |
| T+1:52 | Meterpreter session established (192.168.248.3:4444 ← 192.168.248.4:40023) |
| T+2:05 | Privilege confirmed as `root` via `getuid` |
| T+2:15 | Host reconnaissance performed (`sysinfo`, `ipconfig`, `ps`) |
| T+2:40 | Network connection evidence collected (`netstat -antp`) |
| T+2:50 | Packet capture (tcpdump) initiated to record ongoing session traffic |

---

## 3. Attack Details

| Field | Value |
|-------|-------|
| Attack Type | Remote Code Execution via Backdoored Service (CVE-2011-2523) |
| Source IP (Attacker) | 192.168.248.3 (Kali Linux) |
| Target IP (Victim) | 192.168.248.4 (Metasploitable2) |
| Tool Used | Metasploit Framework v6.4.135-dev |
| Exploit Module | exploit/unix/ftp/vsftpd_234_backdoor |
| Payload | cmd/linux/http/x86/meterpreter_reverse_tcp |
| Vulnerable Service | vsftpd 2.3.4 (FTP, port 21) |
| Backdoor Listener Port | 6200/TCP |
| Meterpreter Callback Port | 4444/TCP |
| Privilege Obtained | root |
| Exploitation Attempts | 3 (2 failed, 1 successful via forced override) |

---

## 4. Access Confirmed

| Command | Output | Significance |
|---------|--------|---------------|
| `getuid` | `root` | Confirms full administrative privilege on the target — highest possible severity outcome |
| `sysinfo` | `Computer: metasploitable.localdomain`, `OS: Ubuntu 8.04 (Linux 2.6.24-16-server)` | Confirms target identity and an outdated, unsupported OS/kernel |
| `ipconfig` | Second interface (`eth1`) present with no IPv4 address on known segment | Indicates possible reachable network the attacker's current position cannot directly see — a lateral movement opportunity |

---

## 5. Detection Method

**Detection Tool:** Manual post-exploitation review (session commands, host process listing, network connection state) plus packet capture (tcpdump) on the attacker's interface
**Log Source:** No SIEM log source was available for this attack class; detection was performed entirely through direct evidence collection during the engagement
**Correlated Evidence:**

| Layer | Evidence | Command |
|---|---|---|
| Session | Root privilege confirmed | `getuid` |
| Host | Anomalous root process from non-standard path | `ps` (process `mvJBVNMpG`) |
| Network | Established connections on ports 6200 and 4444 | `netstat -antp` |

**Detection Logic (for future automation):**
```
Root process with random/unrecognized name
  + execution path outside standard binary directories (e.g. not /usr/bin, /usr/sbin)
  + correlated outbound connection to non-standard port (4444)
= Post-exploitation payload indicator
```

---

## 6. Attacker Intent Analysis

| Priority | Indicator | Likely Intent |
|----------|-----------|--------------|
| 1st | Selection of an "excellent" ranked exploit for the exact identified version | Reliable, low-risk path to guaranteed access rather than a speculative attempt |
| 2nd | Immediate escalation from raw shell to Meterpreter | Establish a more capable, persistent, feature-rich foothold rather than settling for basic command execution |
| 3rd | Post-access enumeration (`sysinfo`, `ipconfig`, `ps`) | Standard situational awareness — mapping the environment before deciding next steps |
| 4th | Identification of a second network interface | Reconnaissance for potential lateral movement into a segment not directly reachable before this compromise |

---

## 7. Impact Assessment

| Category | Assessment |
|----------|-----------|
| Confidentiality | Critical — root access permits reading of any file on the system, including credentials, configuration, and any sensitive data |
| Integrity | Critical — root access permits modification of any file, service, or configuration, including planting persistence mechanisms |
| Availability | Low observed impact — no disruptive actions taken during this engagement, though root access trivially permits denial-of-service if desired |
| Overall Severity | Critical — complete, unrestricted administrative control of the host was achieved |

**Critical concern:** This represents the most severe outcome possible on a single host. Combined with the second network interface discovered during reconnaissance, this compromise could realistically serve as a pivot point into additional network segments in a non-lab environment.

---

## 8. Root Cause Analysis

The compromise was possible due to:
1. A critically outdated and known-backdoored version of vsftpd (2.3.4) remaining in active service
2. No network-level restriction on inbound connections to FTP (port 21) or the backdoor's listener port (6200)
3. No host-based monitoring to detect the spawning of an unrecognized root process
4. No egress filtering to prevent the compromised host from establishing an outbound callback connection to the attacker
5. Absence of any SIEM visibility into this attack class — the compromise was detectable only through direct, manual post-exploitation review

---

## 9. Recommendations

| Priority | Recommendation |
|----------|---------------|
| Critical | Immediately remove or patch vsftpd 2.3.4 — no legitimate justification exists for running this version |
| Critical | Deploy host-based monitoring (auditd/EDR) to alert on new root processes launched from non-standard paths |
| Critical | Investigate and remediate the second network interface's connectivity to prevent unintended lateral movement paths |
| High | Implement network-layer detection for any connection to port 6200 |
| High | Implement egress filtering to block unsolicited outbound connections on non-business ports |
| High | Forward auditd and Zeek conn-log telemetry into Splunk to close the current SIEM visibility gap for this attack class |
| Medium | Address the second known-backdoored service identified during reconnaissance (UnrealIRCd, CVE-2010-2075) before it is also exploited |

---

## 10. Lessons Learned

**Real Exploits Behave Differently Than Simulated Ones**
Unlike the manually-triggered netcat shell used in prior projects, this exploit exhibited genuine real-world unpredictability (the "cooldown" failures) — a reminder that production exploitation and detection work must account for retries, partial successes, and inconsistent tool behavior, not just clean, one-shot scenarios.

**Privilege Level Changes the Severity Calculus Entirely**
User-level access (as seen in the earlier reverse shell project) and root-level access (this incident) are not points on the same scale — they represent fundamentally different levels of risk and require different urgency in response.

**Single-Source Detection Is Insufficient**
No individual log source captured this entire compromise. It took correlating session output, host process state, and network connection state together to build a complete, defensible picture — directly informing the recommendation to centralize multiple telemetry sources into the SIEM.

**Exploitation Tooling Leaves Artifacts**
Even a fully successful, "clean" Metasploit exploitation left a visible trace on the host — an oddly-named root process. This reinforces that host-based visibility remains valuable even against sophisticated tooling.

---

## 11. MITRE ATT&CK Mapping

| Tactic | Technique | ID |
|--------|-----------|-----|
| Initial Access | Exploit Public-Facing Application | T1190 |
| Execution | Command and Scripting Interpreter: Unix Shell | T1059.004 |
| Privilege Escalation | Exploitation for Privilege Escalation | T1068 |
| Command and Control | Non-Application Layer Protocol | T1095 |
| Discovery | System Information Discovery | T1082 |
| Discovery | System Network Configuration Discovery | T1016 |
| Discovery | Process Discovery | T1057 |

---

*Report prepared as part of SOC Home Lab training — simulated environment only*
*Analyst: Sreelakshmi Chandran | github.com/Leee-bit*
