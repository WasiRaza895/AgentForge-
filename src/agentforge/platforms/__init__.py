from typing import Dict, Type, List
from agentforge.platforms.base import BasePlatform

def get_platform_class(name: str) -> Type[BasePlatform]:
    """Dynamically imports and returns a platform class by name to avoid circular dependencies."""
    name = name.lower()
    
    if name == "web":
        from agentforge.platforms.web import WebPlatform
        return WebPlatform
    elif name == "youtube":
        from agentforge.platforms.youtube import YouTubePlatform
        return YouTubePlatform
    elif name == "rss":
        from agentforge.platforms.rss import RSSPlatform
        return RSSPlatform
    elif name == "github":
        from agentforge.platforms.github_platform import GitHubPlatform
        return GitHubPlatform
    elif name == "twitter":
        from agentforge.platforms.twitter import TwitterPlatform
        return TwitterPlatform
    elif name == "reddit":
        from agentforge.platforms.reddit import RedditPlatform
        return RedditPlatform
    elif name == "search":
        from agentforge.platforms.search import SearchPlatform
        return SearchPlatform
    elif name == "linkedin":
        from agentforge.platforms.linkedin import LinkedInPlatform
        return LinkedInPlatform
    elif name == "slack":
        from agentforge.platforms.slack import SlackPlatform
        return SlackPlatform
    elif name == "discord":
        from agentforge.platforms.discord import DiscordPlatform
        return DiscordPlatform
    elif name == "email":
        from agentforge.platforms.email_platform import EmailPlatform
        return EmailPlatform
    elif name == "telegram":
        from agentforge.platforms.telegram import TelegramPlatform
        return TelegramPlatform
    else:
        raise ValueError(f"Unknown platform: {name}")

def get_platform(name: str) -> BasePlatform:
    """Instantiates and returns a platform instance by name."""
    cls = get_platform_class(name)
    return cls()

def list_platforms() -> List[str]:
    """Returns a list of all registered platform names."""
    return [
        "web", "youtube", "rss", "github", "twitter", "reddit",
        "search", "linkedin", "slack", "discord", "email", "telegram"
    ]
