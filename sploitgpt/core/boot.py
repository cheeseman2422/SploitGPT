"""
SploitGPT Boot Sequence

Initializes the agent with:
1. Environment enumeration
2. Tool availability check
3. Prior loot parsing
4. Session state loading
5. LLM connection verification
"""

import asyncio
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from sploitgpt.core.config import get_settings

console = Console()


@dataclass
class BootContext:
    """Context gathered during boot sequence."""
    
    # Environment
    hostname: str = ""
    username: str = ""
    interfaces: list[dict[str, str]] = field(default_factory=list)
    
    # Tools
    available_tools: list[str] = field(default_factory=list)
    missing_tools: list[str] = field(default_factory=list)
    
    # Prior work
    known_hosts: list[str] = field(default_factory=list)
    open_ports: dict[str, list[int]] = field(default_factory=dict)
    findings: list[dict[str, Any]] = field(default_factory=dict)
    
    # State
    msf_connected: bool = False
    ollama_connected: bool = False
    model_loaded: bool = False
    
    # Session
    session_count: int = 0


async def enumerate_environment() -> dict[str, Any]:
    """Gather information about the current environment."""
    env = {}
    
    # Hostname
    result = subprocess.run(["hostname"], capture_output=True, text=True)
    env["hostname"] = result.stdout.strip()
    
    # Username
    result = subprocess.run(["whoami"], capture_output=True, text=True)
    env["username"] = result.stdout.strip()
    
    # Network interfaces
    result = subprocess.run(["ip", "-br", "addr"], capture_output=True, text=True)
    interfaces = []
    for line in result.stdout.strip().split("\n"):
        parts = line.split()
        if len(parts) >= 3:
            interfaces.append({
                "name": parts[0],
                "state": parts[1],
                "addr": parts[2] if len(parts) > 2 else ""
            })
    env["interfaces"] = interfaces
    
    return env


async def check_tools() -> tuple[list[str], list[str]]:
    """Check which security tools are available."""
    essential_tools = [
        "nmap", "masscan", "msfconsole", "sqlmap", "gobuster",
        "nikto", "hydra", "john", "searchsploit", "nuclei",
        "smbclient", "enum4linux", "crackmapexec", "netcat"
    ]
    
    available = []
    missing = []
    
    for tool in essential_tools:
        result = subprocess.run(["which", tool], capture_output=True)
        if result.returncode == 0:
            available.append(tool)
        else:
            missing.append(tool)
    
    return available, missing


async def parse_loot_directory(loot_dir: Path) -> dict[str, Any]:
    """Parse prior reconnaissance data from loot directory."""
    findings = {
        "hosts": [],
        "ports": {},
        "services": [],
        "vulns": []
    }
    
    if not loot_dir.exists():
        return findings
    
    # Parse .gnmap files for quick host/port extraction
    for gnmap_file in loot_dir.glob("*.gnmap"):
        try:
            content = gnmap_file.read_text()
            for line in content.split("\n"):
                if "Host:" in line and "Ports:" in line:
                    # Extract host
                    host_match = line.split("Host:")[1].split()[0]
                    if host_match and host_match not in findings["hosts"]:
                        findings["hosts"].append(host_match)
                    
                    # Extract ports
                    if "Ports:" in line:
                        ports_section = line.split("Ports:")[1]
                        ports = []
                        for port_info in ports_section.split(","):
                            port_info = port_info.strip()
                            if "/" in port_info:
                                port_num = port_info.split("/")[0]
                                if port_num.isdigit():
                                    ports.append(int(port_num))
                        if host_match and ports:
                            findings["ports"][host_match] = ports
        except Exception:
            pass
    
    return findings


async def check_msf_connection() -> bool:
    """Check if Metasploit RPC is available."""
    settings = get_settings()
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((settings.msf_host, settings.msf_port))
        sock.close()
        return result == 0
    except Exception:
        return False


async def check_ollama_connection() -> bool:
    """Check if Ollama is available."""
    settings = get_settings()
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.ollama_host}/api/tags", timeout=5)
            return resp.status_code == 200
    except Exception:
        return False


async def boot_sequence() -> BootContext:
    """Run the full boot sequence and return context."""
    ctx = BootContext()
    settings = get_settings()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Step 1: Environment
        task = progress.add_task("[cyan]Enumerating environment...", total=None)
        env = await enumerate_environment()
        ctx.hostname = env.get("hostname", "unknown")
        ctx.username = env.get("username", "unknown")
        ctx.interfaces = env.get("interfaces", [])
        progress.update(task, description=f"[green]✓ Environment: {ctx.username}@{ctx.hostname}")
        
        # Step 2: Tools
        task = progress.add_task("[cyan]Checking tools...", total=None)
        ctx.available_tools, ctx.missing_tools = await check_tools()
        progress.update(task, description=f"[green]✓ Tools: {len(ctx.available_tools)} available")
        
        # Step 3: Prior loot
        task = progress.add_task("[cyan]Parsing prior reconnaissance...", total=None)
        findings = await parse_loot_directory(settings.loot_dir)
        ctx.known_hosts = findings.get("hosts", [])
        ctx.open_ports = findings.get("ports", {})
        progress.update(task, description=f"[green]✓ Prior work: {len(ctx.known_hosts)} hosts known")
        
        # Step 4: Metasploit
        task = progress.add_task("[cyan]Connecting to Metasploit...", total=None)
        ctx.msf_connected = await check_msf_connection()
        if ctx.msf_connected:
            progress.update(task, description="[green]✓ Metasploit RPC connected")
        else:
            progress.update(task, description="[yellow]⚠ Metasploit RPC not available")
        
        # Step 5: Ollama/LLM
        task = progress.add_task("[cyan]Connecting to LLM...", total=None)
        ctx.ollama_connected = await check_ollama_connection()
        if ctx.ollama_connected:
            progress.update(task, description=f"[green]✓ LLM ready ({settings.model})")
            ctx.model_loaded = True
        else:
            progress.update(task, description="[yellow]⚠ LLM not available - check Ollama")
    
    # Summary
    console.print()
    if ctx.known_hosts:
        console.print(f"[dim]Known targets: {', '.join(ctx.known_hosts[:5])}{'...' if len(ctx.known_hosts) > 5 else ''}[/]")
    if ctx.missing_tools:
        console.print(f"[dim yellow]Missing tools: {', '.join(ctx.missing_tools[:5])}[/]")
    console.print()
    
    return ctx
