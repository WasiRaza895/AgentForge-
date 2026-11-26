import os
import json
import re
import httpx
from typing import Dict, Any, List
from agentforge.platforms.base import BasePlatform
from agentforge.utils import run_command, check_tool_installed
from agentforge.vault import CredentialVault

class GitHubPlatform(BasePlatform):
    name = "github"
    description = "Interact with GitHub. Read issues, repos, search, create issues/PRs, and comment using gh CLI."
    supports_read = True
    supports_write = True
    supports_search = True
    requires_auth = True
    auth_type = "token"

    def _get_env(self) -> Dict[str, str]:
        """Gets environment dictionary including GITHUB_TOKEN if configured in Vault."""
        env = os.environ.copy()
        vault = CredentialVault()
        token = vault.get("github", "token")
        if token:
            env["GITHUB_TOKEN"] = token
        return env

    def _run_gh_cmd(self, args_str: str) -> tuple[bool, str]:
        """Runs a gh CLI command with environment variable support."""
        if not check_tool_installed("gh"):
            return False, "GitHub CLI ('gh') is not installed."
        
        # Build command list
        cmd = f"gh {args_str}"
        env = self._get_env()
        
        try:
            import subprocess
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                check=False
            )
            output = (result.stdout or "") + (result.stderr or "")
            return result.returncode == 0, output.strip()
        except Exception as e:
            return False, str(e)

    def read(self, target: str, **kwargs) -> Dict[str, Any]:
        """Reads info about a repository, issue, or pull request.
        
        target format: 'owner/repo' or 'owner/repo/issues/123'
        """
        action = kwargs.get("action", "repo")
        
        if "/" not in target:
            return {
                "platform": self.name,
                "action": "read",
                "success": False,
                "error": "Invalid repository target format. Expected 'owner/repo'."
            }

        parts = target.strip("/").split("/")
        if len(parts) >= 4 and parts[2] in ("issues", "pull"):
            # Reading a specific issue/PR
            issue_num = parts[3]
            repo = f"{parts[0]}/{parts[1]}"
            cmd_type = "issue" if parts[2] == "issues" else "pr"
            success, output = self._run_gh_cmd(f"{cmd_type} view {issue_num} -R {repo} --json title,body,state,comments,author")
        else:
            # Reading repository details or README
            repo = f"{parts[0]}/{parts[1]}"
            if action == "readme":
                success, output = self._run_gh_cmd(f"repo view {repo} --web=false --json readme")
            else:
                success, output = self._run_gh_cmd(f"repo view {repo} --json name,description,stargazerCount,owner,url")

        if not success:
            return {
                "platform": self.name,
                "action": "read",
                "success": False,
                "error": output
            }

        try:
            return {
                "platform": self.name,
                "action": "read",
                "success": True,
                "data": json.loads(output)
            }
        except Exception:
            return {
                "platform": self.name,
                "action": "read",
                "success": True,
                "raw_data": output
            }

    def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Searches GitHub repositories."""
        limit = kwargs.get("limit", 10)
        success, output = self._run_gh_cmd(f"search repos \"{query}\" --limit {limit} --json nwo,description,stargazersCount,url")
        if not success:
            return [{"error": output}]
        try:
            return json.loads(output)
        except Exception:
            return [{"raw": output}]

    def _create_issue_api(self, repo: str, title: str, body: str) -> Dict[str, Any]:
        result = {"platform": self.name, "action": "create-issue", "success": False}
        if not re.fullmatch(r"[a-zA-Z0-9-]+/[a-zA-Z0-9_.-]+", repo) or repo.split("/")[1] in {".", ".."}:
            return {**result, "error": "Enter a GitHub repository as owner/repo."}

        token = CredentialVault().get("github", "token")
        if not token:
            return {**result, "error": "Add a GitHub access token to the local vault."}

        try:
            response = httpx.post(
                f"https://api.github.com/repos/{repo}/issues",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2026-03-10",
                },
                json={"title": title, "body": body},
                timeout=12.0,
            )
        except httpx.HTTPError:
            return {**result, "error": "GitHub did not confirm the issue. Check the repository before retrying."}

        if response.status_code != 201:
            return {**result, "error": f"GitHub returned HTTP {response.status_code}. Check the repository and token permissions."}

        try:
            url = response.json().get("html_url")
        except (AttributeError, ValueError):
            url = None
        return {**result, "success": True, "url": url}

    def write(self, content: str, **kwargs) -> Dict[str, Any]:
        """Creates an issue, PR, or comments on an issue.
        
        Expected kwargs:
            action: 'create-issue', 'create-pr', 'comment'
            repo: 'owner/repo'
            title: str (required for issue/PR)
            issue_number: int/str (required for comment)
        """
        action = kwargs.get("action", "create-issue")
        repo = kwargs.get("repo")
        
        if not repo:
            return {
                "platform": self.name,
                "action": "write",
                "success": False,
                "error": "Missing 'repo' argument (format: owner/repo)."
            }

        if action == "create-issue":
            title = kwargs.get("title", "New Issue")
            if kwargs.get("use_api"):
                return self._create_issue_api(repo, title, content)
            success, output = self._run_gh_cmd(f"issue create -R {repo} -t \"{title}\" -b \"{content}\"")
        elif action == "create-pr":
            title = kwargs.get("title", "New Pull Request")
            # Assumes current git repo state has upstream branch
            success, output = self._run_gh_cmd(f"pr create -R {repo} -t \"{title}\" -b \"{content}\"")
        elif action == "comment":
            issue_num = kwargs.get("issue_number")
            if not issue_num:
                return {
                    "platform": self.name,
                    "action": "write",
                    "success": False,
                    "error": "Missing 'issue_number' for comment action."
                }
            success, output = self._run_gh_cmd(f"issue comment {issue_num} -R {repo} -b \"{content}\"")
        else:
            return {
                "platform": self.name,
                "action": "write",
                "success": False,
                "error": f"Unsupported write action: {action}"
            }

        return {
            "platform": self.name,
            "action": action,
            "success": success,
            "output": output
        }

    def doctor(self) -> Dict[str, Any]:
        if not check_tool_installed("gh"):
            return {
                "platform": self.name,
                "status": "Broken",
                "tool": "gh",
                "auth": "none",
                "notes": "GitHub CLI ('gh') is not installed. Install via: scoop/brew/winget install gh"
            }
            
        success, output = self._run_gh_cmd("auth status")
        has_vault_token = bool(CredentialVault().get("github", "token"))
        
        if success or has_vault_token:
            notes = "Authenticated via Vault GITHUB_TOKEN" if has_vault_token else "Authenticated via gh login"
            return {
                "platform": self.name,
                "status": "Ready",
                "tool": "gh CLI",
                "auth": "Authenticated",
                "notes": notes
            }
        else:
            return {
                "platform": self.name,
                "status": "Not Configured",
                "tool": "gh CLI",
                "auth": "Missing",
                "notes": "Not authenticated. Run 'gh auth login' or save token to Vault: 'agentforge vault set github token YOUR_TOKEN'"
            }

    def get_required_tools(self) -> List[str]:
        return ["gh"]
