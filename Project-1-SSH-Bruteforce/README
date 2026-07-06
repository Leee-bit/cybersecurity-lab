# Project 1 — SSH Brute Force Detection in Splunk

![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Difficulty](https://img.shields.io/badge/Difficulty-Beginner-yellow)
![Tools](https://img.shields.io/badge/Tools-Kali%20%7C%20Hydra%20%7C%20Splunk-red)

## 🎯 Objective

Simulate an SSH brute force attack from Kali Linux against Metasploitable2, detect the attack using Splunk SPL queries, build a SOC detection dashboard, and configure an automated alert.

---

## 🧠 What is an SSH Brute Force Attack?

SSH (Secure Shell) is a protocol that allows users to remotely log into Linux systems via the terminal. It runs on **port 22** by default.

A brute force attack is when an attacker systematically tries thousands of username and password combinations against a login service until they find valid credentials. It is one of the most common attack techniques used against internet-facing servers.

**Why it matters:** Weak or default passwords are extremely common. Tools like Hydra can try thousands of passwords per minute, making brute force attacks fast and effective against poorly secured systems.

---

## 🖥️ Lab Environment

| Component | Details |
|-----------|---------|
| Attacker | Kali Linux (192.168.248.3) |
| Target | Metasploitable2 (192.168.248.4) |
| SIEM | Splunk Enterprise (Windows host 192.168.248.1) |
| Attack Tool | Hydra v9.7 |
| Wordlist | rockyou.txt (14,344,399 passwords) |
| Log Source | /var/log/auth.log via rsyslog → UDP 514 |

---

## ⚔️ Attack Simulation

### Phase 1: Reconnaissance
Verified SSH service was running on target:
```bash
nmap -p 22 192.168.248.4
```
**Result:**
```
PORT   STATE SERVICE
22/tcp open  ssh
```

### Phase 2: SSH Compatibility Fix
Metasploitable2 uses old SSH algorithms not supported by modern Kali. Added compatibility settings to `/etc/ssh/ssh_config`:
```
Host 192.168.248.4
    HostKeyAlgorithms +ssh-rsa
    KexAlgorithms +diffie-hellman-group1-sha1,diffie-hellman-group14-sha1
    MACs +hmac-sha1,hmac-md5
    PubkeyAcceptedAlgorithms +ssh-rsa
```

### Phase 3: Brute Force Attack
Launched SSH brute force using Hydra:
```bash
hydra -l msfadmin -P /usr/share/wordlists/rockyou.txt 192.168.248.4 ssh -t 4 -V
```

**Command breakdown:**
| Flag | Meaning |
|------|---------|
| `-l msfadmin` | Target username |
| `-P rockyou.txt` | Password wordlist |
| `192.168.248.4` | Target IP |
| `ssh` | Target service |
| `-t 4` | 4 parallel threads |
| `-V` | Verbose output |

**Attack Result:** 197 failed login attempts generated in ~3 minutes

---

## 🔍 Detection in Splunk

### Raw Log Format
Each failed SSH attempt generates this log entry on Metasploitable2:
```
Jul 6 23:01:28 metasploitable sshd[7457]: Failed password for msfadmin from 192.168.248.3 port 57262 ssh2
```

### Query 1: Find All Failed SSH Attempts
```spl
index=lab_logs "Failed password"
| table _time, _raw
```
**Result:** 197 events found

### Query 2: Extract Attacker IP and Count Attempts
```spl
index=lab_logs "Failed password"
| rex "Failed password for \w+ from (?P<src_ip>\d+\.\d+\.\d+\.\d+)"
| stats count by src_ip
```
**Result:**
| src_ip | count |
|--------|-------|
| 192.168.248.3 | 197 |

### Query 3: Brute Force Threshold Detection
```spl
index=lab_logs "Failed password"
| rex "Failed password for \w+ from (?P<src_ip>\d+\.\d+\.\d+\.\d+)"
| stats count by src_ip
| where count > 10
```
**Result:** Confirmed brute force — 197 attempts from single IP (normal user = 3-5 max)

### Query 4: Attack Timeline
```spl
index=lab_logs "Failed password"
| timechart span=1m count
```
**Result:** Clear spike pattern — flat baseline then sudden surge of attempts

---

## 📊 Splunk Dashboard

Built a SOC detection dashboard with two panels:

**Panel 1 — Failed SSH Attempts by Source IP**
- Visualization: Statistics Table
- Shows attacker IP and total attempt count
- Immediately identifies the source of attack

**Panel 2 — SSH Attack Timeline**
- Visualization: Line Chart
- Shows attempts per minute over time
- Reveals the attack pattern — sudden spike = brute force

---

## 🔔 Automated Alert

Configured a Splunk scheduled alert:

| Setting | Value |
|---------|-------|
| Alert Name | SSH Brute Force Detected |
| Schedule | Hourly |
| Trigger Condition | Number of Results > 0 |
| Action | Add to Triggered Alerts |

The alert automatically runs the detection query and fires whenever any IP exceeds the threshold — mimicking real SOC monitoring.

---

## 📸 Screenshots

| Screenshot | Description |
|------------|-------------|
| `hydra-attack-running.png` | Hydra generating failed SSH attempts |
| `splunk-197-events.png` | 197 failed password events in Splunk |
| `splunk-attacker-ip.png` | Extracted attacker IP with count |
| `soc-dashboard.png` | Complete SOC detection dashboard |
| `alert-configured.png` | Automated alert configuration |

---

## 🧠 Key Concepts Learned

**SSH Brute Force Pattern**
A legitimate user failing to log in generates 3-5 failed attempts maximum. An attacker using Hydra generates hundreds or thousands. The threshold detection (`count > 10`) is the core detection logic.

**SPL rex Command**
Splunk doesn't always automatically parse fields from raw logs. The `rex` command uses regular expressions to extract specific values (like IP addresses) from raw log text and create searchable fields.

**Log Flow Pipeline**
```
Attack happens on Metasploitable2
        ↓
sshd writes to /var/log/auth.log
        ↓
rsyslog forwards via UDP 514
        ↓
Splunk indexes the event
        ↓
SPL query detects the pattern
        ↓
Alert fires → SOC analyst investigates
```

**Why Single IP High Volume = Brute Force**
Normal authentication failures are distributed across many users and time periods. A brute force attack concentrates hundreds of failures from one source IP in a short time window — this concentration is the signature we detect.

---

## ⚠️ Issues Faced & Fixed

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Hydra kex error | Modern Kali vs old Metasploitable2 SSH algorithm mismatch | Added legacy algorithm support to /etc/ssh/ssh_config |
| `stats count by src` returned no results | Splunk didn't auto-parse src field from syslog format | Used `rex` to manually extract IP from raw log text |
| Bad key types error | ssh-dss completely removed from modern OpenSSH | Removed ssh-dss, kept only ssh-rsa |

---

## 📈 Detection Quality Assessment

| Metric | Value |
|--------|-------|
| True Positives | 197 (all Hydra attempts correctly detected) |
| False Positives | 0 (no legitimate traffic flagged) |
| Detection Threshold | > 10 failed attempts from single IP |
| Detection Latency | < 5 minutes (alert schedule) |

---

## ➡️ Next Project

[Project 2 — Port Scan Detection Engineering](../Project-2-Port-Scan/)

Perform multiple Nmap scan types against Metasploitable2 and create SIEM queries to detect reconnaissance activity while reducing false positives.
