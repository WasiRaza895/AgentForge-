import yaml
import re
from typing import Dict, Any, List, Optional
from agentforge.platforms import get_platform

class Pipeline:
    """YAML-based workflow engine to validate and run sequential, multi-platform agent actions."""
    
    def __init__(self, config_path: Optional[str] = None, config_dict: Optional[dict] = None):
        self.config = {}
        if config_path:
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        elif config_dict:
            self.config = config_dict

    def validate(self) -> List[str]:
        """Validates the pipeline configuration. Returns a list of validation error strings."""
        errors = []
        if not self.config:
            return ["Pipeline configuration is empty."]

        if "name" not in self.config:
            errors.append("Pipeline requires a 'name'.")
            
        steps = self.config.get("steps")
        if not steps or not isinstance(steps, list):
            return ["Pipeline requires a 'steps' list."]

        for idx, step in enumerate(steps):
            step_name = step.get("name", f"Step {idx}")
            platform = step.get("platform")
            action = step.get("action")
            
            if not platform:
                errors.append(f"[{step_name}] Missing 'platform' parameter.")
            if not action:
                errors.append(f"[{step_name}] Missing 'action' parameter.")

        return errors

    def _resolve_variables(self, val: Any, context: Dict[str, Any]) -> Any:
        """Recursively interpolates variables like {step_var.field} in parameters."""
        if isinstance(val, str):
            # Regex to find placeholders like {tweets.data.title}
            placeholders = re.findall(r"\{([^}]+)\}", val)
            if not placeholders:
                return val
                
            resolved_val = val
            for placeholder in placeholders:
                path = placeholder.split(".")
                root = path[0]
                
                # Fetch root var from context
                if root not in context:
                    continue
                    
                obj = context[root]
                
                # Walk path
                try:
                    for key in path[1:]:
                        if isinstance(obj, dict):
                            obj = obj.get(key)
                        elif isinstance(obj, list):
                            obj = obj[int(key)]
                        else:
                            obj = getattr(obj, key)
                    
                    # Replace in string. If the value itself is an object and there's no other text, return it directly.
                    if len(placeholders) == 1 and val == f"{{{placeholder}}}":
                        return obj
                    resolved_val = resolved_val.replace(f"{{{placeholder}}}", str(obj))
                except Exception:
                    # If path resolution fails, leave as placeholder
                    continue
            return resolved_val
            
        elif isinstance(val, dict):
            return {k: self._resolve_variables(v, context) for k, v in val.items()}
        elif isinstance(val, list):
            return [self._resolve_variables(item, context) for item in val]
        return val

    def run(self) -> Dict[str, Any]:
        """Executes all pipeline steps sequentially, returning execution log & status."""
        errors = self.validate()
        if errors:
            return {"success": False, "error": "Validation failed: " + "; ".join(errors)}

        context = {}
        log = []
        success = True
        
        steps = self.config.get("steps", [])
        for idx, step in enumerate(steps):
            step_name = step.get("name", f"Step {idx} ({step.get('platform')}.{step.get('action')})")
            platform_name = step.get("platform")
            action = step.get("action")
            params = step.get("params", {})
            output_var = step.get("output_var")
            
            # Resolve placeholders in parameters using the run context
            resolved_params = self._resolve_variables(params, context)
            
            step_log = {
                "step": step_name,
                "platform": platform_name,
                "action": action,
                "success": False
            }
            
            try:
                platform = get_platform(platform_name)
                # Map action to method call
                if action == "read":
                    target = resolved_params.get("target")
                    if not target:
                        raise ValueError("Missing 'target' in read params.")
                    res = platform.read(target, **resolved_params)
                elif action == "search":
                    query = resolved_params.get("query")
                    if not query:
                        raise ValueError("Missing 'query' in search params.")
                    res = platform.search(query, **resolved_params)
                else:
                    # Write actions or custom actions
                    content = resolved_params.get("content", "")
                    res = platform.write(content, **resolved_params)
                
                step_success = res.get("success", True) if isinstance(res, dict) else True
                step_log["success"] = step_success
                step_log["result"] = res
                
                # Save result to context for downstream steps
                if output_var:
                    context[output_var] = res
                    
                if not step_success:
                    success = False
                    if step.get("abort_on_failure", True):
                        step_log["status"] = "Aborted pipeline on step failure."
                        log.append(step_log)
                        break
            except Exception as e:
                success = False
                step_log["error"] = str(e)
                log.append(step_log)
                if step.get("abort_on_failure", True):
                    break
                continue
                
            log.append(step_log)
            
        return {
            "name": self.config.get("name"),
            "success": success,
            "log": log,
            "context_keys": list(context.keys())
        }
