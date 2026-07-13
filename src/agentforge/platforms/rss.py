import feedparser
from typing import Dict, Any, List
from agentforge.platforms.base import BasePlatform

class RSSPlatform(BasePlatform):
    name = "rss"
    description = "Read any RSS/Atom feed entries."
    supports_read = True
    supports_write = False
    supports_search = False

    def read(self, feed_url: str, **kwargs) -> Dict[str, Any]:
        """Parses the RSS feed and returns recent entries."""
        limit = kwargs.get("limit", 10)
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                # Bozo flag is set for malformed feeds, but some are still readable
                if not feed.entries:
                    return {
                        "platform": self.name,
                        "action": "read",
                        "success": False,
                        "error": "Failed to parse feed. Invalid format."
                    }

            feed_meta = {
                "title": feed.feed.get("title", "Unknown Feed"),
                "description": feed.feed.get("description", "No description"),
                "link": feed.feed.get("link", feed_url),
            }

            entries = []
            for entry in feed.entries[:limit]:
                entries.append({
                    "title": entry.get("title", "No Title"),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", entry.get("description", "")),
                    "published": entry.get("published", entry.get("updated", "Unknown Date")),
                    "author": entry.get("author", "Unknown Author")
                })

            return {
                "platform": self.name,
                "action": "read",
                "success": True,
                "metadata": feed_meta,
                "entries": entries
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
            # Test feedparser version check or load
            version = getattr(feedparser, "__version__", "installed")
            return {
                "platform": self.name,
                "status": "Ready",
                "tool": f"feedparser ({version})",
                "auth": "none",
                "notes": "RSS parser is active."
            }
        except Exception as e:
            return {
                "platform": self.name,
                "status": "Broken",
                "tool": "feedparser",
                "auth": "none",
                "notes": f"Library load failed: {e}"
            }
