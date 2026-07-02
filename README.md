# 🛡️ Cybersecurity Home Lab 

![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Lab](https://img.shields.io/badge/Lab-Home%20SOC-blue)
![Tools](https://img.shields.io/badge/Tools-Kali%20%7C%20Splunk%20%7C%20Metasploitable2-red)

A hands-on cybersecurity home lab built to develop real-world SOC analyst skills through practical attack simulation, log analysis, and detection engineering. Each project mirrors tasks performed daily by security analysts in enterprise environments.

---

## 👩‍💻 About This Lab

This repository documents a structured 9-project SOC analyst training program built entirely from scratch on a home lab environment. Every project involves:

- Simulating real attacks in an isolated environment
- Building detection logic in a SIEM (Splunk)
- Analyzing logs and packet captures
- Documenting findings like a professional incident report

---

## 🖥️ Lab Architecture

```
┌─────────────────────────────────────────────────────┐
│                  HOST MACHINE                        │
│         Windows 11 │ Intel i7 │ 16GB RAM             │
│                                                      │
│  ┌─────────────┐      ┌──────────────────────────┐  │
│  │  Kali Linux │      │      Splunk Free          │  │
│  │ 192.168.x.3│      │    localhost:8000         │  │
│  │  (Attacker) │      │  192.168.x.1 (Windows)  │  │
│  └──────┬──────┘      └────────────┬─────────────┘  │
│         │  attacks                 │ receives logs   │
│         ▼                          │                 │
│  ┌─────────────┐                   │                 │
│  │Metasploitable│──────────────────┘                 │
│  │192.168.x.4 │   rsyslog → UDP 514                │
│  │  (Target)   │                                     │
│  └─────────────┘                                     │
│                                                      │
│         All VMs on Host-Only Network                 │
│              192.168.x.0/24                        │
└─────────────────────────────────────────────────────┘
```

---

## 🧰 Lab Environment

| Component | Details |
|-----------|---------|
| Host OS | Windows 11 (64-bit) |
| Hypervisor | Oracle VirtualBox |
| Attacker VM | Kali Linux 2026.2 (AMD64) |
| Target VM | Metasploitable2 (Ubuntu 8.04 Hardy) |
| SIEM | Splunk Enterprise (Free License) |
| Network | Host-Only (192.168.248.0/24) |
| Log Forwarding | rsyslog → UDP Syslog → Splunk port 514 |

### 🔍 Tool Glossary (Beginner Friendly)

**🖥️ Oracle VirtualBox**
A free software that lets you run multiple operating systems inside your real computer, like apps running in isolated windows. Think of it as a "computer inside your computer" — it keeps the lab completely separate from your real system.

**⚔️ Kali Linux**
A special version of Linux pre-loaded with hundreds of security tools like Nmap, Metasploit, and Wireshark. It is the industry-standard OS used by penetration testers and security researchers worldwide — our attacker machine in this lab.

**🎯 Metasploitable2**
A deliberately broken and vulnerable Linux server created by Rapid7 purely for security practice. Think of it as the "crash test dummy" of cybersecurity — it exists to be safely attacked in a lab environment and never exposed to a real network.

**📊 Splunk**
A powerful SIEM (Security Information and Event Management) platform that collects, indexes, and searches through logs from multiple systems. Think of it as a search engine for security events — it helps analysts detect attacks by finding suspicious patterns across thousands of log entries.

**📤 rsyslog**
A lightweight log forwarding service built into Linux. It collects system logs (logins, errors, service events) and forwards them in real time to a central destination — in our lab, that destination is Splunk on port 514.

**🔍 Nmap**
A network scanning tool used to discover what devices are on a network and what ports and services they are running. Attackers use it for reconnaissance; defenders use it to understand their own network exposure.

**💥 Metasploit**
An open-source framework for developing and executing exploits against known vulnerabilities. Used by penetration testers to simulate real attacks and by SOC analysts to understand how those attacks actually work under the hood.

**🦈 Wireshark**
A network packet analyser that captures and displays all network traffic in real time. It lets you see exactly what data is flowing between machines — essential for detecting suspicious connections and analysing attack traffic at the packet level.

---

## 📁 Projects

| # | Project | Skills Covered | Status |
|---|---------|---------------|--------|
| 0 | [Lab Environment Setup](./Week-0-Lab-Setup/) | Virtualization, Networking, SIEM Setup | ✅ Complete |
| 1 | [SSH Brute-Force Detection in Splunk](./Project-1-SSH-Bruteforce/) | Splunk SPL, Auth Log Analysis, Alerting | 🔄 In Progress |
| 2 | Port Scan Detection Engineering | Nmap, SIEM Queries, False Positive Tuning | ⏳ Upcoming |
| 3 | Reverse Shell Network Detection | Netcat, Wireshark, Packet Analysis | ⏳ Upcoming |
| 4 | End-to-End SOC Investigation Simulation | Full Attack Chain, Incident Timeline | ⏳ Upcoming |
| 5 | Custom Log-Based Intrusion Detection Script | Python/Bash, Log Parsing, SIEM Integration | ⏳ Upcoming |
| 6 | Beaconing Traffic Detection Lab | C2 Detection, Time-Based Analysis | ⏳ Upcoming |
| 7 | Exploitation Visibility Analysis | Log Coverage Gaps, Detection Engineering | ⏳ Upcoming |
| 8 | Web Attack Detection in SIEM | SQLi/XSS Detection, HTTP Log Analysis | ⏳ Upcoming |
| 9 | Network Baseline vs Attack Deviation Report | Traffic Analysis, Behavioral Detection | ⏳ Upcoming |

---

## 🛠️ Tools & Technologies

| Category | Tools |
|----------|-------|
| Attacker Tools | Kali Linux, Metasploit, Nmap, Netcat, Hydra |
| Defense & Detection | Splunk, rsyslog, Wireshark |
| Scripting | Python, Bash |
| Virtualization | Oracle VirtualBox |
| Documentation | Markdown, GitHub |

---

## 🎯 Learning Objectives

- Build and operate a functional SOC home lab from scratch
- Simulate real-world attacks and detect them using a SIEM
- Write detection queries (SPL) in Splunk
- Develop Python/Bash scripts for custom intrusion detection
- Produce professional incident reports and investigation timelines
- Build a public portfolio demonstrating blue team skills

---

## 📌 Methodology

Each project follows this structured approach:

```
1. SIMULATE   → Execute the attack in the isolated lab
2. DETECT     → Build SIEM queries and detection logic
3. ANALYZE    → Investigate logs and identify IOCs
4. DOCUMENT   → Write up findings like a real incident report
5. IMPROVE    → Tune detections to reduce false positives
```

---

## 🔗 Connect

- GitHub: [Leee-bit](https://github.com/Leee-bit)

---

> ⚠️ **Disclaimer:** All attacks performed in this lab are conducted in a completely isolated, private network environment against intentionally vulnerable machines. This work is strictly for educational purposes.

