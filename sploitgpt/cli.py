"""
SploitGPT CLI Entry Point
"""

import asyncio
import sys

from rich.console import Console

from sploitgpt.core.boot import boot_sequence
from sploitgpt.tui.app import SploitGPTApp

console = Console()


def print_banner() -> None:
    """Print the SploitGPT banner."""
    banner = """
[bold red] ███████╗██████╗ ██╗      ██████╗ ██╗████████╗ ██████╗ ██████╗ ████████╗[/]
[bold red] ██╔════╝██╔══██╗██║     ██╔═══██╗██║╚══██╔══╝██╔════╝ ██╔══██╗╚══██╔══╝[/]
[bold red] ███████╗██████╔╝██║     ██║   ██║██║   ██║   ██║  ███╗██████╔╝   ██║   [/]
[bold red] ╚════██║██╔═══╝ ██║     ██║   ██║██║   ██║   ██║   ██║██╔═══╝    ██║   [/]
[bold red] ███████║██║     ███████╗╚██████╔╝██║   ██║   ╚██████╔╝██║        ██║   [/]
[bold red] ╚══════╝╚═╝     ╚══════╝ ╚═════╝ ╚═╝   ╚═╝    ╚═════╝ ╚═╝        ╚═╝   [/]
                                                                         
[dim]            [ Autonomous AI Penetration Testing Framework ][/]
"""
    console.print(banner)


async def async_main() -> int:
    """Async main entry point."""
    print_banner()
    
    # Run boot sequence
    console.print("\n[bold cyan]Initializing SploitGPT...[/]\n")
    
    try:
        context = await boot_sequence()
    except Exception as e:
        console.print(f"[bold red]Boot failed:[/] {e}")
        return 1
    
    # Launch TUI
    app = SploitGPTApp(context=context)
    await app.run_async()
    
    return 0


def main() -> int:
    """Main entry point."""
    try:
        return asyncio.run(async_main())
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye.[/]")
        return 0


if __name__ == "__main__":
    sys.exit(main())
