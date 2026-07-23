# Project 2 — Port Scan Detection Engineering

![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Difficulty](https://img.shields.io/badge/Difficulty-Beginner--Intermediate-yellow)
![Tools](https://img.shields.io/badge/Tools-Kali%20%7C%20Nmap%20%7C%20iptables%20%7C%20Splunk-red)
![MITRE](https://img.shields.io/badge/MITRE-T1595%20%7C%20T1046-orange)

## 🎯 Objective

Simulate multiple types of network reconnaissance using Nmap, capture the scan traffic using iptables firewall logging, detect port scan patterns in Splunk using SPL queries, and build detection logic that reduces false positives while catching real scans.

---

## 🧠 What is a Port Scan?

A port scan is a reconnaissance technique where an attacker sends packets to a range of ports on a target system to discover which services are running. It is typically the **first step in an attack** — before exploiting anything, attackers need to know what doors are open.

**Why it matters for SOC analysts:**
Detecting port scans gives you early warning of an incoming attack — before any exploitation happens. It is one of the most valuable detection capabilities a SOC can have.

---

## 🖥️ Lab Environment

| Component | Details |
|-----------|---------|
| Attacker | Kali Linux (192.168.248.3) |
| Target | Metasploitable2 (192.168.248.4) |
| SIEM | Splunk Enterprise (Windows host 192.168.248.1) |
| Scan Tool | Nmap 7.99 |
| Logging Tool | iptables (Linux firewall) |
| Log Source | iptables → kernel syslog → rsyslog → Splunk UDP 514 |

---

## ⚔️ Attack Simulation

### Phase 1: Enable Firewall Logging on Target

Before scanning, iptables logging was enabled on Metasploitable2 to capture all incoming packets:

```bash
sudo iptables -I INPUT -j LOG --log-prefix "IPTABLE: " --log-level 4
```

**Command breakdown:**
| Flag | Meaning |
|------|---------|
| `-I INPUT` | Insert rule for all incoming traffic |
| `-j LOG` | Action = log the packet to syslog |
| `--log-prefix "IPTABLE: "` | Label every entry for easy Splunk searching |
| `--log-level 4` | Warning level — goes to syslog |

**Verified rule was active:**
```bash
sudo iptables -L INPUT -n
```
```
Chain INPUT (policy ACCEPT)
target  prot  source      destination
LOG     all   0.0.0.0/0   0.0.0.0/0    LOG flags 0 level 4 prefix 'IPTABLE:'
```

### Phase 2: Run 4 Different Nmap Scan Types

**Scan 1 — SYN Scan (Stealth Scan):**
```bash
nmap -sS -T4 192.168.248.4
```
- Sends SYN packets only — never completes TCP handshake
- Fastest scan type (1018 ports/min in lab)
- Called "stealth" because it doesn't fully connect

**Scan 2 — Version Detection:**
```bash
nmap -sV 192.168.248.4
```
- Connects to open ports and identifies exact software versions
- More detectable than SYN scan (950 ports/min)
- Reveals exploitable version information

**Scan 3 — UDP Scan:**
```bash
nmap -sU -T4 --top-ports 20 192.168.248.4
```
- Scans UDP ports instead of TCP
- Slowest scan type (724 ports/min)
- Shows `open|filtered` when no response received

**Scan 4 — Aggressive Scan:**
```bash
nmap -A -T4 192.168.248.4
```
- Combines version detection + OS detection + default scripts
- Most comprehensive — reveals OS, versions, vulnerabilities
- Takes longest (908 ports/min — slower due to script execution)

### Phase 3: Scan Results Summary

```
PORT     STATE  SERVICE     VERSION
21/tcp   open   ftp         vsftpd 2.3.4 (backdoor!)
22/tcp   open   ssh         OpenSSH 4.7p1
23/tcp   open   telnet      Linux telnetd
80/tcp   open   http        Apache 2.2.8
445/tcp  open   netbios-ssn Samba 3.0.20
1524/tcp open   bindshell   Metasploitable root shell
3306/tcp open   mysql       MySQL 5.0.51a (no root password!)
...and 16 more open ports
```

**OS Detected:** Linux 2.6.9 - 2.6.33 (2008 era — extremely outdated)

---

## 🔍 Detection in Splunk

### Raw Log Format
Each scanned port generates this iptables log entry:
```
IPTABLE:IN=eth0 OUT= MAC=08:00:27:c8:27:4b:... 
SRC=192.168.248.3 DST=192.168.248.4 LEN=44 
PROTO=TCP SPT=63250 DPT=22 WINDOW=1024 SYN URGP=0
```

**Key fields:**
| Field | Value | Meaning |
|-------|-------|---------|
| `IN=eth0` | eth0 | Network interface |
| `SRC` | 192.168.248.3 | Attacker IP (Kali) |
| `DST` | 192.168.248.4 | Target IP (Metasploitable2) |
| `PROTO` | TCP | Protocol |
| `DPT` | 22 | Destination port being scanned |
| `SYN` | flag | SYN scan confirmed |

### Query 1: Detect Port Scan by Unique Port Count
```spl
index=lab_logs "IPTABLE" "192.168.248.3"
| rex "SRC=(?P<src_ip>\d+\.\d+\.\d+\.\d+)"
| rex "DPT=(?P<dest_port>\d+)"
| stats dc(dest_port) as ports_scanned by src_ip
| where ports_scanned > 15
| sort -ports_scanned
```
**Result:**
| src_ip | ports_scanned |
|--------|--------------|
| 192.168.248.3 | 1047 |

### Query 2: Attack Timeline
```spl
index=lab_logs "IPTABLE" "192.168.248.3"
| rex "SRC=(?P<src_ip>\d+\.\d+\.\d+\.\d+)"
| timechart span=1m count by src_ip
```
**Result:** Clear spike pattern showing 4 distinct scan bursts

### Query 3: Top Ports Targeted
```spl
index=lab_logs "IPTABLE" "192.168.248.3"
| rex "DPT=(?P<dest_port>\d+)"
| stats count by dest_port
| sort -count
| head 20
```
**Result:**
| Port | Count | Service |
|------|-------|---------|
| 8180 | 566 | Apache Tomcat |
| 80 | 484 | HTTP |
| 21 | 307 | FTP |
| 445 | 235 | SMB |
| 3306 | 154 | MySQL |

### Query 4: Scan Rate Per Minute (False Positive Reduction)
```spl
index=lab_logs "IPTABLE" "192.168.248.3"
| rex "SRC=(?P<src_ip>\d+\.\d+\.\d+\.\d+)"
| rex "DPT=(?P<dest_port>\d+)"
| bin _time span=1m
| stats dc(dest_port) as ports_per_min by _time, src_ip
| where ports_per_min > 10
| sort -ports_per_min
```
**Result:**
| Time | src_ip | ports_per_min |
|------|--------|--------------|
| 22:26 | 192.168.248.3 | 1018 |
| 22:21 | 192.168.248.3 | 950 |
| 22:35 | 192.168.248.3 | 908 |
| 22:37 | 192.168.248.3 | 724 |

---

## 📊 Splunk Dashboard

Built a SOC detection dashboard with 4 panels:

| Panel | Visualization | Purpose |
|-------|--------------|---------|
| Unique Ports Scanned by IP | Statistics Table | Identify scanning IPs |
| Port Scan Timeline | Column Chart | Show attack spike pattern |
| Top Ports Targeted | Bar Chart | Reveal attacker intent |
| Scan Rate Per Minute | Statistics Table | False positive reduction |

---

## 🔔 Automated Alert

| Setting | Value |
|---------|-------|
| Alert Name | Port Scan Detected |
| Schedule | Every 5 minutes |
| Trigger Condition | Number of Results > 0 |
| Action | Add to Triggered Alerts |

---

## 🧠 Key Concepts Learned

**Different Scan Types Leave Different Signatures**
```
SYN scan:     SYN flag only — fastest, most common
Version scan: Full connection + banner grabbing
UDP scan:     No response = open|filtered
Aggressive:   Multiple packet types + scripts
```

**Port Scan Detection Logic**
A single IP hitting 1000+ unique ports in minutes is statistically impossible for legitimate traffic. The `dc(dest_port)` (distinct count) metric is the core detection signal.

**False Positive Reduction**
Using `ports_per_min > 10` instead of just `count > 10` distinguishes between:
- Legitimate monitoring (2-3 ports/min) → not flagged
- Port scanner (700-1018 ports/min) → flagged

**iptables as Detection Source**
Linux's built-in firewall can log every packet — even to closed ports. This gives SOC analysts visibility into reconnaissance activity that application logs would never capture.

---

## ⚠️ Issues Faced & Fixed

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| No scan logs in Splunk initially | iptables not logging by default | Added LOG rule to INPUT chain |
| Loopback traffic flooding results | iptables logging internal traffic too | Added `"192.168.248.3"` filter to queries |
| `open\|filtered` state in UDP scan | UDP doesn't always respond | Expected behaviour — firewall blocking or port silently accepting |

---

## 📈 Detection Results

| Metric | Value |
|--------|-------|
| Total ports scanned | 1047 unique ports |
| Peak scan rate | 1018 ports/minute |
| Scan types detected | 4 (SYN, Version, UDP, Aggressive) |
| Detection threshold | > 10 unique ports/minute |
| False positives | 0 |
| Detection latency | < 5 minutes (alert schedule) |

---

## 🗺️ MITRE ATT&CK Mapping

| Tactic | Technique | ID |
|--------|-----------|-----|
| Reconnaissance | Active Scanning: Scanning IP Blocks | T1595.001 |
| Reconnaissance | Active Scanning: Vulnerability Scanning | T1595.002 |
| Discovery | Network Service Discovery | T1046 |
| Discovery | System Service Discovery | T1007 |

---

## ➡️ Next Project

[Project 3 — Reverse Shell Network Detection](../Project-3-Reverse-Shell/)

Generate reverse shells using Netcat and Metasploit, capture the traffic in Wireshark, and build Splunk detection logic to identify abnormal outbound connections and suspicious ports.
