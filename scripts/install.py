#!/usr/bin/env python3
"""
SploitGPT Installation Script

This script:
1. Checks system requirements
2. Downloads Ollama and required model
3. Syncs knowledge bases (MITRE ATT&CK, GTFOBins)
4. Builds training data from security sources
5. Runs install-time fine-tuning (optional)
6. Sets up Docker environment
"""

import asyncio
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Rich for pretty output
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
except ImportError:
    print("Installing rich for pretty output...")
    subprocess.run([sys.executable, "-m", "pip", "install", "rich", "-q"], check=True)
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt


console = Console()


BANNER = """
[bold red]
 ███████╗██████╗ ██╗      ██████╗ ██╗████████╗ ██████╗ ██████╗ ████████╗
 ██╔════╝██╔══██╗██║     ██╔═══██╗██║╚══██╔══╝██╔════╝ ██╔══██╗╚══██╔══╝
 ███████╗██████╔╝██║     ██║   ██║██║   ██║   ██║  ███╗██████╔╝   ██║   
 ╚════██║██╔═══╝ ██║     ██║   ██║██║   ██║   ██║   ██║██╔═══╝    ██║   
 ███████║██║     ███████╗╚██████╔╝██║   ██║   ╚██████╔╝██║        ██║   
 ╚══════╝╚═╝     ╚══════╝ ╚═════╝ ╚═╝   ╚═╝    ╚═════╝ ╚═╝        ╚═╝   
[/bold red]
[dim]Autonomous AI Pentesting Agent with Self-Improving Capabilities[/dim]
"""


def check_gpu() -> dict:
    """Check for GPU availability."""
    result = {
        "has_nvidia": False,
        "has_amd": False,
        "vram_gb": 0,
        "recommended_model": "qwen2.5:7b",
    }
    
    # Check NVIDIA
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        if output:
            vram_mb = int(output.split("\n")[0])
            result["has_nvidia"] = True
            result["vram_gb"] = vram_mb / 1024
            
            # Recommend model based on VRAM
            if result["vram_gb"] >= 24:
                result["recommended_model"] = "qwen2.5:32b"
            elif result["vram_gb"] >= 16:
                result["recommended_model"] = "qwen2.5:14b"
            elif result["vram_gb"] >= 8:
                result["recommended_model"] = "qwen2.5:7b"
            else:
                result["recommended_model"] = "qwen2.5:3b"
                
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Check AMD (ROCm)
    try:
        output = subprocess.check_output(["rocm-smi", "--showmeminfo", "vram"], stderr=subprocess.DEVNULL)
        if b"Total" in output:
            result["has_amd"] = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return result


def check_docker() -> bool:
    """Check if Docker is installed and running."""
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_ollama() -> bool:
    """Check if Ollama is installed."""
    return shutil.which("ollama") is not None


def install_ollama() -> bool:
    """Install Ollama."""
    console.print("\n[yellow]Installing Ollama...[/yellow]")
    
    system = platform.system().lower()
    
    if system == "linux":
        cmd = "curl -fsSL https://ollama.com/install.sh | sh"
    elif system == "darwin":
        cmd = "brew install ollama"
    else:
        console.print("[red]Please install Ollama manually from https://ollama.com[/red]")
        return False
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError:
        console.print("[red]Failed to install Ollama[/red]")
        return False


def start_ollama() -> bool:
    """Start Ollama service."""
    try:
        # Check if already running
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/version"],
            capture_output=True
        )
        if result.returncode == 0:
            return True
        
        # Start in background
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Wait for it to start
        import time
        for _ in range(30):
            time.sleep(1)
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/version"],
                capture_output=True
            )
            if result.returncode == 0:
                return True
        
        return False
        
    except Exception as e:
        console.print(f"[red]Failed to start Ollama: {e}[/red]")
        return False


def pull_model(model: str) -> bool:
    """Pull an Ollama model."""
    console.print(f"\n[yellow]Pulling model {model}...[/yellow]")
    console.print("[dim]This may take a while depending on your connection speed.[/dim]")
    
    try:
        subprocess.run(["ollama", "pull", model], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


async def sync_knowledge_bases():
    """Sync MITRE ATT&CK and other knowledge bases."""
    from sploitgpt.knowledge import sync_attack_data
    from sploitgpt.knowledge.gtfobins import download_gtfobins_data
    
    console.print("\n[yellow]Syncing knowledge bases...[/yellow]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # MITRE ATT&CK
        task = progress.add_task("Downloading MITRE ATT&CK data...", total=None)
        try:
            count = await sync_attack_data(force=True)
            progress.update(task, description=f"[green]✓ Loaded {count} ATT&CK techniques[/green]")
        except Exception as e:
            progress.update(task, description=f"[red]✗ ATT&CK sync failed: {e}[/red]")
        
        # GTFOBins
        task = progress.add_task("Downloading GTFOBins data...", total=None)
        try:
            count = await download_gtfobins_data()
            progress.update(task, description=f"[green]✓ Loaded {count} GTFOBins entries[/green]")
        except Exception as e:
            progress.update(task, description=f"[red]✗ GTFOBins sync failed: {e}[/red]")


async def build_training_data():
    """Build training data from security sources."""
    from scripts.build_training_data import main as build_data
    
    console.print("\n[yellow]Building training data...[/yellow]")
    
    try:
        await build_data()
        console.print("[green]✓ Training data built successfully[/green]")
    except Exception as e:
        console.print(f"[red]✗ Failed to build training data: {e}[/red]")


async def run_finetuning(model: str):
    """Run install-time fine-tuning."""
    from sploitgpt.training.finetune import InstallTimeFineTuner
    
    console.print("\n[yellow]Running fine-tuning...[/yellow]")
    console.print("[dim]This will create a security-specialized version of your model.[/dim]")
    
    try:
        finetuner = InstallTimeFineTuner(
            base_model=model,
            output_name="sploitgpt"
        )
        
        success = await finetuner.run_finetuning()
        
        if success:
            console.print("[green]✓ Fine-tuning completed![/green]")
            console.print("[dim]Your model is now specialized for penetration testing.[/dim]")
            return "sploitgpt"
        else:
            console.print("[yellow]⚠ Fine-tuning skipped or failed, using base model[/yellow]")
            return model
            
    except Exception as e:
        console.print(f"[red]✗ Fine-tuning failed: {e}[/red]")
        return model


def build_docker_image():
    """Build the Docker image."""
    console.print("\n[yellow]Building Docker image...[/yellow]")
    console.print("[dim]This creates a Kali Linux container with all pentesting tools.[/dim]")
    
    try:
        subprocess.run(
            ["docker", "build", "-t", "sploitgpt", "."],
            check=True
        )
        console.print("[green]✓ Docker image built successfully[/green]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Failed to build Docker image: {e}[/red]")
        return False


def create_env_file(model: str, ollama_host: str = "http://host.docker.internal:11434"):
    """Create .env file with configuration."""
    env_content = f"""# SploitGPT Configuration
SPLOITGPT_OLLAMA_HOST={ollama_host}
SPLOITGPT_MODEL={model}
SPLOITGPT_LLM_MODEL=ollama/{model}
SPLOITGPT_DEBUG=false
SPLOITGPT_AUTO_TRAIN=true
"""
    
    env_path = Path(".env")
    env_path.write_text(env_content)
    console.print(f"[green]✓ Configuration saved to {env_path}[/green]")


async def main():
    """Main installation routine."""
    console.print(Panel(BANNER, border_style="red"))
    console.print("\n[bold]Welcome to SploitGPT Installation![/bold]\n")
    
    # Check GPU
    console.print("[cyan]Checking system...[/cyan]")
    gpu_info = check_gpu()
    
    if gpu_info["has_nvidia"]:
        console.print(f"[green]✓ NVIDIA GPU detected with {gpu_info['vram_gb']:.1f}GB VRAM[/green]")
    elif gpu_info["has_amd"]:
        console.print("[green]✓ AMD GPU detected (ROCm)[/green]")
    else:
        console.print("[yellow]⚠ No GPU detected, will use CPU (slower)[/yellow]")
    
    console.print(f"[dim]Recommended model: {gpu_info['recommended_model']}[/dim]")
    
    # Check Docker
    if check_docker():
        console.print("[green]✓ Docker is installed and running[/green]")
    else:
        console.print("[red]✗ Docker is not available[/red]")
        console.print("[dim]Please install Docker: https://docs.docker.com/get-docker/[/dim]")
        if not Confirm.ask("Continue without Docker? (limited functionality)"):
            return
    
    # Install/check Ollama
    if check_ollama():
        console.print("[green]✓ Ollama is installed[/green]")
    else:
        console.print("[yellow]⚠ Ollama not found[/yellow]")
        if Confirm.ask("Install Ollama now?"):
            if not install_ollama():
                console.print("[red]Failed to install Ollama[/red]")
                return
    
    # Start Ollama
    console.print("\n[cyan]Starting Ollama service...[/cyan]")
    if not start_ollama():
        console.print("[red]Failed to start Ollama[/red]")
        return
    console.print("[green]✓ Ollama is running[/green]")
    
    # Model selection
    model = Prompt.ask(
        "\n[cyan]Select model[/cyan]",
        default=gpu_info["recommended_model"],
        choices=["qwen2.5:3b", "qwen2.5:7b", "qwen2.5:14b", "qwen2.5:32b"]
    )
    
    # Pull model
    if not pull_model(model):
        console.print(f"[red]Failed to pull {model}[/red]")
        return
    console.print(f"[green]✓ Model {model} is ready[/green]")
    
    # Sync knowledge bases
    await sync_knowledge_bases()
    
    # Build training data
    if Confirm.ask("\n[cyan]Build training data from security sources?[/cyan]", default=True):
        await build_training_data()
    
    # Fine-tuning (optional)
    final_model = model
    if Confirm.ask("\n[cyan]Run install-time fine-tuning?[/cyan] (recommended, ~30 min)", default=True):
        final_model = await run_finetuning(model)
    
    # Build Docker image
    if check_docker():
        if Confirm.ask("\n[cyan]Build Docker image?[/cyan]", default=True):
            build_docker_image()
    
    # Create config
    create_env_file(final_model)
    
    # Done!
    console.print(Panel(
        f"""
[bold green]Installation Complete![/bold green]

[cyan]To start SploitGPT:[/cyan]

  [bold]Docker (recommended):[/bold]
    docker-compose up -d
    docker exec -it sploitgpt sploitgpt

  [bold]Local development:[/bold]
    source .venv/bin/activate
    python -m sploitgpt

[dim]Model: {final_model}[/dim]
[dim]Documentation: https://github.com/cheeseman2422/SploitGPT[/dim]
        """,
        title="🎉 Ready!",
        border_style="green"
    ))


if __name__ == "__main__":
    asyncio.run(main())
