import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from agentforge.platforms import get_platform, list_platforms
from agentforge.utils import check_tool_installed

class Doctor:
    """Diagnostic suite to check system dependencies, platform connections, and Vault configs."""
    
    def __init__(self):
        self.console = Console()

    def run_system_checks(self) -> bool:
        """Performs system checks for Python and core package dependencies."""
        self.console.print("[bold blue]Checking System Environment...[/bold blue]")
        
        table = Table(title="System Environment Diagnostics")
        table.add_column("Check", style="cyan")
        table.add_column("Status")
        table.add_column("Details")

        # Python Version
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        table.add_row("Python Version", "[green]OK[/green]", py_ver)

        # Pip check
        has_pip = check_tool_installed("pip")
        table.add_row("pip Package Manager", "[green]OK[/green]" if has_pip else "[red]Missing[/red]", "Required for installs" if has_pip else "Install pip first")

        # Node check
        has_node = check_tool_installed("node")
        table.add_row("Node.js Runtime", "[green]OK[/green]" if has_node else "[yellow]Optional[/yellow]", "Found" if has_node else "Optional, required for certain JS-based MCP tools")

        self.console.print(table)
        return True

    def run_platform_checks(self) -> None:
        """Queries and checks status of every registered integration platform."""
        self.console.print("\n[bold blue]Diagnosing Platform Connectors...[/bold blue]")
        
        table = Table(title="Platform Integration Health Checks")
        table.add_column("Platform", style="cyan bold")
        table.add_column("Status", style="bold")
        table.add_column("Tool", style="magenta")
        table.add_column("Auth Status", style="blue")
        table.add_column("Notes/Action Item")

        platforms = list_platforms()
        for name in platforms:
            try:
                platform = get_platform(name)
                diag = platform.doctor()
                
                status_color = {
                    "Ready": "[green]Ready[/green]",
                    "Partial": "[yellow]Partial[/yellow]",
                    "Not Configured": "[yellow]Not Configured[/yellow]",
                    "Broken": "[red]Broken[/red]"
                }.get(diag.get("status", "Broken"), "[red]Broken[/red]")
                
                table.add_row(
                    diag.get("platform", name).upper(),
                    status_color,
                    diag.get("tool", "builtin"),
                    diag.get("auth", "none"),
                    diag.get("notes", "")
                )
            except Exception as e:
                table.add_row(
                    name.upper(),
                    "[red]Broken[/red]",
                    "unknown",
                    "none",
                    f"Initialization crash: {e}"
                )

        self.console.print(table)

    def diagnose(self) -> None:
        """Executes full diagnostic suite and prints report panels."""
        self.console.print(Panel.fit(
            "[bold white]AgentForge Diagnostics Tool[/bold white]\n"
            "Checking all systems, vault configurations, and connections.",
            border_style="magenta"
        ))
        self.run_system_checks()
        self.run_platform_checks()
