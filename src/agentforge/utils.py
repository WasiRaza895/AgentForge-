import shutil
import subprocess
import re
from pathlib import Path
from typing import Tuple, Optional, Union

def get_config_dir() -> Path:
    """Returns the path to the ~/.agentforge config directory."""
    return Path.home() / ".agentforge"

def ensure_config_dir() -> Path:
    """Creates the ~/.agentforge directory if it does not exist, setting permissions to owner-only."""
    config_dir = get_config_dir()
    if not config_dir.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
        try:
            # Set directory permissions to owner read/write/execute only (0o700)
            config_dir.chmod(0o700)
        except Exception:
            pass
    return config_dir

def check_tool_installed(tool_name: str) -> bool:
    """Checks if a CLI tool exists in the system's PATH."""
    return shutil.which(tool_name) is not None

def run_command(cmd: Union[str, list], capture: bool = True) -> Tuple[bool, str]:
    """Runs a shell command and returns a tuple of (success, output_string)."""
    shell = isinstance(cmd, str)
    try:
        if capture:
            result = subprocess.run(
                cmd,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            output = (result.stdout or "") + (result.stderr or "")
            success = result.returncode == 0
            return success, output.strip()
        else:
            result = subprocess.run(cmd, shell=shell, check=False)
            return result.returncode == 0, ""
    except Exception as e:
        return False, str(e)

def sanitize_text(text: str) -> str:
    """Strips HTML tags, normalizes whitespace, and cleans up text for agents."""
    if not text:
        return ""
    # Strip HTML tags
    text = re.sub(r'<[^>]*>', ' ', text)
    # Normalize multiple whitespace/newlines
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def truncate(text: str, max_length: int = 1000) -> str:
    """Truncates text to max_length characters with an ellipsis if it exceeds the limit."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"\n... [Truncated {len(text) - max_length} chars]"
