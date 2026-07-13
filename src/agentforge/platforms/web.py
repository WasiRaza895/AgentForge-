import httpx
from typing import Dict, Any, List
from agentforge.platforms.base import BasePlatform
from agentforge.utils import sanitize_text

class WebPlatform(BasePlatform):
    name = "web"
    description = "Read any webpage, stripping HTML to clean markdown/text."
    supports_read = True
    supports_write = False
    supports_search = False

    def read(self, url: str, **kwargs) -> Dict[str, Any]:
        """Fetches URL content and sanitizes it. Falls back to Jina Reader if available."""
        use_jina = kwargs.get("use_jina", True)
        
        # Try Jina Reader first if requested (produces cleaner Markdown for LLMs)
        if use_jina:
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
                            "title": url,
                            "content": response.text.strip()
                        }
            except Exception:
                pass  # Fallback to direct read
                
        # Direct fallback read
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
                response = client.get(url)
                if response.status_code != 200:
                    return {
                        "platform": self.name,
                        "action": "read",
                        "success": False,
                        "error": f"Failed to fetch. HTTP Status: {response.status_code}"
                    }
                
                clean_content = sanitize_text(response.text)
                return {
                    "platform": self.name,
                    "action": "read",
                    "success": True,
                    "url": url,
                    "content": clean_content
                }
        except Exception as e:
            return {
                "platform": self.name,
                "action": "read",
                "success": False,
                "error": str(e)
            }

    def doctor(self) -> Dict[str, Any]:
        try:
            # Check basic connection
            with httpx.Client(timeout=3.0) as client:
                client.get("https://httpbin.org/status/200")
            return {
                "platform": self.name,
                "status": "Ready",
                "tool": "httpx",
                "auth": "none",
                "notes": "Web connectivity is active."
            }
        except Exception as e:
            return {
                "platform": self.name,
                "status": "Broken",
                "tool": "httpx",
                "auth": "none",
                "notes": f"Internet connection error: {e}"
            }
