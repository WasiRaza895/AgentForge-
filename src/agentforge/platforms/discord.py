import httpx
from typing import Dict, Any, List
from agentforge.platforms.base import BasePlatform
from agentforge.vault import CredentialVault

class DiscordPlatform(BasePlatform):
    name = "discord"
    description = "Send notifications and messages to Discord channels via Webhooks."
    supports_read = False
    supports_write = True
    supports_search = False
    requires_auth = True
    auth_type = "webhook"

    def read(self, target: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("Discord platform does not support read operations directly. Use write/send.")

    def write(self, content: str, **kwargs) -> Dict[str, Any]:
        """Sends a message to Discord via webhook."""
        vault = CredentialVault()
        webhook_url = kwargs.get("webhook_url") or vault.get("discord", "webhook_url")

        if not webhook_url:
            return {
                "platform": self.name,
                "action": "send",
                "success": False,
                "error": "Discord Webhook URL is missing. Configure 'webhook_url' in Vault."
            }

        payload = {
            "content": content
        }
        
        # Support username, avatar, and embeds customization
        if "username" in kwargs:
            payload["username"] = kwargs["username"]
        if "avatar_url" in kwargs:
            payload["avatar_url"] = kwargs["avatar_url"]
        if "embeds" in kwargs:
            payload["embeds"] = kwargs["embeds"]
        if "tts" in kwargs:
            payload["tts"] = kwargs["tts"]

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(webhook_url, json=payload)
                if response.status_code in (200, 204):
                    return {
                        "platform": self.name,
                        "action": "send",
                        "success": True,
                        "notes": "Message sent successfully to Discord."
                    }
                else:
                    return {
                        "platform": self.name,
                        "action": "send",
                        "success": False,
                        "error": f"Discord returned error status {response.status_code}: {response.text}"
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
        webhook_url = vault.get("discord", "webhook_url")
        if webhook_url:
            return {
                "platform": self.name,
                "status": "Ready",
                "tool": "Discord Webhook",
                "auth": "Configured",
                "notes": "Discord integration is ready."
            }
        else:
            return {
                "platform": self.name,
                "status": "Not Configured",
                "tool": "Discord Webhook",
                "auth": "Missing",
                "notes": "Discord Webhook URL is missing. Configure using: 'agentforge vault set discord webhook_url YOUR_URL'"
            }
