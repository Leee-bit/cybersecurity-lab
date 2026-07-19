# 📊 Splunk SPL Queries — Complete Reference

All detection queries used across all lab projects, explained line by line.

---

## 📌 How to Read SPL Queries

```
index=lab_logs "Failed password"   ← search filter
| rex "from (?P<src_ip>...)"       ← extract fields
| stats count by src_ip            ← calculate
| where count > 10                 ← filter results
| sort -count                      ← sort output
```

Each `|` (pipe) passes results to the next command — read left to right, top to bottom.

---

## 🔐 Project 1 — SSH Brute Force Detection

### P1-Q1: Find All Failed SSH Attempts
```spl
index=lab_logs "Failed password"
| table _time, _raw
```
**What it does:** Shows all raw log entries containing "Failed password" — the text SSH writes every time a login fails.

**Fields:**
| Field | Meaning |
|-------|---------|
| `_time` | Timestamp of the event |
| `_raw` | Complete raw log line as received |

---

### P1-Q2: Extract Attacker IP and Count Attempts
```spl
index=lab_logs "Failed password"
| rex "Failed password for \w+ from (?P<src_ip>\d+\.\d+\.\d+\.\d+)"
| stats count by src_ip
| sort -count
```
**What it does:** Extracts the attacker's IP address from raw log text and counts how many times each IP failed.

**Rex pattern breakdown:**
| Pattern | Matches |
|---------|---------|
| `Failed password for` | Literal text |
| `\w+` | Any word (the username) |
| `from` | Literal text |
| `(?P<src_ip>...)` | Creates field called `src_ip` |
| `\d+\.\d+\.\d+\.\d+` | IP address pattern |

---

### P1-Q3: Brute Force Threshold Detection ⭐ (Core Alert Query)
```spl
index=lab_logs "Failed password"
| rex "Failed password for \w+ from (?P<src_ip>\d+\.\d+\.\d+\.\d+)"
| stats count by src_ip
| where count > 10
| sort -count
```
**What it does:** Flags any IP with more than 10 failed SSH attempts — the core brute force detection logic.

**Why threshold of 10:**
- Normal user forgetting password: 3-5 attempts max
- Hydra brute force tool: hundreds per minute
- Threshold of 10 catches all automated attacks without false positives

**Lab result:** 192.168.248.3 — 197 attempts detected ✅

---

### P1-Q4: Attack Timeline
```spl
index=lab_logs "Failed password"
| timechart span=1m count
```
**What it does:** Shows failed login attempts grouped by minute — reveals the attack spike pattern.

**Reading the chart:**
- Flat line = normal (no attack)
- Sudden spike = brute force attack in progress
- Returns to flat = attack stopped

---

### P1-Q5: Targeted Username Detection
```spl
index=lab_logs "Failed password"
| rex "Failed password for (?P<username>\w+) from (?P<src_ip>\d+\.\d+\.\d+\.\d+)"
| stats count by src_ip, username
| sort -count
```
**What it does:** Shows which usernames are being targeted — reveals attacker's knowledge of the system.

---

### P1-Q6: Compromise Detection (Successful Login After Brute Force)
```spl
index=lab_logs ("Failed password" OR "Accepted password")
| rex "(Failed|Accepted) password for (?P<username>\w+) from (?P<src_ip>\d+\.\d+\.\d+\.\d+)"
| stats count(eval(match(_raw,"Failed"))) as failures,
        count(eval(match(_raw,"Accepted"))) as successes by src_ip
| where failures > 10 AND successes > 0
```
**What it does:** Detects if brute force succeeded — finds IPs that had many failures AND at least one success.

**Why this is critical:** If this query returns results, the system is likely compromised.

---

## 🔍 Project 2 — Port Scan Detection

### P2-Q1: Detect Port Scan by Unique Port Count ⭐ (Core Detection)
```spl
index=lab_logs "IPTABLE" "192.168.248.3"
| rex "SRC=(?P<src_ip>\d+\.\d+\.\d+\.\d+)"
| rex "DPT=(?P<dest_port>\d+)"
| stats dc(dest_port) as ports_scanned by src_ip
| where ports_scanned > 15
| sort -ports_scanned
```
**What it does:** Counts unique destination ports per source IP — the signature of port scanning.

**Key command — `dc(dest_port)`:**
- `dc` = distinct count = count unique values only
- Counts each port number once even if hit multiple times
- Normal traffic: 1-3 unique ports
- Port scanner: hundreds of unique ports

**Lab result:** 192.168.248.3 scanned 1047 unique ports ✅

---

### P2-Q2: Port Scan Timeline
```spl
index=lab_logs "IPTABLE" "192.168.248.3"
| rex "SRC=(?P<src_ip>\d+\.\d+\.\d+\.\d+)"
| timechart span=1m count by src_ip
```
**What it does:** Shows packet count per minute from each IP — reveals distinct scan bursts.

**What the spike pattern reveals:**
- Each spike = one Nmap scan type
- Different heights = different scan speeds (SYN fastest, UDP slowest)

---

### P2-Q3: Top Ports Targeted by Attacker
```spl
index=lab_logs "IPTABLE" "192.168.248.3"
| rex "DPT=(?P<dest_port>\d+)"
| stats count by dest_port
| sort -count
| head 20
```
**What it does:** Shows which ports received most probes — reveals attacker's priorities and intent.

**Analyst insight:** High counts on specific ports = attacker interested in those services specifically.

---

### P2-Q4: Scan Rate Per Minute (False Positive Reduction) ⭐
```spl
index=lab_logs "IPTABLE" "192.168.248.3"
| rex "SRC=(?P<src_ip>\d+\.\d+\.\d+\.\d+)"
| rex "DPT=(?P<dest_port>\d+)"
| bin _time span=1m
| stats dc(dest_port) as ports_per_min by _time, src_ip
| where ports_per_min > 10
| sort -ports_per_min
```
**What it does:** Measures unique ports per minute — distinguishes scanners from legitimate monitoring.

**Key command — `bin _time span=1m`:**
- Groups all events into 1-minute time buckets
- Allows rate-based calculations per minute

**False positive logic:**
```
Monitoring tool checks 3 ports/min  → ports_per_min=3  → NOT flagged
Nmap scanner hits 1000 ports/min    → ports_per_min=1000 → FLAGGED 🚨
```

**Lab result:**
| Time | IP | Ports/min |
|------|----|-----------|
| 22:26 | 192.168.248.3 | 1018 (SYN scan) |
| 22:21 | 192.168.248.3 | 950 (Version scan) |
| 22:35 | 192.168.248.3 | 908 (Aggressive) |
| 22:37 | 192.168.248.3 | 724 (UDP scan) |

---

### P2-Q5: Detect SYN Scans Specifically
```spl
index=lab_logs "IPTABLE" "SYN"
| rex "SRC=(?P<src_ip>\d+\.\d+\.\d+\.\d+)"
| rex "DPT=(?P<dest_port>\d+)"
| stats dc(dest_port) as syn_ports by src_ip
| where syn_ports > 15
```
**What it does:** Filters specifically for SYN flag packets — detects stealth SYN scans.

---

### P2-Q6: Detect UDP Scans
```spl
index=lab_logs "IPTABLE" "PROTO=UDP"
| rex "SRC=(?P<src_ip>\d+\.\d+\.\d+\.\d+)"
| rex "DPT=(?P<dest_port>\d+)"
| stats dc(dest_port) as udp_ports by src_ip
| where udp_ports > 5
```
**What it does:** Detects UDP reconnaissance specifically — different threshold because UDP scanning is slower.

---

### P2-Q7: Full Reconnaissance Summary
```spl
index=lab_logs "IPTABLE"
| rex "SRC=(?P<src_ip>\d+\.\d+\.\d+\.\d+)"
| rex "DPT=(?P<dest_port>\d+)"
| rex "PROTO=(?P<protocol>\w+)"
| stats dc(dest_port) as unique_ports,
        count as total_packets,
        values(protocol) as protocols by src_ip
| where unique_ports > 15
| sort -unique_ports
```
**What it does:** Complete picture — unique ports, total packets, and protocols used per attacker IP.

---

## 🛠️ General Utility Queries

### Check All Logs (Any Project)
```spl
index=lab_logs
| head 20
| table _time, _raw
```
**Use:** Verify logs are flowing and check raw format before building detection queries.

---

### Search Everything (Troubleshooting)
```spl
index=*
| head 20
| table _time, _raw
```
**Use:** When `index=lab_logs` returns nothing — confirms if ANY logs are being received.

---

### Count Events by Source
```spl
index=lab_logs
| stats count by host
```
**Use:** See how many events came from each source machine.

---

### Find Events in Last 5 Minutes
```spl
index=lab_logs earliest=-5m
| table _time, _raw
```
**Use:** Check if recent attack traffic is arriving in Splunk in real time.

---

## 📝 SPL Command Quick Reference

| Command | Syntax | What it does |
|---------|--------|-------------|
| `rex` | `rex "pattern (?P<fieldname>...)"` | Extract field from raw text using regex |
| `stats count` | `stats count by field` | Count events grouped by field |
| `stats dc()` | `stats dc(field) as name` | Count unique/distinct values |
| `timechart` | `timechart span=1m count` | Chart events over time |
| `where` | `where count > 10` | Filter results by condition |
| `sort` | `sort -count` | Sort (- = descending) |
| `head` | `head 20` | Show first N results |
| `table` | `table field1, field2` | Display as clean table |
| `bin` | `bin _time span=1m` | Group time into buckets |
| `eval` | `eval risk=count*10` | Create calculated field |
| `values()` | `values(field)` | List all unique values |

---

## 🔡 Regex Patterns Used

| Pattern | What it matches |
|---------|----------------|
| `\d+\.\d+\.\d+\.\d+` | IP address (e.g. 192.168.248.3) |
| `\w+` | Any word (letters, numbers, underscore) |
| `(?P<name>...)` | Named capture group — creates Splunk field |
| `\d+` | One or more digits |
| `.*` | Any characters (wildcard) |

---

*Reference document for github.com/Leee-bit/cybersecurity-lab*
*Analyst: Sreelakshmi Chandran*
