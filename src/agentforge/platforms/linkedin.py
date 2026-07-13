import httpx
from typing import Dict, Any, List
from agentforge.platforms.base import BasePlatform
from agentforge.vault import CredentialVault

class LinkedInPlatform(BasePlatform):
    name = "linkedin"
    description = "Read LinkedIn profiles/pages via Jina Reader, and post updates using LinkedIn API."
    supports_read = True
    supports_write = True
    supports_search = False
    requires_auth = True
    auth_type = "oauth"

    def read(self, url: str, **kwargs) -> Dict[str, Any]:
        """Reads a LinkedIn profile/page using Jina Reader to bypass auth gates."""
        jina_url = f"https://r.jina.ai/{url}"
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(jina_url)
                if response.status_code == 200:
                    return {
                        "platform": self.name,
                        "action": "read",
                        "success": True,
                        "url": url,
                        "content": response.text.strip()
                    }
                else:
                    return {
                        "platform": self.name,
                        "action": "read",
                        "success": False,
                        "error": f"Failed to fetch LinkedIn content. Status: {response.status_code}"
                    }
        except Exception as e:
            return {
                "platform": self.name,
                "action": "read",
                "success": False,
                "error": str(e)
            }

    def write(self, content: str, **kwargs) -> Dict[str, Any]:
        """Posts an update to LinkedIn profile."""
        vault = CredentialVault()
        access_token = vault.get("linkedin", "access_token")
        person_id = vault.get("linkedin", "person_id") # URN format: 'urn:li:person:XXXX'

        if not access_token or not person_id:
            return {
                "platform": self.name,
                "action": "post",
                "success": False,
                "error": "LinkedIn API credentials are missing. Configure 'access_token' and 'person_id' in Vault."
            }

        url = "https://api.linkedin.com/v2/shares"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        payload = {
            "owner": person_id,
            "subject": kwargs.get("subject", "AgentForge Update"),
            "text": {
                "text": content
            },
            "distribution": {
                "linkedInDistributionTarget": {
                    "visibleToGuests": True
                }
            }
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload, headers=headers)
                if response.status_code in (200, 201):
                    res_data = response.json()
                    return {
                        "platform": self.name,
                        "action": "post",
                        "success": True,
                        "share_id": res_data.get("id"),
                        "url": f"https://www.linkedin.com/share?id={res_data.get('id')}"
                    }
                else:
                    return {
                        "platform": self.name,
                        "action": "post",
                        "success": False,
                        "error": f"API Error: {response.text}"
                    }
        except Exception as e:
            return {
                "platform": self.name,
                "action": "post",
                "success": False,
                "error": str(e)
            }

    def doctor(self) -> Dict[str, Any]:
        vault = CredentialVault()
        token = vault.get("linkedin", "access_token")
        person = vault.get("linkedin", "person_id")
        
        if token and person:
            return {
                "platform": self.name,
                "status": "Ready",
                "tool": "LinkedIn API",
                "auth": "Authenticated",
                "notes": f"Ready to post for URN {person}."
            }
        else:
            return {
                "platform": self.name,
                "status": "Ready",
                "tool": "Jina Reader",
                "auth": "READ-ONLY",
                "notes": "READ is active. Configure 'access_token' and 'person_id' in Vault to unlock WRITE."
            }
