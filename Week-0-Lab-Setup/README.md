
# Week 0 — Lab Environment Setup

## 🎯 Objective
Set up a safe, isolated home lab environment to simulate 
real-world cyberattacks and practice detection engineering.

## 🖥️ Lab Components
| Component | Details |
|-----------|---------|
| Host OS | Windows 11 |
| Hypervisor | Oracle VirtualBox |
| Attacker VM | Kali Linux 2026.2 |
| Target VM | Metasploitable2 |
| SIEM | Splunk Free |
| Network Mode | Host-Only (isolated) |

## ✅ Steps Completed

### Step 1 — Verified Virtualization
- Opened Task Manager → Performance → CPU
- Confirmed Virtualization: **Enabled**
- This is required for VirtualBox to run VMs

### Step 2 — Downloaded Kali Linux
- Downloaded pre-built VirtualBox image from kali.org
- Chose Virtual Machines tab → VirtualBox 64-bit
- Extracted using built-in Windows extractor

### Step 3 — Added Kali to VirtualBox
- VirtualBox → Machine → Add → selected .vbox file
- Fixed VERR_FILE_NOT_FOUND error by moving VM files
  from Temp folder to Documents/VMs (permanent location)

### Step 4 — Booted and Logged In
- Default credentials: kali / kali
- Opened Root Terminal Emulator
- Confirmed root access with: whoami → output: root

### Step 5 — Checked Network (In Progress)
- Ran: ip a
- Current IP: 10.0.2.15 (NAT mode)
- Next: Change to Host-Only so Kali can reach Metasploitable2

## 📚 What I Learned
- VirtualBox is a hypervisor — runs virtual computers 
  inside your real computer safely
- NAT mode = internet access but VMs can't talk to each other
- Host-Only mode = VMs talk to each other, no internet (what we need)
- Root terminal in Kali = full admin access
- apt update = refreshes package list
- apt upgrade = installs updates
- ip a = shows network interfaces and IP addresses

## ⚠️ Issues Faced & Fixed
| Issue | Fix |
|-------|-----|
| Windows Defender blocked Kali download | Temporarily disabled real-time protection |
| VERR_FILE_NOT_FOUND error on boot | Moved VM files from Temp to Documents/VMs |
| VirtualBox couldn't find .7z file | .7z must be extracted first to get .vbox file |

## 🔄 Status
- [x] VirtualBox installed
- [x] Kali Linux running
- [ ] Network changed to Host-Only
- [ ] Metasploitable2 downloaded and running
- [ ] Kali ↔ Metasploitable2 ping successful
- [ ] Splunk installed
- [ ] Logs flowing into Splunk
