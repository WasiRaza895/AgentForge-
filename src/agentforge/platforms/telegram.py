import httpx
from typing import Dict, Any, List
from agentforge.platforms.base import BasePlatform
from agentforge.vault import CredentialVault

class TelegramPlatform(BasePlatform):
    name = "telegram"
    description = "Send messages and notifications to Telegram chats/channels using Bot API."
    supports_read = False
    supports_write = True
    supports_search = False
    requires_auth = True
    auth_type = "token"

    def read(self, target: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("Telegram platform does not support read operations directly. Use write/send.")

    def write(self, content: str, **kwargs) -> Dict[str, Any]:
        """Sends a message to a Telegram chat/channel."""
        vault = CredentialVault()
        token = kwargs.get("bot_token") or vault.get("telegram", "bot_token")
        chat_id = kwargs.get("chat_id") or vault.get("telegram", "chat_id")
        parse_mode = kwargs.get("parse_mode", "Markdown")

        if not token or not chat_id:
            return {
                "platform": self.name,
                "action": "send",
                "success": False,
                "error": "Telegram credentials (bot_token, chat_id) are missing. Configure in Vault."
            }

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": content,
            "parse_mode": parse_mode
        }
        
        # Support other sendMessage options
        if "disable_web_page_preview" in kwargs:
            payload["disable_web_page_preview"] = kwargs["disable_web_page_preview"]
        if "disable_notification" in kwargs:
            payload["disable_notification"] = kwargs["disable_notification"]

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload)
                res_data = response.json()
                if response.status_code == 200 and res_data.get("ok"):
                    return {
                        "platform": self.name,
                        "action": "send",
                        "success": True,
                        "message_id": res_data.get("result", {}).get("message_id")
                    }
                else:
                    return {
                        "platform": self.name,
                        "action": "send",
                        "success": False,
                        "error": f"Telegram API Error: {res_data.get('description', response.text)}"
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
        token = vault.get("telegram", "bot_token")
        chat_id = vault.get("telegram", "chat_id")
        
        if token and chat_id:
            return {
                "platform": self.name,
                "status": "Ready",
                "tool": "Telegram Bot API",
                "auth": "Configured",
                "notes": f"Configured bot for chat/channel {chat_id}."
            }
        else:
            return {
                "platform": self.name,
                "status": "Not Configured",
                "tool": "Telegram Bot API",
                "auth": "Missing",
                "notes": "Telegram credentials are missing. Configure using: 'agentforge vault set telegram bot_token YOUR_TOKEN'"
            }
