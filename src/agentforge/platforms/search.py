import httpx
import re
from typing import Dict, Any, List
from agentforge.platforms.base import BasePlatform
from agentforge.utils import sanitize_text
from agentforge.vault import CredentialVault

class SearchPlatform(BasePlatform):
    name = "search"
    description = "Perform a web search. Integrates with Exa API if key is present, otherwise falls back to free DuckDuckGo scraping."
    supports_read = False
    supports_write = False
    supports_search = True

    def read(self, target: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("Search platform does not support read operations directly. Use search.")

    def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Searches the web using Exa API or falls back to DuckDuckGo HTML parsing."""
        limit = kwargs.get("limit", 5)
        
        exa_key = None
        if kwargs.get("use_exa", True):
            vault = CredentialVault()
            exa_key = vault.get("search", "exa_key") or vault.get("exa", "api_key")
        
        if exa_key:
            try:
                headers = {
                    "accept": "application/json",
                    "content-type": "application/json",
                    "x-api-key": exa_key
                }
                payload = {
                    "query": query,
                    "numResults": limit,
                    "useAutoprompt": True
                }
                with httpx.Client(timeout=10.0) as client:
                    response = client.post("https://api.exa.ai/search", json=payload, headers=headers)
                    if response.status_code == 200:
                        results = []
                        for item in response.json().get("results", []):
                            results.append({
                                "title": item.get("title", "No Title"),
                                "url": item.get("url", ""),
                                "snippet": item.get("author", "") or "No snippet",
                                "score": item.get("score", 0.0)
                            })
                        return results
            except Exception:
                pass # Fallback to DuckDuckGo

        # Free DuckDuckGo search scraping
        url = "https://html.duckduckgo.com/html/"
        params = {"q": query}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
                response = client.post(url, data=params)
                if response.status_code != 200:
                    return [{"error": f"Search failed. HTTP Status: {response.status_code}"}]
                
                results = []
                blocks = response.text.split('class="result results_links')[1:]
                for block in blocks[:limit]:
                    # Extract link and title
                    link_title_match = re.search(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.DOTALL)
                    if not link_title_match:
                        continue

                    href = link_title_match.group(1)
                    title = link_title_match.group(2)

                    # Clean title HTML tags (e.g. <b>)
                    title = re.sub(r'<[^>]*>', '', title).strip()

                    # Clean up URL redirects (DDG wraps them sometimes: //duckduckgo.com/l/?uddg=URL)
                    clean_url = href
                    if "uddg=" in href:
                        try:
                            uddg_part = href.split("uddg=")[1].split("&")[0]
                            from urllib.parse import unquote
                            clean_url = unquote(uddg_part)
                        except Exception:
                            pass

                    # Extract snippet
                    snippet_match = re.search(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>|<div class="result__snippet"[^>]*>(.*?)</div>', block, re.DOTALL)
                    snippet = "No snippet available."
                    if snippet_match:
                        raw_snippet = snippet_match.group(1) or snippet_match.group(2) or ""
                        snippet = re.sub(r'<[^>]*>', '', raw_snippet).strip()
                        
                    results.append({
                        "title": sanitize_text(title),
                        "url": clean_url,
                        "snippet": sanitize_text(snippet)
                    })
                        
                return results if results else [{"error": "No search results found."}]
        except Exception as e:
            return [{"error": str(e)}]

    def doctor(self) -> Dict[str, Any]:
        vault = CredentialVault()
        exa_key = vault.get("search", "exa_key") or vault.get("exa", "api_key")
        if exa_key:
            return {
                "platform": self.name,
                "status": "Ready",
                "tool": "Exa API",
                "auth": "Authenticated",
                "notes": "Semantic web search is active."
            }
        else:
            return {
                "platform": self.name,
                "status": "Ready",
                "tool": "DuckDuckGo scraper",
                "auth": "none",
                "notes": "Free web search is active (no API keys required)."
            }
