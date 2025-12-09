"""
SploitGPT TUI Application
"""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Header, Input, RichLog, Static

from sploitgpt.core.boot import BootContext
from sploitgpt.agent import Agent


class PromptInput(Input):
    """Custom input for the command prompt."""
    
    BINDINGS = [
        Binding("up", "history_prev", "Previous command", show=False),
        Binding("down", "history_next", "Next command", show=False),
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.history: list[str] = []
        self.history_index: int = -1
    
    def action_history_prev(self) -> None:
        """Go to previous command in history."""
        if self.history and self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.value = self.history[-(self.history_index + 1)]
    
    def action_history_next(self) -> None:
        """Go to next command in history."""
        if self.history_index > 0:
            self.history_index -= 1
            self.value = self.history[-(self.history_index + 1)]
        elif self.history_index == 0:
            self.history_index = -1
            self.value = ""


class StatusBar(Static):
    """Status bar showing current state."""
    
    def __init__(self, context: BootContext):
        super().__init__()
        self.context = context
    
    def compose(self) -> ComposeResult:
        msf = "[green]MSF[/]" if self.context.msf_connected else "[red]MSF[/]"
        llm = "[green]LLM[/]" if self.context.ollama_connected else "[red]LLM[/]"
        hosts = f"[cyan]{len(self.context.known_hosts)}[/] hosts"
        
        yield Static(f" {msf} | {llm} | {hosts} ")


class SploitGPTApp(App):
    """Main SploitGPT TUI Application."""
    
    TITLE = "SploitGPT"
    SUB_TITLE = "Autonomous AI Penetration Testing"
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #output {
        height: 1fr;
        border: solid $primary;
        padding: 0 1;
    }
    
    #input-container {
        height: 3;
        padding: 0 1;
    }
    
    #prompt-label {
        width: auto;
        color: $success;
        padding: 0 1 0 0;
    }
    
    #prompt-input {
        width: 1fr;
    }
    
    #status-bar {
        height: 1;
        dock: bottom;
        background: $surface-darken-1;
    }
    
    .choice-button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear", "Clear"),
    ]
    
    def __init__(self, context: BootContext):
        super().__init__()
        self.context = context
        self.agent = Agent(context)
        self.awaiting_choice = False
        self.choice_callback = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            RichLog(id="output", highlight=True, markup=True),
            Horizontal(
                Static("sploitgpt > ", id="prompt-label"),
                PromptInput(id="prompt-input", placeholder="Enter command or /help"),
                id="input-container"
            ),
        )
        yield Footer()
    
    async def on_mount(self) -> None:
        """Called when app is mounted."""
        output = self.query_one("#output", RichLog)
        
        # Welcome message
        output.write("[bold red]SploitGPT[/] [dim]v0.1.0[/]")
        output.write("")
        
        if self.context.ollama_connected:
            output.write(f"[green]✓[/] LLM ready: {self.context.model_loaded}")
        else:
            output.write("[yellow]⚠[/] LLM not connected - run 'ollama serve' on host")
        
        if self.context.msf_connected:
            output.write("[green]✓[/] Metasploit RPC connected")
        else:
            output.write("[yellow]⚠[/] Metasploit RPC not available")
        
        if self.context.known_hosts:
            output.write(f"[cyan]ℹ[/] {len(self.context.known_hosts)} known hosts from prior recon")
        
        output.write("")
        output.write("[dim]Type a command, or prefix with / for AI assistance[/]")
        output.write("[dim]Examples: nmap -sV 10.0.0.1  |  /scan the network  |  /help[/]")
        output.write("")
        
        # Focus input
        self.query_one("#prompt-input", PromptInput).focus()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission."""
        if event.input.id != "prompt-input":
            return
        
        command = event.value.strip()
        if not command:
            return
        
        # Add to history
        prompt_input = self.query_one("#prompt-input", PromptInput)
        prompt_input.history.append(command)
        prompt_input.history_index = -1
        prompt_input.value = ""
        
        output = self.query_one("#output", RichLog)
        output.write(f"[bold green]>[/] {command}")
        
        # Check if it's an AI command or direct shell
        if command.startswith("/"):
            await self.handle_agent_command(command[1:])
        else:
            await self.handle_shell_command(command)
    
    async def handle_shell_command(self, command: str) -> None:
        """Execute a direct shell command."""
        output = self.query_one("#output", RichLog)
        
        try:
            import asyncio
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            stdout, _ = await proc.communicate()
            result = stdout.decode() if stdout else ""
            
            if result:
                for line in result.split("\n"):
                    output.write(line)
        except Exception as e:
            output.write(f"[red]Error:[/] {e}")
    
    async def handle_agent_command(self, command: str) -> None:
        """Handle an AI-assisted command."""
        output = self.query_one("#output", RichLog)
        
        if command.lower() == "help":
            output.write("")
            output.write("[bold cyan]SploitGPT Commands[/]")
            output.write("")
            output.write("  [bold]/scan[/] <target>     - Scan a target")
            output.write("  [bold]/enumerate[/] <target> - Enumerate services")
            output.write("  [bold]/exploit[/] <target>   - Find and run exploits")
            output.write("  [bold]/privesc[/]            - Privilege escalation")
            output.write("  [bold]/help[/]               - Show this help")
            output.write("")
            output.write("[dim]Or just describe what you want in natural language:[/]")
            output.write("[dim]  /find sql injection vulnerabilities on 10.0.0.1[/]")
            output.write("")
            return
        
        if not self.context.ollama_connected:
            output.write("[red]Error:[/] LLM not connected. Start Ollama first.")
            return
        
        output.write("[dim]Thinking...[/]")
        
        # Process with agent
        try:
            async for response in self.agent.process(command):
                if response.type == "message":
                    output.write(response.content)
                elif response.type == "command":
                    output.write(f"[cyan]$[/] {response.content}")
                elif response.type == "result":
                    for line in response.content.split("\n"):
                        output.write(f"  {line}")
                elif response.type == "choice":
                    output.write("")
                    output.write(f"[bold yellow]{response.question}[/]")
                    for i, option in enumerate(response.options, 1):
                        output.write(f"  [bold][{i}][/] {option}")
                    output.write("")
                    # TODO: Handle choice input
                elif response.type == "error":
                    output.write(f"[red]Error:[/] {response.content}")
        except Exception as e:
            output.write(f"[red]Agent error:[/] {e}")
    
    def action_clear(self) -> None:
        """Clear the output."""
        self.query_one("#output", RichLog).clear()
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
