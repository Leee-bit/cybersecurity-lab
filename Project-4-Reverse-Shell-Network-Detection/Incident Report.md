# Incident Report — Reverse Shell Network Compromise

**Report ID:** IR-2026-003
**Date:** 27 July 2026
**Analyst:** Sreelakshmi Chandran
**Severity:** Critical
**Status:** Contained (Lab Simulation)

---

## 1. Executive Summary

An outbound reverse shell connection was detected originating from internal lab host 192.168.248.4 to external host 192.168.248.3 on port 4444/TCP. The connection provided the remote host with full interactive command execution on the compromised system, confirmed via captured `whoami` and `id` commands. The activity was identified through both live (Wireshark) and offline (tcpdump) packet capture, isolated using network-layer indicators rather than host-based logging, which was not available for this connection type. No lateral movement or data exfiltration was observed beyond the initial shell access.

---

## 2. Incident Timeline

| Time (session elapsed) | Event |
|--------------|-------|
| T+0:00 | Baseline connectivity confirmed between hosts (ICMP, 0% loss) |
| T+0:05 | Packet capture started on 192.168.248.3, interface eth0 |
| T+0:12 | Listener opened on 192.168.248.3, port 4444/TCP |
| T+1:36 | Outbound TCP SYN observed from 192.168.248.4 → 192.168.248.3:4444 |
| T+1:36 | TCP handshake completed (SYN, SYN-ACK, ACK) |
| T+3:14 | First interactive command observed (`whoami`) — plaintext response `msfadmin` |
| T+3:29 | Second interactive command observed (`id`) — full UID/GID/group output returned |
| T+3:29 | Capture stopped — 21 packets recorded, 0 dropped |

---

## 3. Attack Details

| Field | Value |
|-------|-------|
| Attack Type | Reverse Shell / Unauthorized Remote Command Execution |
| Source IP (Victim) | 192.168.248.4 (Metasploitable2) |
| Destination IP (Attacker) | 192.168.248.3 (Kali Linux) |
| Tool Used | Netcat (nc) |
| Connection Direction | Outbound from victim to attacker (reverse of standard client-server model) |
| Destination Port | 4444/TCP |
| Protocol | Raw TCP, unencrypted |
| Total Packets Captured | 21 |
| Commands Executed | `whoami`, `id` |
| Duration | ~3.5 minutes (session) |

---

## 4. Shell Access Confirmed

| Command | Output | Significance |
|---------|--------|---------------|
| `whoami` | `msfadmin` | Confirms remote command execution as the `msfadmin` account |
| `id` | `uid=1000(msfadmin) gid=1000(msfadmin) groups=4(adm),20(dialout),24(cdrom),25(floppy),29(audio),30(dip),44(video),46(plugdev),107(fuse),111(lpadmin),112(admin),119(sambashare),1000(msfadmin)` | Confirms full group membership, including `adm` — indicating meaningful administrative access on the host |

---

## 5. Detection Method

**Detection Tool:** Wireshark (live capture) and tcpdump (offline capture)
**Log Source:** Raw packet capture on interface eth0 — no application or SIEM log source was available for this connection type
**Detection Filter:**
```
ip.addr == 192.168.248.4
```

**Detection Logic:**
No SPL/SIEM query was used for this incident, since Splunk's current pipeline (rsyslog → UDP 514) does not ingest connection-level or packet-level telemetry. Detection instead relied on manually identifying the following network-layer conditions:

```
Outbound connection from internal host
  → to unregistered high port (4444)
  → with no preceding DNS resolution
  → sustained bidirectional PSH/ACK traffic at irregular intervals
= Reverse shell signature
```

This is the network-layer equivalent of a detection rule and represents the logic that would be encoded into a NIDS (e.g., Zeek/Suricata) signature in a production environment.

---

## 6. Attacker Intent Analysis

| Priority | Indicator | Likely Intent |
|----------|-----------|--------------|
| 1st | Outbound connection to attacker-controlled port 4444 | Establish persistent, interactive command-and-control channel |
| 2nd | Immediate execution of `whoami`/`id` | Situational awareness — confirming privilege level post-compromise |
| 3rd | Use of `/bin/bash` via `-e` flag | Full shell access rather than limited command execution |
| 4th | No encryption used | Likely early-stage or non-evasive access; a more sophisticated attacker would use an encrypted or encoded channel to evade detection |

---

## 7. Impact Assessment

| Category | Assessment |
|----------|-----------|
| Confidentiality | High — attacker gained interactive shell access with `msfadmin` privileges, including group membership relevant to administration |
| Integrity | Medium — no file modification observed during this session, but capability existed |
| Availability | No impact observed |
| Overall Severity | Critical — full interactive remote code execution achieved, session was ongoing at time of capture |

**Critical concern:** Unlike reconnaissance (Project 2), this incident represents confirmed post-exploitation access. Any command available to `msfadmin` — including reading sensitive files, pivoting to other hosts, or establishing persistence — was available to the attacker for the duration of the session.

---

## 8. Root Cause Analysis

The reverse shell was possible due to:
1. Assumed initial code execution vector on Metasploitable2 (simulated here directly via `nc -e`, but consistent with what a real exploit chain — e.g., against vsftpd 2.3.4 or UnrealIRCd, identified in Project 2 — would achieve)
2. No egress filtering — the host was permitted to make unrestricted outbound connections on arbitrary ports
3. No host-based process monitoring (e.g., auditd) to detect the spawning of a shell tied to a network connection
4. No network intrusion detection system in place to flag unregistered outbound ports

---

## 9. Recommendations

| Priority | Recommendation |
|----------|---------------|
| Critical | Implement egress filtering — block outbound connections to non-business ports by default |
| Critical | Deploy host-based monitoring (auditd) to log `execve` of shell-spawning binaries (`/bin/bash`, `nc`, etc.) |
| High | Deploy network-layer detection (Zeek/Suricata) to flag outbound connections with no preceding DNS resolution |
| High | Forward Zeek `conn.log` and auditd logs into Splunk to close the current SIEM visibility gap for this attack class |
| Medium | Alert on sustained low-and-bursty TCP sessions to a single external IP/port, distinguishing interactive shells from normal application traffic |
| Low | Consider network segmentation to limit blast radius if a host is compromised |

---

## 10. Lessons Learned

**Network-Layer Detection Without Host Logs:**
Unlike Project 1 (SSH brute force) and Project 2 (port scan), which were both detected via log ingestion into Splunk, this incident had no usable host-based log source. Detection relied entirely on packet capture and manual interpretation of TCP metadata — a reminder that SIEM coverage is only as good as the log sources feeding it.

**Connection Direction as the Core Signal:**
The single most reliable indicator in this incident was not the port number or payload content, but the *direction* of the connection — an internal host initiating an outbound session to an external listener. This holds true even if the attacker changes the port or encrypts the payload.

**Capture Timing Is Non-Negotiable:**
Packet capture must be active before the triggering event occurs. Unlike Splunk queries, which can search historical indexed data, a live or offline packet capture cannot retroactively reveal traffic that was never recorded.

**Unencrypted Shells Are a Gift to Defenders:**
Because this session used plaintext netcat, the entire command/response conversation was directly readable from the capture — providing stronger evidence than would be available against an encrypted C2 channel, where only connection metadata (not content) would be visible.

---

## 11. MITRE ATT&CK Mapping

| Tactic | Technique | ID |
|--------|-----------|-----|
| Execution | Command and Scripting Interpreter: Unix Shell | T1059.004 |
| Command and Control | Non-Application Layer Protocol | T1095 |
| Command and Control | Ingress Tool Transfer / Remote Access Software (conceptually adjacent) | T1105 |
| Discovery | System Owner/User Discovery | T1033 |
| Discovery | Permission Groups Discovery | T1069 |

---

*Report prepared as part of SOC Home Lab training — simulated environment only*
*Analyst: Sreelakshmi Chandran | github.com/Leee-bit*
