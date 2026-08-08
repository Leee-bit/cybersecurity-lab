# Project 6 — Custom Log-Based Intrusion Detection Script → System (Python)

![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Difficulty](https://img.shields.io/badge/Difficulty-Intermediate-orange)
![Tools](https://img.shields.io/badge/Tools-Python%20%7C%20Hydra%20%7C%20Netcat-red)

## 🎯 Objective

Build a standalone, SIEM-independent intrusion detection script in Python that parses raw SSH authentication logs, applies custom sliding-window threshold detection logic, and generates persistent alerts — replicating the same brute-force detection achieved with Splunk in Project 1, but from first principles. Then upgrade the one-shot script into a lightweight, continuously-running detection **system** capable of monitoring a live log file in real time, without materially increasing resource usage.

---

## 🧠 Why Build This Instead of Just Using Splunk?

Splunk (and any SIEM) does a lot of work behind the scenes when you run an SPL query — parsing, indexing, time-windowing, and thresholding. Understanding how that logic actually works "under the hood" makes for a stronger analyst, and not every environment has a SIEM available.

**Why it matters:** Many real SOC/detection engineering roles involve writing exactly this kind of custom tooling — lightweight scripts that parse logs and apply detection rules where a full SIEM isn't deployed, isn't licensed for a given data source, or where a quick standalone check is needed. This project builds that skill directly.

---

## 🖥️ Lab Environment

| Component | Details |
|-----------|---------|
| Attacker | Kali Linux (192.168.248.3) |
| Target | Metasploitable2 (192.168.248.4) |
| Attack Tool | Hydra |
| Wordlist | rockyou.txt |
| Log Source | /var/log/auth.log (transferred from target to attacker via netcat) |
| Detection Script | Python 3 |

---

## ⚔️ Data Generation

### Phase 1: Generate Fresh Attack Traffic
```bash
hydra -l msfadmin -P /usr/share/wordlists/rockyou.txt 192.168.248.4 ssh -t 4 -V
```
Run for approximately 60 seconds and stopped manually (Ctrl+C) — enough to generate a realistic burst of failed login attempts without exhausting the full wordlist.

### Phase 2: Retrieve the Log File from the Target
Since Metasploitable2 has no clipboard/GUI, the log file was transferred to Kali using netcat rather than copy-paste:

**On Kali (listener):**
```bash
nc -lvp 9001 > auth.log
```
**On Metasploitable2 (sender):**
```bash
nc 192.168.248.3 9001 < /var/log/auth.log
```
This produced a local copy of the target's authentication log (`auth.log`, ~70KB) on Kali, ready for parsing.

### Raw Log Format
```
Aug  1 20:51:08 metasploitable sshd[4751]: Failed password for msfadmin from 192.168.248.3 port 55784 ssh2
```

---

## 🐍 Script Design

### Detection Logic
```
For each source IP:
  Collect all "Failed password" timestamps
  For each attempt, count how many attempts from the same IP
    occur within the next 60 seconds
  If that count >= 10 → flag as brute force
```
This mirrors Splunk's `bin _time span=1m | stats count by src_ip | where count > 10` logic from Project 1, implemented as a manual sliding time window in Python instead of relying on SPL.

### Key Components

| Component | Purpose |
|---|---|
| `re` (regex) | Extracts timestamp and source IP from each log line |
| `datetime` | Converts raw timestamp text into comparable time objects |
| `collections.defaultdict` | Groups all failed-attempt timestamps by source IP |
| Sliding window loop | Counts attempts within a rolling 60-second window per IP |
| `sys.argv` | Accepts the log filename as a command-line argument, defaulting to `auth.log` if omitted |
| File-based alerting | Appends timestamped alerts to `alerts.log`, persisting across multiple runs |

### Regex Pattern
```python
r"^(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2}).*Failed password for \w+ from (\d+\.\d+\.\d+\.\d+)"
```
Captures two groups: the syslog-style timestamp, and the source IP address following "Failed password for \<user\> from".

---

## 🔍 Detection Results

### Test 1 — Default execution
```bash
python3 ids_detector.py
```
```
[*] Reading log file: auth.log
[ALERT] Brute force suspected from 192.168.248.3
        120 failed attempts within 60s starting at 2026-08-01 20:48:00
Total unique source IPs seen: 1
  192.168.248.3: 392 total failed attempts
[*] 1 alert(s) written to alerts.log
```

### Test 2 — Explicit log file argument
```bash
python3 ids_detector.py auth.log
```
Produced identical detection output, confirming the command-line argument override works correctly alongside the default fallback.

### Test 3 — Alert persistence
```bash
cat alerts.log
```
```
[2026-08-01 21:39:47] ALERT: Brute force suspected from 192.168.248.3 — 120 failed attempts within 60s starting at 2026-08-01 20:48:00
[2026-08-01 21:40:51] ALERT: Brute force suspected from 192.168.248.3 — 120 failed attempts within 60s starting at 2026-08-01 20:48:00
```
Confirmed alerts append (not overwrite) across multiple runs, building a persistent alert history — matching how a real IDS would behave over time.

---

## 🚩 Findings

| Metric | Value |
|---|---|
| Unique source IPs in log | 1 (192.168.248.3) |
| Total failed login attempts | 392 |
| Peak attempts within a single 60s window | 120 |
| Detection threshold | 10 attempts / 60 seconds |
| Alert triggered | Yes |

**Comparison to Project 1 (Splunk):** Project 1's Hydra run generated 197 failed attempts detected via Splunk SPL. This run generated 392 (a longer attack duration), detected independently by this custom script — confirming the detection logic produces consistent results regardless of tooling, as long as the underlying threshold logic is sound.

---

## 🔁 Upgrade: From Script to System

### Why the Distinction Matters
A one-shot script that reads a static log file and exits isn't a true Intrusion Detection *System* — real IDS platforms (Snort, Suricata, Zeek) run continuously, watch live data as it arrives, and alert in near real time. `ids_detector.py` demonstrated correct detection logic, but only against a snapshot. To legitimately call this a "system," it needed to run continuously without needing to be manually re-triggered.

### Design Goals for the Upgrade
- Monitor the log file continuously (like `tail -f`), reacting to new lines as they're written
- Stay lightweight — negligible CPU/RAM usage, safe to leave running during other lab work
- Avoid duplicate alert spam for the same ongoing burst
- Avoid unbounded memory growth over long monitoring sessions

### Key Additions in `ids_system.py`

| Addition | Purpose |
|---|---|
| `f.seek(0, 2)` | Starts reading from the end of the file, so only new activity is processed — same principle as `tail -f` |
| `while True` loop + `time.sleep(1)` | Checks for new lines once per second instead of busy-looping, keeping CPU usage near zero while idle |
| `already_alerted` set | Prevents repeated alerts for the same ongoing burst from the same IP |
| `cleanup_old_entries()` | Runs every 5 minutes, discarding timestamps older than the cleanup window so memory usage stays flat over long-running sessions |
| `try / except KeyboardInterrupt` | Allows clean shutdown via Ctrl+C without leaving the file handle in a bad state |

### Validation Test

**Setup:** Started `ids_system.py` monitoring `auth.log` in one terminal, left it running.

**Test:** From a separate terminal, appended 15 synthetic "Failed password" log lines directly to `auth.log` using a `for` loop, simulating new attack traffic arriving in real time.

**Result:**
```
[2026-08-01 22:08:49] ALERT: Brute force suspected from 192.168.248.3 — 10 failed attempts within 60s starting at 2026-08-01 22:00:00
```
The running system detected the new burst and generated a single, correctly de-duplicated alert within approximately 1-2 seconds of the new lines being written — with no restart, re-run, or manual re-triggering required.

### Debugging Note: User Context Mismatch
During initial testing, the test burst appeared to produce no alert. Root cause: the monitoring script was running as the `root` user (home directory `/root`), while the test `for` loop was run in a separate terminal logged in as the `kali` user (home directory `/home/kali`). Both files were named `auth.log`, but `~` resolved to two different directories depending on the user context — meaning two completely separate files were being written to and read from. Resolved by ensuring both the monitor and the test traffic generation ran under the same user context (`root`) in the same working directory (`/root`).

This is a realistic, transferable lesson: file paths and `~` shortcuts are user-context-dependent, and mismatches like this are a common source of "why isn't this working" confusion in multi-user environments.

---

## 🧠 Key Concepts Learned

**Regex for Log Parsing**
Regular expressions let you extract structured data (timestamp, IP) from unstructured raw text without needing the log source to already be indexed or parsed by a separate system.

**Sliding Time Windows**
Detecting "X events within Y seconds" requires more than a simple count — it requires comparing every event's timestamp against nearby events, exactly what Splunk's `bin`/`timechart` functions abstract away. Implementing it manually clarified what that abstraction is actually doing.

**File Transfer Without a GUI**
Metasploitable2 has no clipboard support, so retrieving log data required a network-based transfer method (netcat) rather than copy-paste — reinforcing netcat's versatility beyond just reverse shells (Project 3/4).

**Detection Engineering Is Tool-Agnostic**
The same core detection logic (count of failed attempts per IP, per time window) was successfully implemented in two completely different tools — Splunk SPL and raw Python — reinforcing that the *logic* is the transferable skill, not the specific query language.

**Continuous Monitoring Doesn't Require Heavy Resources**
A live-monitoring loop, done correctly (sleep-based polling instead of busy-waiting, tracking file position instead of re-reading everything, periodic cleanup of old data), stays extremely lightweight — nothing like the resource strain of a full packet-capture GUI. The engineering pattern (not the act of "running continuously" itself) is what determines resource cost.

**"Script" vs. "System" Is a Meaningful Distinction**
A detection tool that only reacts to a static snapshot and a detection tool that continuously watches live data are architecturally different, even if they share the same core detection logic. Being precise about which one you've built (and why) reflects a clearer understanding of how real IDS platforms actually operate.

---

## ⚠️ Issues Faced & Fixed

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Unable to copy-paste log output from Metasploitable2 | Metasploitable2 has no GUI/clipboard support | Transferred the log file to Kali directly using netcat instead of manual copy-paste |
| Netcat transfer appeared to hang after sending | Netcat doesn't auto-close the connection after sending data by default | Manually pressed Ctrl+C on the sending side to close the connection |
| Pasting Python code directly into the bash terminal caused errors | Bash tried to interpret Python syntax as shell commands | Used `nano` to save the code into a `.py` file first, then executed it with `python3 <file>.py` |

---

## 📈 Detection Quality Assessment

| Metric | Value |
|--------|-------|
| True Positives | 1 (correctly flagged the only attacking IP) |
| False Positives | 0 |
| Detection Threshold | ≥10 failed attempts within 60 seconds |
| Detection Method | Custom Python regex + sliding-window logic (no SIEM) |
| Alert Persistence | Confirmed — alerts append across multiple script runs |

---

## 🔧 Recommended Improvements

- Add a second detection rule (e.g., port-scan detection, reimplementing Project 2's logic) to make this a more general-purpose mini-IDS
- Add email/webhook notification support for real-time alerting instead of just a local log file
- Package the threshold and window values as command-line flags (`--threshold`, `--window`) instead of hardcoded constants
- Extend parsing to support multiple log formats (e.g., Apache access logs, iptables logs) beyond just SSH auth logs

---

📝 Notes

Quick definitions of new terms/concepts encountered in this project:

Regex (Regular Expression) — A pattern-matching language for finding, extracting, or validating specific chunks of text (like an IP address or timestamp) inside a larger block of text.
Sliding Window (detection) — A method of checking events against nearby events in time, rather than a simple total count, to answer "how many things happened within the last X seconds?"
defaultdict — A Python dictionary that automatically creates a default value (e.g., an empty list) for a new key the first time it's used, instead of throwing an error.
Polling loop — Repeatedly checking for new data at a fixed interval (e.g., once per second), rather than continuously busy-checking — keeps CPU usage low while still reacting quickly.
tail -f (concept) — Watching a file for new lines as they're written, rather than reading the file once and stopping — the model our continuous IDS script's file-reading logic was based on.
IDS Script vs. IDS System — A script runs once against a static snapshot of data; a system runs continuously, reacting to new data in real time. Same detection logic can power either.
Hydra vs. Metasploit — Hydra is a credential-guessing tool (tries many username/password combinations against a working login); Metasploit is an exploitation framework (abuses a flaw in software to gain access, no valid credentials needed).

---

*Lab conducted as part of SOC Home Lab training — simulated environment only*
*Analyst: Sreelakshmi Chandran | github.com/Leee-bit*
