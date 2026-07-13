import httpx
from typing import Dict, Any, List, Optional
from agentforge.platforms.base import BasePlatform
from agentforge.utils import check_tool_installed, run_command
from agentforge.vault import CredentialVault

class RedditPlatform(BasePlatform):
    name = "reddit"
    description = "Read posts/comments on Reddit, search subreddits, and post or reply."
    supports_read = True
    supports_write = True
    supports_search = True
    requires_auth = True
    auth_type = "oauth"

    def _get_praw_reddit(self) -> Optional[Any]:
        """Tries to build a PRAW Reddit client using vault credentials."""
        vault = CredentialVault()
        client_id = vault.get("reddit", "client_id")
        client_secret = vault.get("reddit", "client_secret")
        username = vault.get("reddit", "username")
        password = vault.get("reddit", "password")
        user_agent = vault.get("reddit", "user_agent") or "AgentForge/0.1.0"

        if client_id and client_secret and username and password:
            try:
                import praw
                return praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    username=username,
                    password=password,
                    user_agent=user_agent
                )
            except ImportError:
                return None
        return None

    def read(self, target: str, **kwargs) -> Dict[str, Any]:
        """Reads a post and its comments. Target is URL or post ID."""
        post_id = target.split("/")[-1] if "/" in target else target
        if "comments" in target:
            # Extract id from middle of URL if URL format has comments/id/title
            parts = target.split("/comments/")
            if len(parts) > 1:
                post_id = parts[1].split("/")[0]

        # Fetch using Reddit JSON API directly (No API keys needed!)
        url = f"https://www.reddit.com/comments/{post_id}.json"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        try:
            with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
                response = client.get(url)
                if response.status_code != 200:
                    return {
                        "platform": self.name,
                        "action": "read",
                        "success": False,
                        "error": f"Failed to fetch post. HTTP Status: {response.status_code}"
                    }
                
                json_data = response.json()
                # Parse Post Detail
                post_data = json_data[0]["data"]["children"][0]["data"]
                post_info = {
                    "id": post_data.get("id"),
                    "title": post_data.get("title"),
                    "selftext": post_data.get("selftext"),
                    "author": post_data.get("author"),
                    "subreddit": post_data.get("subreddit"),
                    "ups": post_data.get("ups"),
                    "url": post_data.get("url")
                }
                
                # Parse Comments (Top 10)
                comments_list = []
                comments_data = json_data[1]["data"]["children"]
                for comment in comments_data[:10]:
                    c_data = comment.get("data", {})
                    if not c_data.get("body"):
                        continue
                    comments_list.append({
                        "id": c_data.get("id"),
                        "author": c_data.get("author"),
                        "body": c_data.get("body"),
                        "ups": c_data.get("ups")
                    })
                
                post_info["comments"] = comments_list
                return {
                    "platform": self.name,
                    "action": "read",
                    "success": True,
                    "data": post_info
                }
        except Exception as e:
            return {
                "platform": self.name,
                "action": "read",
                "success": False,
                "error": str(e)
            }

    def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Searches Reddit posts."""
        subreddit = kwargs.get("subreddit")
        limit = kwargs.get("limit", 5)
        
        # Build search endpoint
        if subreddit:
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
        else:
            url = "https://www.reddit.com/search.json"
            
        params = {"q": query, "limit": limit, "sort": "relevance"}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        try:
            with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
                response = client.get(url, params=params)
                if response.status_code != 200:
                    return [{"error": f"Search failed. HTTP Status: {response.status_code}"}]
                
                results = []
                children = response.json().get("data", {}).get("children", [])
                for child in children:
                    data = child.get("data", {})
                    results.append({
                        "id": data.get("id"),
                        "title": data.get("title"),
                        "author": data.get("author"),
                        "subreddit": data.get("subreddit"),
                        "url": f"https://www.reddit.com{data.get('permalink')}",
                        "ups": data.get("ups")
                    })
                return results
        except Exception as e:
            return [{"error": str(e)}]

    def write(self, content: str, **kwargs) -> Dict[str, Any]:
        """Submits a post or replies to a comment/post."""
        reddit_client = self._get_praw_reddit()
        action = kwargs.get("action", "post")
        
        if not reddit_client:
            return {
                "platform": self.name,
                "action": "write",
                "success": False,
                "error": "Reddit API credentials are missing. Configure 'client_id', 'client_secret', 'username', 'password' in the Vault."
            }

        try:
            if action == "post":
                subreddit_name = kwargs.get("subreddit")
                title = kwargs.get("title")
                if not subreddit_name or not title:
                    return {
                        "platform": self.name,
                        "action": "write",
                        "success": False,
                        "error": "Posting requires both 'subreddit' and 'title' arguments."
                    }
                
                subreddit = reddit_client.subreddit(subreddit_name)
                submission = subreddit.submit(title, selftext=content)
                return {
                    "platform": self.name,
                    "action": "post",
                    "success": True,
                    "id": submission.id,
                    "url": submission.url
                }
            elif action == "reply":
                reply_to = kwargs.get("reply_to")
                if not reply_to:
                    return {
                        "platform": self.name,
                        "action": "write",
                        "success": False,
                        "error": "Reply requires 'reply_to' target ID (submission or comment ID)."
                    }
                
                # Check if it's a submission or comment
                if reply_to.startswith("t3_") or len(reply_to) == 6:
                    # Submission ID
                    target = reddit_client.submission(id=reply_to.replace("t3_", ""))
                else:
                    # Comment ID
                    target = reddit_client.comment(id=reply_to.replace("t1_", ""))
                
                comment = target.reply(content)
                return {
                    "platform": self.name,
                    "action": "reply",
                    "success": True,
                    "id": comment.id,
                    "url": f"https://www.reddit.com{comment.permalink}"
                }
            else:
                return {
                    "platform": self.name,
                    "action": "write",
                    "success": False,
                    "error": f"Unsupported action: {action}"
                }
        except Exception as e:
            return {
                "platform": self.name,
                "action": "write",
                "success": False,
                "error": str(e)
            }

    def doctor(self) -> Dict[str, Any]:
        reddit_client = self._get_praw_reddit()
        if reddit_client:
            try:
                # Test connection
                reddit_client.user.me()
                return {
                    "platform": self.name,
                    "status": "Ready",
                    "tool": "praw",
                    "auth": "Authenticated",
                    "notes": "Full read/write permissions active."
                }
            except Exception as e:
                return {
                    "platform": self.name,
                    "status": "Broken",
                    "tool": "praw",
                    "auth": "Authentication failed",
                    "notes": f"Credentials error: {e}"
                }
        else:
            return {
                "platform": self.name,
                "status": "Ready",
                "tool": "JSON API",
                "auth": "READ-ONLY",
                "notes": "READ is ready. Setup WRITE by configuring Reddit client_id/secret in Vault."
            }
