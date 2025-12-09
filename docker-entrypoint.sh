#!/bin/bash
set -e

# ASCII Banner
echo '
 ███████╗██████╗ ██╗      ██████╗ ██╗████████╗ ██████╗ ██████╗ ████████╗
 ██╔════╝██╔══██╗██║     ██╔═══██╗██║╚══██╔══╝██╔════╝ ██╔══██╗╚══██╔══╝
 ███████╗██████╔╝██║     ██║   ██║██║   ██║   ██║  ███╗██████╔╝   ██║   
 ╚════██║██╔═══╝ ██║     ██║   ██║██║   ██║   ██║   ██║██╔═══╝    ██║   
 ███████║██║     ███████╗╚██████╔╝██║   ██║   ╚██████╔╝██║        ██║   
 ╚══════╝╚═╝     ╚══════╝ ╚═════╝ ╚═╝   ╚═╝    ╚═════╝ ╚═╝        ╚═╝   
                                                                         
            [ Autonomous AI Penetration Testing Framework ]
'

# Start Metasploit RPC daemon in background
echo "[*] Starting Metasploit RPC daemon..."
msfrpcd -P sploitgpt -S -a 127.0.0.1 -p 55553 &
sleep 2

# Initialize database if needed
if [ ! -f /app/data/sploitgpt.db ]; then
    echo "[*] Initializing database..."
    python3 -c "from sploitgpt.db import init_db; init_db()"
fi

# Check for Ollama connection
if [ -n "$OLLAMA_HOST" ]; then
    echo "[*] Checking Ollama connection at $OLLAMA_HOST..."
    if curl -s "$OLLAMA_HOST/api/tags" > /dev/null 2>&1; then
        echo "[+] Ollama connected"
    else
        echo "[!] Warning: Cannot connect to Ollama at $OLLAMA_HOST"
    fi
fi

# Parse loot directory for prior work
if [ -d /app/loot ] && [ "$(ls -A /app/loot 2>/dev/null)" ]; then
    echo "[*] Found prior reconnaissance data in loot/"
    ls -la /app/loot/*.nmap /app/loot/*.xml 2>/dev/null | head -5 || true
fi

echo "[*] SploitGPT ready"
echo ""

# Execute the main command
exec "$@"
