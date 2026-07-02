# Week 0 — Home Lab Environment Setup

![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Duration](https://img.shields.io/badge/Duration-1%20Week-blue)
![Difficulty](https://img.shields.io/badge/Difficulty-Beginner-yellow)

## 🎯 Objective

Build a fully isolated, functional cybersecurity home lab from scratch capable of:
- Simulating real cyberattacks safely
- Capturing and forwarding logs to a SIEM
- Detecting attacks through log analysis in Splunk

---

## 🏗️ Lab Architecture

```
┌──────────────────────────────────────────────────────┐
│                   HOST MACHINE                        │
│          Windows 11 │ i7 12th Gen │ 16GB RAM          │
│                  192.168.248.1                        │
│                       │                              │
│          VirtualBox Host-Only Network                 │
│               192.168.248.0/24                        │
│                       │                              │
│         ┌─────────────┴──────────────┐               │
│         │                            │               │
│  ┌──────▼──────┐             ┌───────▼──────┐        │
│  │  Kali Linux │             │Metasploitable│        │
│  │192.168.248.3│  ─attacks→  │192.168.248.4 │        │
│  │  Attacker   │             │    Target    │        │
│  └─────────────┘             └───────┬──────┘        │
│                                      │               │
│                              rsyslog │ UDP:514        │
│                                      ▼               │
│                              ┌───────────────┐       │
│                              │    Splunk      │       │
│                              │ localhost:8000 │       │
│                              │   SIEM/SOC     │       │
│                              └───────────────┘       │
└──────────────────────────────────────────────────────┘
```

---

## 🖥️ Environment Specifications

| Component | Specification |
|-----------|--------------|
| Host Machine | Asus Vivobook, Windows 11 64-bit |
| Processor | Intel Core i7 12th Gen (1.70GHz) |
| RAM | 16GB |
| Storage | 954GB (202GB used) |
| Hypervisor | Oracle VirtualBox |
| Attacker VM | Kali Linux 2026.2 AMD64 |
| Target VM | Metasploitable2 (Ubuntu 8.04 Hardy) |
| SIEM | Splunk Enterprise Free |
| Network Type | Host-Only (isolated, no internet exposure) |

---

## 🌐 Network Configuration

| Device | IP Address | Role |
|--------|-----------|------|
| Windows Host | 192.168.248.1 | Splunk SIEM host |
| Kali Linux | 192.168.248.3 | Attacker machine |
| Metasploitable2 | 192.168.248.4 | Vulnerable target |

**Network Mode:** Host-Only — VMs can communicate with each other and the host but have no access to the internet or external networks. This ensures the vulnerable Metasploitable2 VM is never exposed to real networks.

**Why Host-Only?**

| Mode | Internet Access | VM-to-VM | Use Case |
|------|----------------|----------|----------|
| NAT | ✅ Yes | ❌ No | Updates only |
| Host-Only | ❌ No | ✅ Yes | Lab attacks |
| Bridged | ✅ Yes | ✅ Yes | ⚠️ Risky |

> Both Kali and Metasploitable2 have a second NAT adapter enabled solely for package installation. This adapter is kept disabled during attack simulations.

---

## ✅ Setup Steps

### Step 1 — Verify Hardware Virtualization
Before installing VirtualBox, confirm Intel VT-x is enabled:

**Task Manager → Performance → CPU → Virtualization: Enabled**

Without this, VirtualBox cannot run 64-bit VMs. If disabled, it must be enabled in BIOS settings.

---

### Step 2 — Install Oracle VirtualBox
Downloaded Oracle VirtualBox from virtualbox.org. No Extension Pack was required for basic lab functionality.

**Key check:** Confirmed 64-bit Windows and sufficient RAM (16GB) before proceeding — this determines how many VMs can run simultaneously.

---

### Step 3 — Download and Import Kali Linux
Downloaded the pre-built VirtualBox image from kali.org (Virtual Machines tab) to avoid manual OS installation.

**Issue encountered:** Windows Defender quarantined the download mid-transfer (flagging security tools inside the package as threats), leaving a 1.58MB incomplete file instead of the full ~3-4GB image.

**Resolution:** Temporarily disabled real-time protection during download, then re-enabled immediately after.

**How to identify an incomplete download:** Always check file size against the expected size listed on the download page. A 1.58MB "OS image" is an immediate red flag.

---

### Step 4 — Configure Kali VM
- Imported `.vbox` file into VirtualBox via Machine → Add
- Set RAM allocation to 2048MB
- Verified default login: `kali` / `kali`

**Issue encountered:** `VERR_FILE_NOT_FOUND` error on first boot

**Root cause:** VM files were extracted to `C:\Users\laksh\AppData\Local\Temp\` — a folder Windows clears automatically.

**Resolution:** Moved all VM files to a permanent location (`Documents\VMs\`). VirtualBox was then pointed to the new path via Machine → Add.

**Lesson:** Always store VM files in a permanent directory. Never leave them in Temp or Downloads.

---

### Step 5 — Configure Network Adapters

Both VMs were configured with two network adapters:

**Adapter 1 — Host-Only** (primary, always active)
- Enables VM-to-VM communication for attack simulation
- Assigns IPs in the `192.168.248.x` range

**Adapter 2 — NAT** (secondary, for package installation only)
- Provides internet access for installing tools and packages
- On Metasploitable2, IP must be manually requested:
```bash
sudo dhclient eth1
```

**Verification command:**
```bash
ip a
# Look for two interfaces: eth0 (Host-Only) and eth1 (NAT)
```

---

### Step 6 — Download and Import Metasploitable2
Downloaded from SourceForge:
```
https://sourceforge.net/projects/metasploitable/files/Metasploitable2/
```

**Import method:** Since Metasploitable2 uses a `.vmdk` disk format (not `.vbox`), it was imported by:
1. Creating a new VM manually (Linux → Ubuntu 64-bit, 1024MB RAM)
2. Selecting "Use an existing virtual hard disk file" 
3. Browsing to `Metasploitable.vmdk`

**Default credentials:** `msfadmin` / `msfadmin`

> ⚠️ Metasploitable2 must **never** be exposed to an untrusted network. It is intentionally vulnerable to dozens of known exploits.

---

### Step 7 — Verify VM Connectivity

Confirmed all machines can communicate by pinging across the network:

**From Kali → Metasploitable2:**
```bash
ping 192.168.248.4
# Expected: 0% packet loss
```

**From Metasploitable2 → Windows (Splunk host):**
```bash
ping 192.168.248.1
# Expected: 0% packet loss
```

**Issue encountered:** 100% packet loss from VMs to Windows host

**Root cause:** Windows Defender Firewall was blocking all inbound ICMP (ping) traffic from the Host-Only network.

**Resolution:** Added two inbound firewall rules via elevated Command Prompt:
```
netsh advfirewall firewall add rule name="Allow ICMP" protocol=icmpv4 dir=in action=allow
netsh advfirewall firewall add rule name="Splunk UDP 514" protocol=UDP dir=in localport=514 action=allow
```

---

### Step 8 — Install and Configure Splunk

Downloaded Splunk Enterprise (Free License) from splunk.com and installed on the Windows host.

Splunk runs as a local web application accessible at:
```
http://localhost:8000
```

**Configuration steps:**
1. Settings → Forwarding and Receiving → Configure Receiving → New Port: `9997`
2. Settings → Indexes → New Index → Name: `lab_logs`
3. Settings → Data Inputs → UDP → New Local UDP → Port: `514`, Source type: `syslog`, Index: `lab_logs`

**Verified Splunk is listening on UDP 514:**
```
netstat -an | findstr :514
UDP    0.0.0.0:514    *:*   ← Splunk listening on all interfaces
```

---

### Step 9 — Configure Log Forwarding from Metasploitable2

**Issue encountered:** Old `sysklogd` daemon on Metasploitable2 does not support remote log forwarding without the `-r` flag, and modifying startup flags did not persist reliably.

**Resolution:** Replaced `sysklogd` with `rsyslog` (modern, reliable log forwarder).

**Step 1 — Fix package repositories** (Ubuntu Hardy repos are archived):
```bash
sudo nano /etc/apt/sources.list
# Replace contents with:
deb http://old-releases.ubuntu.com/ubuntu/ hardy main restricted universe multiverse
deb http://old-releases.ubuntu.com/ubuntu/ hardy-updates main restricted universe multiverse
deb http://old-releases.ubuntu.com/ubuntu/ hardy-security main restricted universe multiverse
```

**Step 2 — Enable internet temporarily** (NAT adapter):
```bash
sudo dhclient eth1
ping 8.8.8.8   # Verify internet works
```

**Step 3 — Install rsyslog:**
```bash
sudo apt-get update
sudo apt-get install rsyslog -y
```

**Step 4 — Configure forwarding:**
```bash
sudo nano /etc/rsyslog.conf
# Add at the bottom:
*.* @192.168.248.1:514
```

**Step 5 — Restart rsyslog:**
```bash
sudo /etc/init.d/rsyslog restart
```

**Step 6 — Test log forwarding:**
```bash
logger "test from metasploitable rsyslog"
```

**Verified in Splunk:** `index=*` returned 18 events — log pipeline confirmed working ✅

---

## 🔍 Troubleshooting Reference

| Problem | Symptom | Root Cause | Fix |
|---------|---------|-----------|-----|
| Kali won't boot | VERR_FILE_NOT_FOUND | VM files in Temp folder | Move to permanent location, re-add VM |
| VMs can't communicate | 100% ping loss between VMs | Wrong network mode (NAT) | Change to Host-Only adapter |
| No internet in VM | apt-get fails | Only Host-Only adapter active | Enable NAT as Adapter 2, run `dhclient eth1` |
| Logs not reaching Splunk | 0 events in Splunk | Windows Firewall blocking UDP 514 | Add inbound firewall rule for UDP 514 |
| VMs can't ping Windows | 100% packet loss to host | Windows Firewall blocking ICMP | Add inbound firewall rule for ICMP |
| rsyslog install fails | Could not resolve repo | Old Ubuntu repos dead + no DNS | Update sources.list to old-releases.ubuntu.com |
| Old syslogd not forwarding | 0 events despite correct config | sysklogd missing `-r` flag | Replace with rsyslog |

---

## 📚 Key Concepts Learned

**Virtualization**
Running multiple isolated operating systems on a single physical machine using a hypervisor (VirtualBox). Each VM is completely isolated from the others and from the host OS.

**Network Modes**
- NAT: VM gets internet but is isolated from other VMs
- Host-Only: VMs talk to each other and the host, no internet
- Bridged: VM acts as a real device on your network (avoid for vulnerable VMs)

**IP Addressing**
- `10.0.2.x` range = NAT mode (VirtualBox default)
- `192.168.248.x` range = Host-Only network (our lab)
- `.1` address = always the gateway/host machine

**Log Forwarding Pipeline**
```
Metasploitable2 event occurs
       ↓
rsyslog captures it (/var/log/auth.log etc.)
       ↓
rsyslog forwards via UDP to 192.168.248.1:514
       ↓
Splunk receives and indexes the event
       ↓
Analyst searches and detects in Splunk
```

**Key Linux Commands Used**

| Command | What it does |
|---------|-------------|
| `ip a` | Show all network interfaces and IP addresses |
| `ping <IP>` | Test connectivity to another machine |
| `sudo dhclient eth1` | Request IP address for network interface |
| `sudo nano <file>` | Open a file for editing in terminal |
| `logger "message"` | Manually generate a syslog entry |
| `sudo /etc/init.d/rsyslog restart` | Restart the rsyslog service |
| `cat /etc/rsyslog.conf \| grep 192` | Check if forwarding rule is saved |

---

## ✅ Completion Checklist

- [x] Hardware virtualization confirmed enabled
- [x] Oracle VirtualBox installed
- [x] Kali Linux 2026.2 imported and booted
- [x] Metasploitable2 imported and booted
- [x] Host-Only network configured (192.168.248.0/24)
- [x] Kali → Metasploitable2 ping successful
- [x] Metasploitable2 → Windows ping successful
- [x] Kali → Windows ping successful
- [x] Windows Firewall rules configured
- [x] Splunk installed and accessible at localhost:8000
- [x] Splunk UDP 514 input configured
- [x] lab_logs index created in Splunk
- [x] rsyslog installed on Metasploitable2
- [x] Log forwarding verified (18 events received in Splunk)

---

## ➡️ Next Step

[Project 1 — SSH Brute-Force Detection in Splunk](../Project-1-SSH-Bruteforce/)

Simulate SSH brute-force attacks from Kali against Metasploitable2 and build Splunk dashboards with threshold-based alerts to detect credential abuse patterns.
