"""Credentials and reviewed write actions exposed by the local Studio."""

from threading import Lock
from urllib.parse import urlsplit

from agentforge import utils
from agentforge.pipeline import Pipeline
from agentforge.vault import CredentialVault


CONNECTIONS = {
    "github": ("github", "token"),
    "slack": ("slack", "webhook_url"),
    "exa": ("search", "exa_key"),
}
VAULT_LOCK = Lock()


class MissingConnection(ValueError):
    def __init__(self, provider: str):
        super().__init__("Add the service credential in Service Connections to continue.")
        self.provider = provider


def _is_slack_webhook(value: str) -> bool:
    try:
        url = urlsplit(value)
        return (
            url.scheme == "https" and url.netloc in {"hooks.slack.com", "hooks.slack-gov.com"}
            and url.path.startswith("/services/") and len(url.path.split("/")) == 5
            and all(url.path.split("/")[2:]) and not url.query and not url.fragment
        )
    except ValueError:
        return False


def _configured(vault: CredentialVault, name: str) -> bool:
    credential = vault.get(*CONNECTIONS[name])
    if name == "slack":
        return bool(credential and _is_slack_webhook(credential))
    if name == "exa":
        key = credential or vault.get("exa", "api_key")
        return bool(key and not key.startswith("AIza"))
    return bool(credential)


def connection_status() -> dict[str, bool]:
    with VAULT_LOCK:
        if not (utils.get_config_dir() / "credentials.json").is_file():
            return dict.fromkeys(CONNECTIONS, False)
        vault = CredentialVault()
        return {name: _configured(vault, name) for name in CONNECTIONS}


def save_connection(provider: str, credential: str) -> None:
    if provider not in CONNECTIONS:
        raise ValueError("Choose GitHub, Slack, or Exa.")
    credential = credential.strip()
    if not credential or len(credential) > 1000 or any(char.isspace() for char in credential):
        raise ValueError("Enter a credential without spaces or line breaks.")
    if provider == "slack" and not _is_slack_webhook(credential):
        raise ValueError("Paste an HTTPS Slack incoming webhook URL with a /services/ path.")
    if provider == "exa" and credential.startswith("AIza"):
        raise ValueError("Paste Google Gemini keys into the AI Model section above.")

    with VAULT_LOCK:
        CredentialVault().set(*CONNECTIONS[provider], credential)


def run_reviewed_action(provider: str, confirmed: bool, repo: str, title: str, content: str) -> dict:
    if provider not in {"github", "slack"}:
        raise ValueError("Choose a GitHub issue or a Slack message.")
    if confirmed is not True:
        raise ValueError("Review and confirm the destination and content before running an action.")
    if not connection_status()[provider]:
        raise MissingConnection(provider)

    if provider == "github":
        if not repo.strip() or not title.strip():
            raise ValueError("Enter the repository and issue title.")
        name = "Create a GitHub issue"
        step = {"platform": "github", "action": "create-issue", "params": {
            "repo": repo.strip(), "title": title.strip(), "content": content, "use_api": True,
        }}
    else:
        if not content.strip():
            raise ValueError("Enter a Slack message.")
        name = "Send a Slack message"
        step = {"platform": "slack", "action": "send", "params": {"content": content}}

    report = Pipeline(config_dict={"name": name, "steps": [step]}).run()
    outcome = report["log"][0].get("result", {})
    if not report["success"]:
        message = outcome.get("error") if provider == "github" else None
        return {"success": False, "error": message or "The service did not confirm the action. Check the destination before retrying."}
    if provider == "github":
        return {"success": True, "message": "GitHub issue created.", "url": outcome.get("url")}
    return {"success": True, "message": "Message sent to the Slack channel associated with your webhook."}
