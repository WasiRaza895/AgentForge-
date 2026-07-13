from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

class BasePlatform(ABC):
    """Abstract Base Class representing an AgentForge integration platform."""
    
    name: str = ""
    description: str = ""
    supports_read: bool = True
    supports_write: bool = False
    supports_search: bool = False
    requires_auth: bool = False
    auth_type: str = "none"  # none, cookie, token, oauth, webhook
    
    @abstractmethod
    def read(self, target: str, **kwargs) -> Dict[str, Any]:
        """Reads data from the platform. e.g. a post, profile, or thread."""
        pass
    
    def write(self, content: str, **kwargs) -> Dict[str, Any]:
        """Writes data/posts content to the platform. Raises error if unsupported."""
        raise NotImplementedError(f"{self.name} does not support write operations.")
    
    def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Searches the platform. Raises error if unsupported."""
        raise NotImplementedError(f"{self.name} does not support searching.")
    
    def doctor(self) -> Dict[str, Any]:
        """Diagnoses health, tool availability, and authentication status.
        
        Returns a dict containing:
            platform: str
            status: str ('Ready', 'Partial', 'Not Configured', 'Broken')
            tool: str (name of tool)
            auth: str (status of authentication)
            notes: str (recommendation or error details)
        """
        return {
            "platform": self.name,
            "status": "Ready" if not self.requires_auth else "Not Configured",
            "tool": "builtin",
            "auth": "none",
            "notes": ""
        }
    
    def get_required_tools(self) -> List[str]:
        """Returns a list of external CLI tools required by this platform."""
        return []
