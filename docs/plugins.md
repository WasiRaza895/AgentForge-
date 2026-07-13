# Plugin Development Guide

AgentForge is built to be extensible. You can write custom platform integrations, place them in the plugin folder, and they will load dynamically.

---

## 1. Creating a New Plugin
Run the plugin wizard to generate template boilerplate:
```bash
agentforge plugin create custom_platform --cls CustomPlatform
```
This generates a folder under `~/.agentforge/plugins/custom_platform/` containing:
- `plugin.json`: Metadata manifest
- `platform.py`: Python code boilerplate

---

## 2. Plugin Structure

### plugin.json
Describes metadata and maps target execution class:
```json
{
  "name": "My Custom Platform",
  "version": "0.1.0",
  "description": "Integration with my private platform.",
  "platform_class": "MyCustomPlatform",
  "author": "Developer"
}
```

### platform.py
Implements platform actions. It must inherit from `BasePlatform` and define required methods:
```python
from agentforge.platforms.base import BasePlatform
from typing import Dict, Any, List

class MyCustomPlatform(BasePlatform):
    name = "custom"
    description = "Custom API integration."
    supports_read = True
    supports_write = True
    
    def read(self, target: str, **kwargs) -> Dict[str, Any]:
        return {
            "platform": self.name,
            "action": "read",
            "success": True,
            "data": f"Reading details for {target}"
        }
        
    def write(self, content: str, **kwargs) -> Dict[str, Any]:
        return {
            "platform": self.name,
            "action": "write",
            "success": True,
            "data": f"Wrote content: {content}"
        }
```

---

## 3. Discovered and Loaded Plugins
List all successfully loaded plugins:
```bash
agentforge plugin list
```
AgentForge automatically scans `~/.agentforge/plugins/` on startup.
