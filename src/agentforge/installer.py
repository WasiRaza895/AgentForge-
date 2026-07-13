import sys
import shutil
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from agentforge.utils import run_command, check_tool_installed, get_config_dir
from agentforge.platforms import get_platform, list_platforms

class Installer:
    """Automated environment setup to configure dependencies, CLI tools, and agent SKILL.md files."""
    
    def __init__(self, safe_mode: bool = False):
        self.safe_mode = safe_mode
        self.console = Console()

    def install_pip_dependency(self, package: str) -> bool:
        """Installs a python package via pip."""
        self.console.print(f"   Installing python dependency: [yellow]{package}[/yellow]...")
        if self.safe_mode:
            self.console.print(f"   [bold yellow][SAFE MODE][/bold yellow] Skipped installation of '{package}'. Run: pip install {package}")
            return True
            
        success, output = run_command([sys.executable, "-m", "pip", "install", package])
        if success:
            self.console.print(f"   [green]✓[/green] Successfully installed {package}.")
        else:
            self.console.print(f"   [red]✗[/red] Failed to install {package}. Error: {output}")
        return success

    def check_and_install_cli(self, tool_name: str, install_help: str) -> bool:
        """Checks if a CLI tool exists. If not, prints installation guide."""
        if check_tool_installed(tool_name):
            self.console.print(f"   Tool [green]{tool_name}[/green] is already installed.")
            return True
            
        self.console.print(f"   [bold red]✗[/bold red] Required CLI tool [red]{tool_name}[/red] is missing.")
        self.console.print(f"     Action required: {install_help}")
        return False

    def install_dependencies(self, platform_name: str) -> bool:
        """Installs all dependencies required by a specific platform integration."""
        self.console.print(f"\n[bold blue]Setting up dependencies for platform: {platform_name.upper()}[/bold blue]")
        try:
            platform = get_platform(platform_name)
        except Exception as e:
            self.console.print(f"  [red]✗[/red] Failed to initialize platform: {e}")
            return False

        required_tools = platform.get_required_tools()
        success = True
        
        # Check CLI dependencies
        for tool in required_tools:
            if tool == "gh":
                success &= self.check_and_install_cli("gh", "Install GitHub CLI from https://cli.github.com/ or run 'scoop/brew/winget install gh'")
            elif tool == "yt-dlp":
                success &= self.check_and_install_cli("yt-dlp", "Install yt-dlp. Recommended: 'pip install yt-dlp'")
                
        # Check python dependencies mapping
        pip_dependencies = []
        if platform_name == "twitter":
            pip_dependencies = ["tweepy"]
        elif platform_name == "reddit":
            pip_dependencies = ["praw"]
        elif platform_name == "rss":
            pip_dependencies = ["feedparser"]
        elif platform_name == "web":
            pip_dependencies = ["httpx"]
            
        for pkg in pip_dependencies:
            success &= self.install_pip_dependency(pkg)
            
        return success

    def install_all(self) -> None:
        """Installs dependencies across all platforms."""
        self.console.print(Panel(
            "🔨 [bold white]AgentForge Environmental Auto-Installer[/bold white] 🔨\n"
            "Setting up all python libraries, CLI links, and configurations.",
            border_style="green"
        ))
        
        platforms = list_platforms()
        for name in platforms:
            self.install_dependencies(name)
            
        self.console.print("\n[bold green]Environment installation completed.[/bold green]")

    def setup_skill(self, workspace_path: str) -> bool:
        """Deploys AgentForge SKILL.md instruction playbook to the target workspace."""
        self.console.print(f"[bold blue]Deploying SKILL.md to workspace: {workspace_path}[/bold blue]")
        src_skill = Path(__file__).parent.parent.parent / "skill" / "SKILL.md"
        
        # Fallback locate
        if not src_skill.exists():
            src_skill = Path(workspace_path) / "skill" / "SKILL.md"
            if not src_skill.exists():
                src_skill = Path(sys.prefix) / "share" / "agentforge" / "SKILL.md"

        target_dir = Path(workspace_path) / ".agents" / "skills" / "agentforge"
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            target_file = target_dir / "SKILL.md"
            if src_skill.exists():
                shutil.copy(src_skill, target_file)
                self.console.print(f"  [green]✓[/green] Playbook successfully copied to: {target_file}")
                return True
            else:
                self.console.print(f"  [red]✗[/red] Source SKILL.md template not found.")
                return False
        except Exception as e:
            self.console.print(f"  [red]✗[/red] Failed to deploy SKILL.md: {e}")
            return False
