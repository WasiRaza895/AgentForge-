import httpx
import re
from typing import Dict, Any, List, Optional
from agentforge.platforms.base import BasePlatform
from agentforge.utils import run_command, check_tool_installed, sanitize_text
from agentforge.vault import CredentialVault

class TwitterPlatform(BasePlatform):
    name = "twitter"
    description = "Read tweets/threads, search Twitter/X, and post or reply."
    supports_read = True
    supports_write = True
    supports_search = True
    requires_auth = True
    auth_type = "oauth"

    NITTER_INSTANCES = [
        "https://nitter.privacydev.net",
        "https://nitter.poast.org",
        "https://nitter.net",
        "https://nitter.cz"
    ]

    def _get_tweepy_client(self) -> Optional[Any]:
        """Tries to build a tweepy client using vault credentials."""
        vault = CredentialVault()
        api_key = vault.get("twitter", "api_key")
        api_secret = vault.get("twitter", "api_secret")
        access_token = vault.get("twitter", "access_token")
        access_token_secret = vault.get("twitter", "access_token_secret")
        bearer_token = vault.get("twitter", "bearer_token")

        if api_key and api_secret and access_token and access_token_secret:
            try:
                import tweepy
                return tweepy.Client(
                    bearer_token=bearer_token,
                    consumer_key=api_key,
                    consumer_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_token_secret
                )
            except ImportError:
                return None
        return None

    def read(self, target: str, **kwargs) -> Dict[str, Any]:
        """Reads a single tweet or thread. Target is tweet URL or ID."""
        tweet_id = target.split("/")[-1].split("?")[0] if "/" in target else target
        
        # Method 1: Try using xreach CLI if installed
        if check_tool_installed("xreach"):
            success, output = run_command(f"xreach read {tweet_id} --json")
            if success:
                try:
                    import json
                    return {
                        "platform": self.name,
                        "action": "read",
                        "success": True,
                        "data": json.loads(output)
                    }
                except Exception:
                    pass

        # Method 2: Try Nitter instances scraping (Free, Zero API keys)
        for instance in self.NITTER_INSTANCES:
            try:
                url = f"{instance}/i/status/{tweet_id}"
                with httpx.Client(timeout=8.0, follow_redirects=True) as client:
                    response = client.get(url)
                    if response.status_code == 200:
                        # Extract basic text content using regex
                        tweet_text_match = re.findall(r'<div class="tweet-content media-body">([^<]+)</div>', response.text)
                        author_match = re.search(r'<a class="username" [^>]+>@([^<]+)</a>', response.text)
                        
                        content = tweet_text_match[0].strip() if tweet_text_match else "Could not parse text."
                        author = author_match.group(1).strip() if author_match else "unknown"
                        
                        return {
                            "platform": self.name,
                            "action": "read",
                            "success": True,
                            "data": {
                                "id": tweet_id,
                                "author": author,
                                "text": sanitize_text(content),
                                "url": f"https://twitter.com/{author}/status/{tweet_id}"
                            }
                        }
            except Exception:
                continue

        return {
            "platform": self.name,
            "action": "read",
            "success": False,
            "error": "Failed to read tweet. All methods failed or Nitter instances rate-limited."
        }

    def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Searches Twitter/X using Nitter instances or xreach CLI."""
        limit = kwargs.get("limit", 5)
        
        if check_tool_installed("xreach"):
            success, output = run_command(f'xreach search "{query}" -n {limit} --json')
            if success:
                try:
                    import json
                    return json.loads(output)
                except Exception:
                    pass

        # Nitter search scraping
        for instance in self.NITTER_INSTANCES:
            try:
                url = f"{instance}/search"
                params = {"q": query}
                with httpx.Client(timeout=8.0, follow_redirects=True) as client:
                    response = client.get(url, params=params)
                    if response.status_code == 200:
                        # Parse out multiple tweets
                        tweets = []
                        tweet_blocks = re.findall(
                            r'<div class="tweet-body">.*?<a class="username" [^>]+>@([^<]+)</a>.*?<div class="tweet-content media-body">([^<]+)</div>',
                            response.text,
                            re.DOTALL
                        )
                        for author, content in tweet_blocks[:limit]:
                            tweets.append({
                                "author": author.strip(),
                                "text": sanitize_text(content),
                                "source": instance
                            })
                        if tweets:
                            return tweets
            except Exception:
                continue
                
        return [{"error": "Search failed. Twitter CLI and scrapers are currently unavailable."}]

    def write(self, content: str, **kwargs) -> Dict[str, Any]:
        """Posts a new tweet or replies to an existing tweet."""
        reply_to = kwargs.get("reply_to")
        
        # Try Tweepy API V2
        client = self._get_tweepy_client()
        if client:
            try:
                response = client.create_tweet(text=content, in_reply_to_tweet_id=reply_to)
                tweet_id = response.data.get("id") if response.data else "unknown"
                return {
                    "platform": self.name,
                    "action": "post",
                    "success": True,
                    "tweet_id": tweet_id,
                    "url": f"https://twitter.com/i/status/{tweet_id}"
                }
            except Exception as e:
                return {
                    "platform": self.name,
                    "action": "post",
                    "success": False,
                    "error": f"Tweepy error: {str(e)}"
                }

        # CLI fallback
        if check_tool_installed("xreach"):
            cmd = f'xreach post "{content}"'
            if reply_to:
                cmd += f' --reply-to {reply_to}'
            success, output = run_command(cmd)
            return {
                "platform": self.name,
                "action": "post",
                "success": success,
                "output": output
            }

        return {
            "platform": self.name,
            "action": "post",
            "success": False,
            "error": "Tweepy credentials or 'xreach' CLI is missing. Configure keys in Vault: 'api_key', 'api_secret', 'access_token', 'access_token_secret'"
        }

    def doctor(self) -> Dict[str, Any]:
        client = self._get_tweepy_client()
        has_cli = check_tool_installed("xreach")
        
        if client:
            return {
                "platform": self.name,
                "status": "Ready",
                "tool": "tweepy (API v2)",
                "auth": "Authenticated",
                "notes": "Full read/write permissions via OAuth credentials."
            }
        elif has_cli:
            return {
                "platform": self.name,
                "status": "Ready",
                "tool": "xreach CLI",
                "auth": "CLI authenticated",
                "notes": "Capable of Twitter operations."
            }
        else:
            return {
                "platform": self.name,
                "status": "Not Configured",
                "tool": "tweepy / xreach",
                "auth": "Missing",
                "notes": "READ active (via Nitter). Setup WRITE using: 'agentforge vault set twitter api_key ...'"
            }
