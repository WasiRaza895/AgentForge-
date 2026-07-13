import httpx
from typing import Dict, Any, List
from agentforge.vault import CredentialVault
from agentforge.platforms import get_platform

class Notifier:
    """Dispatches notifications across configured communication channels (Slack, Discord, Telegram, Email, Webhooks)."""
    
    def __init__(self):
        self.vault = CredentialVault()

    def setup_channel(self, channel_name: str, channel_type: str, **config) -> None:
        """Configures a notification channel by saving settings into the Vault."""
        # channel_name: e.g. 'slack-research' or 'admin-email'
        # channel_type: 'slack', 'discord', 'telegram', 'email', 'webhook'
        self.vault.set(f"notify_{channel_name}", "type", channel_type)
        for k, v in config.items():
            self.vault.set(f"notify_{channel_name}", k, str(v))

    def list_channels(self) -> Dict[str, Dict[str, str]]:
        """Returns all configured notification channels."""
        channels = {}
        all_creds = self.vault.list_credentials()
        for section in all_creds:
            if section.startswith("notify_"):
                name = section.replace("notify_", "")
                config = self.vault.get_all(section)
                channels[name] = config
        return channels

    def send(self, channel_name: str, message: str, **kwargs) -> Dict[str, Any]:
        """Routes a message to the configured channel name."""
        channel_config = self.vault.get_all(f"notify_{channel_name}")
        if not channel_config:
            # Check if channel name itself is a platform config, fallback to default setup
            channel_type = channel_name
            channel_config = self.vault.get_all(channel_type)
        else:
            channel_type = channel_config.get("type", "")

        if not channel_type:
            return {
                "success": False,
                "error": f"Notification channel '{channel_name}' is not configured."
            }

        # Dispatch based on channel type
        try:
            if channel_type == "slack":
                platform = get_platform("slack")
                webhook = channel_config.get("webhook_url")
                return platform.write(message, webhook_url=webhook, **kwargs)
                
            elif channel_type == "discord":
                platform = get_platform("discord")
                webhook = channel_config.get("webhook_url")
                return platform.write(message, webhook_url=webhook, **kwargs)
                
            elif channel_type == "telegram":
                platform = get_platform("telegram")
                bot_token = channel_config.get("bot_token")
                chat_id = channel_config.get("chat_id")
                return platform.write(message, bot_token=bot_token, chat_id=chat_id, **kwargs)
                
            elif channel_type == "email":
                platform = get_platform("email")
                # Merge config from notification channel and global email defaults
                smtp_config = self.vault.get_all("email")
                smtp_config.update(channel_config)
                smtp_config.update(kwargs)
                return platform.write(message, **smtp_config)
                
            elif channel_type == "webhook":
                url = channel_config.get("url")
                if not url:
                    return {"success": False, "error": "Webhook configuration is missing 'url'."}
                headers = {"Content-Type": "application/json"}
                if "headers" in channel_config:
                    try:
                        import json
                        headers.update(json.loads(channel_config["headers"]))
                    except Exception:
                        pass
                
                payload = {"message": message}
                payload.update(kwargs)
                
                with httpx.Client(timeout=10.0) as client:
                    res = client.post(url, json=payload, headers=headers)
                    return {
                        "success": res.status_code in (200, 201, 204),
                        "status_code": res.status_code,
                        "response": res.text
                    }
            else:
                return {
                    "success": False,
                    "error": f"Unsupported notification channel type: {channel_type}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
