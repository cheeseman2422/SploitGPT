# SploitGPT

```
 ███████╗██████╗ ██╗      ██████╗ ██╗████████╗ ██████╗ ██████╗ ████████╗
 ██╔════╝██╔══██╗██║     ██╔═══██╗██║╚══██╔══╝██╔════╝ ██╔══██╗╚══██╔══╝
 ███████╗██████╔╝██║     ██║   ██║██║   ██║   ██║  ███╗██████╔╝   ██║   
 ╚════██║██╔═══╝ ██║     ██║   ██║██║   ██║   ██║   ██║██╔═══╝    ██║   
 ███████║██║     ███████╗╚██████╔╝██║   ██║   ╚██████╔╝██║        ██║   
 ╚══════╝╚═╝     ╚══════╝ ╚═════╝ ╚═╝   ╚═╝    ╚═════╝ ╚═╝        ╚═╝   
                                                                         
            [ Autonomous AI Penetration Testing Framework ]
```

> **⚠️ AUTHORIZED USE ONLY** - This tool is for authorized penetration testing and security research only. Unauthorized access to computer systems is illegal.

## What is SploitGPT?

SploitGPT is an AI-powered penetration testing framework that:

- 🧠 **Fine-tunes on install** - Trains a security-specialized model on your GPU
- 🔄 **Learns from your sessions** - Gets smarter the more you use it
- 🎯 **Asks, doesn't guess** - Clarifying questions instead of wrong assumptions
- 🔓 **Runs 100% locally** - Private, secure, no API costs after install
- ⚡ **Executes autonomously** - Actually runs commands, not just suggestions

## Quick Start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/sploitgpt.git
cd sploitgpt

# Install (includes 30-min fine-tuning on your GPU)
./install.sh

# Run
./sploitgpt
```

## Requirements

- **Docker** 
- **NVIDIA GPU** with 8GB+ VRAM (for local LLM)
- **Ollama** (auto-installed)
- Linux (tested on Kali, Ubuntu, Debian)

## Features

### 🎯 Intelligent Attack Planning
SploitGPT uses MITRE ATT&CK techniques to plan attacks. When multiple paths exist, it asks you:

```
sploitgpt > compromise 10.0.0.1

🔍 Scanning target...

PORT    STATE SERVICE
22/tcp  open  ssh
80/tcp  open  http
445/tcp open  smb

Multiple attack paths available:
[1] 🌐 Web Application (T1190) - Test for vulns, SQLi, RCE
[2] 📁 SMB Shares (T1021.002) - Enumerate shares, null session
[3] 🔑 Credential Attack (T1110) - Brute force SSH
[4] 🎯 Full Assessment - Try all paths

> 
```

### 🔧 Metasploit Integration
Uses Metasploit as the exploitation backend - no reinventing the wheel:

```
sploitgpt > use exploit for CVE-2021-44228

Using: exploit/multi/http/log4shell_header_injection
Setting RHOSTS=10.0.0.1
Launching exploit...

[*] Meterpreter session 1 opened
```

### 💻 Hybrid Terminal
Direct shell access + AI commands in one interface:

```bash
# Direct shell command
sploitgpt > nmap -sV 10.0.0.1

# AI-assisted command (prefix with /)
sploitgpt > /enumerate this target

# Or just ask
sploitgpt > what services are running?
```

### 📚 Self-Improving
Every session makes the model smarter:

```
Boot sequence:
[✓] Loading SploitGPT model
[✓] Found 47 new session logs
[?] Train on recent data? (5 min) [Y/n]: y
[✓] Model updated with your techniques
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         SploitGPT                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Ollama    │  │   Hybrid    │  │      Metasploit         │ │
│  │   (Local    │◄►│   Terminal  │◄►│      RPC Backend        │ │
│  │    LLM)     │  │   (TUI)     │  │                         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│         │                │                      │              │
│         ▼                ▼                      ▼              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Kali Linux Container                     ││
│  │  nmap • gobuster • sqlmap • hydra • nuclei • burp • ...    ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Training Data

SploitGPT is trained on:
- MITRE ATT&CK techniques and procedures
- Atomic Red Team executable tests
- Public penetration testing writeups
- Tool documentation and examples
- Your own session history (opt-in)

## License

MIT License - See [LICENSE](LICENSE)

## Disclaimer

This tool is provided for authorized security testing and educational purposes only. Users are responsible for complying with all applicable laws. The developers assume no liability for misuse.

---

*"Have I been pwned?" → "Yes. Let me show you how."*
