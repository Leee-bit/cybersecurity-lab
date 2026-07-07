# 📚 Resources & References

Useful references, learning platforms, and documentation used throughout this lab.

---

## 🌐 Learning Platforms

| Platform | What It Offers | Link |
|----------|---------------|------|
| TryHackMe | Guided beginner-friendly SOC labs | tryhackme.com |
| HackTheBox | Intermediate to advanced CTF machines | hackthebox.com |
| LetsDefend | SOC analyst simulator with real alerts | letsdefend.io |
| Blue Team Labs | Defensive security challenges | blueteamlabs.online |
| CyberDefenders | Blue team CTF challenges | cyberdefenders.org |

---

## 📖 Official Documentation

| Tool | Documentation |
|------|--------------|
| Splunk SPL | docs.splunk.com/Documentation/Splunk/latest/SearchReference |
| Kali Linux | kali.org/docs |
| Nmap | nmap.org/book/man.html |
| Metasploit | docs.metasploit.com |
| Wireshark | wireshark.org/docs |

---

## 🎯 SOC Analyst Frameworks

| Framework | Purpose | Link |
|-----------|---------|------|
| MITRE ATT&CK | Adversary tactics and techniques | attack.mitre.org |
| Cyber Kill Chain | Attack lifecycle model | lockheedmartin.com/cyberkillchain |
| NIST CSF | Cybersecurity framework | nist.gov/cyberframework |
| OWASP Top 10 | Web application vulnerabilities | owasp.org/top10 |

---

## 🔐 Certifications Roadmap

| Level | Certification | Focus |
|-------|--------------|-------|
| Beginner | CompTIA Security+ | Security fundamentals |
| Beginner | eJPT (eLearnSecurity) | Practical pentesting |
| Intermediate | BTL1 (Blue Team Level 1) | SOC analyst skills |
| Intermediate | CompTIA CySA+ | Security analytics |
| Advanced | OSCP | Offensive security |

---

## 📰 Security News & Blogs

| Source | What It Covers |
|--------|---------------|
| Krebs on Security | Cybercrime and investigations |
| Bleeping Computer | Malware and breach news |
| The Hacker News | Latest vulnerabilities |
| SANS Internet Storm Center | Daily threat intelligence |
| Threat Post | Enterprise security news |

---

## 🗂️ Wordlists for Brute Force Projects

Kali Linux includes built-in wordlists at:
```
/usr/share/wordlists/
├── rockyou.txt.gz        ← Most common passwords (14M entries)
├── dirb/                 ← Web directory wordlists
└── metasploit/           ← Metasploit wordlists
```

Unzip rockyou:
```bash
gunzip /usr/share/wordlists/rockyou.txt.gz
```
