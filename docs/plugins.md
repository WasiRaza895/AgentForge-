# Plugin Development Guide

AgentForge loads trusted Python adapters from the local plugin folder when a workflow first references them. Use a lowercase folder name with letters, digits, underscores, or hyphens. Install plugins from sources you trust because an adapter runs Python code on your machine.

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
List the plugin manifests available on this machine.
```bash
agentforge plugin list
```
To use the scaffold from step 1, save the following as `custom.yaml` and run `agentforge pipeline run custom.yaml`. The `platform` name is the plugin's folder name.

```yaml
name: Custom adapter example
steps:
  - platform: custom_platform
    action: read
    params:
      target: demo
```
