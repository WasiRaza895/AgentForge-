import httpx
from typing import Dict, Any, List
from agentforge.platforms.base import BasePlatform
from agentforge.vault import CredentialVault

class SlackPlatform(BasePlatform):
    name = "slack"
    description = "Send notifications and post messages to Slack via Incoming Webhooks."
    supports_read = False
    supports_write = True
    supports_search = False
    requires_auth = True
    auth_type = "webhook"

    def read(self, target: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("Slack platform does not support read operations directly. Use write/send.")

    def write(self, content: str, **kwargs) -> Dict[str, Any]:
        """Sends a message to a Slack channel via webhook."""
        vault = CredentialVault()
        webhook_url = kwargs.get("webhook_url") or vault.get("slack", "webhook_url")

        if not webhook_url:
            return {
                "platform": self.name,
                "action": "send",
                "success": False,
                "error": "Slack Incoming Webhook URL is missing. Configure 'webhook_url' in Vault."
            }

        payload = {
            "text": content
        }
        
        # Support Slack block formatting or user customizations
        if "blocks" in kwargs:
            payload["blocks"] = kwargs["blocks"]
        if "channel" in kwargs:
            payload["channel"] = kwargs["channel"]
        if "username" in kwargs:
            payload["username"] = kwargs["username"]
        if "icon_emoji" in kwargs:
            payload["icon_emoji"] = kwargs["icon_emoji"]

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(webhook_url, json=payload)
                if response.status_code == 200 and response.text.strip() == "ok":
                    return {
                        "platform": self.name,
                        "action": "send",
                        "success": True,
                        "notes": "Message sent successfully."
                    }
                else:
                    return {
                        "platform": self.name,
                        "action": "send",
                        "success": False,
                        "error": f"Slack returned error status {response.status_code}: {response.text}"
                    }
        except Exception as e:
            return {
                "platform": self.name,
                "action": "send",
                "success": False,
                "error": str(e)
            }

    def doctor(self) -> Dict[str, Any]:
        vault = CredentialVault()
        webhook_url = vault.get("slack", "webhook_url")
        if webhook_url:
            return {
                "platform": self.name,
                "status": "Ready",
                "tool": "Slack Webhook",
                "auth": "Configured",
                "notes": "Slack integration is ready to send notifications."
            }
        else:
            return {
                "platform": self.name,
                "status": "Not Configured",
                "tool": "Slack Webhook",
                "auth": "Missing",
                "notes": "Slack Webhook URL is missing. Configure using: 'agentforge vault set slack webhook_url YOUR_URL'"
            }
