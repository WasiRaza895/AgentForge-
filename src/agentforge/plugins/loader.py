import sys
import os
import json
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional
from agentforge.utils import ensure_config_dir

class PluginLoader:
    """Scans, installs, and dynamically loads custom integration plugins for AgentForge."""
    
    def __init__(self):
        self.config_dir = ensure_config_dir()
        self.plugins_dir = self.config_dir / "plugins"
        self.plugins_dir.mkdir(exist_ok=True)
        self.loaded_plugins: Dict[str, Any] = {}

    def discover_plugins(self) -> List[Dict[str, Any]]:
        """Scans the plugins directory and lists metadata for all valid plugins."""
        discovered = []
        for item in self.plugins_dir.iterdir():
            if item.is_dir():
                manifest_path = item / "plugin.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            meta["path"] = str(item)
                            discovered.append(meta)
                    except Exception:
                        continue
        return discovered

    def load_plugin_platform(self, plugin_name: str) -> Optional[Any]:
        """Dynamically imports a plugin module and returns its platform class."""
        manifest_path = self.plugins_dir / plugin_name / "plugin.json"
        entry_file = self.plugins_dir / plugin_name / "platform.py"
        
        if not manifest_path.exists() or not entry_file.exists():
            return None

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            
            module_name = f"agentforge_plugin_{plugin_name}"
            spec = importlib.util.spec_from_file_location(module_name, str(entry_file))
            if not spec or not spec.loader:
                return None
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Find the platform class (inherits from BasePlatform)
            class_name = meta.get("platform_class")
            platform_class = getattr(module, class_name, None)
            
            if platform_class:
                self.loaded_plugins[plugin_name] = meta
                return platform_class
        except Exception:
            pass
        return None

    def install_local_plugin(self, src_path: str) -> bool:
        """Installs a plugin from a local directory by copying it to the plugins folder."""
        import shutil
        src = Path(src_path)
        if not src.exists() or not (src / "plugin.json").exists():
            return False
            
        dest = self.plugins_dir / src.name
        if dest.exists():
            shutil.rmtree(dest)
            
        shutil.copytree(src, dest)
        return True

    def create_plugin_template(self, name: str, class_name: str) -> str:
        """Generates a boilerplate folder structure for developing new AgentForge plugins."""
        plugin_dir = self.plugins_dir / name.lower().replace(" ", "_")
        plugin_dir.mkdir(exist_ok=True)
        
        # Write plugin.json manifest
        manifest = {
            "name": name,
            "version": "0.1.0",
            "description": f"Custom {name} integration for AgentForge.",
            "platform_class": class_name,
            "author": "Developer"
        }
        with open(plugin_dir / "plugin.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            
        # Write platform.py template
        boilerplate = f"""from agentforge.platforms.base import BasePlatform
from typing import Dict, Any, List

class {class_name}(BasePlatform):
    name = "{name.lower()}"
    description = "Custom plugin platform {name}."
    supports_read = True
    supports_write = False
    
    def read(self, target: str, **kwargs) -> Dict[str, Any]:
        return {{
            "platform": self.name,
            "action": "read",
            "success": True,
            "target": target,
            "data": "Hello from custom plugin!"
        }}
"""
        with open(plugin_dir / "platform.py", "w", encoding="utf-8") as f:
            f.write(boilerplate)
            
        return str(plugin_dir)
