"""Loopback browser interface for AgentForge workflows and integration actions."""

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape

from agentforge.pipeline import Pipeline
from agentforge.studio_connections import (
    MissingConnection, connection_status, run_reviewed_action, save_connection,
)
from agentforge.utils import truncate


ASSETS = Path(__file__).with_name("studio_assets")
PAGES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/studio.css": ("studio.css", "text/css; charset=utf-8"),
    "/studio.js": ("studio.js", "text/javascript; charset=utf-8"),
    "/connections.js": ("connections.js", "text/javascript; charset=utf-8"),
    "/forge.js": ("forge.js", "text/javascript; charset=utf-8"),
}


def run_demo(demo: str) -> dict:
    if demo not in {"briefing", "scan"}:
        raise KeyError(demo)

    related = (ASSETS / "related.xml").as_posix()
    feed = (ASSETS / "feed.xml").read_text(encoding="utf-8").replace(
        "src/agentforge/studio_assets/related.xml",
        escape(related),
    )
    steps = [
        {
            "name": "Read the release feed",
            "platform": "rss",
            "action": "read",
            "params": {"target": feed, "limit": 3},
            "output_var": "feed",
        },
    ]
    if demo == "briefing":
        steps.append({
            "name": "Follow the related feed",
            "platform": "rss",
            "action": "read",
            "params": {"target": "{feed.metadata.link}", "limit": 2},
            "output_var": "related",
        })
    name = "Release briefing" if demo == "briefing" else "Release feed scan"
    result = Pipeline(config_dict={"name": name, "steps": steps}).run()
    for step in result.get("log", []):
        metadata = step.get("result", {}).get("metadata", {})
        if metadata.get("link") == related:
            metadata["link"] = "src/agentforge/studio_assets/related.xml"
    return result


def run_task(request: str) -> dict:
    """Match a plain-English request to a supported action or demo."""
    request = re.sub(r"^(?:(?:can|could|would) you\s+)?(?:please\s+)?", "", request.strip(), flags=re.IGNORECASE)
    command = request.rstrip(".!?").lower()
    if command in {"run the release briefing", "run the sample workflow", "release briefing"}:
        return run_demo("briefing")
    if command in {"read the release feed", "scan the release feed", "release feed scan"}:
        return run_demo("scan")

    search = re.fullmatch(r"(?:search(?: the web)? for|find|look up)\s+(.+)", request, re.IGNORECASE)
    if search:
        name = "Web search"
        step = {"name": name, "platform": "search", "action": "search", "params": {
            "query": search.group(1), "limit": 5, "use_exa": connection_status()["exa"],
        }}
    else:
        target = re.sub(r"^(?:read|open)(?: the page at)?\s+", "", request, flags=re.IGNORECASE)
        if re.fullmatch(r"(?:[a-z0-9-]+\.)+[a-z]{2,}(?::\d+)?(?:[/?#]\S*)?", target, re.IGNORECASE):
            target = f"https://{target}"
        try:
            url = urlsplit(target)
            is_web_url = (
                url.scheme in {"https", "http"} and url.hostname
                and not url.username and not url.password and not any(char.isspace() for char in target)
            )
        except ValueError:
            is_web_url = False
        if not is_web_url:
            raise ValueError('Try “Search for Python tools”, “Read https://example.com”, or “Run the release briefing”.')

        name = "Webpage read"
        step = {"name": name, "platform": "web", "action": "read", "params": {
            "target": target, "use_jina": False,
        }}

    report = Pipeline(config_dict={"name": name, "steps": [step]}).run()
    if report["success"] and step["platform"] == "web":
        result = report["log"][0]["result"]
        result["content"] = truncate(result["content"], max_length=10000)
    return report


class StudioHandler(BaseHTTPRequestHandler):
    @property
    def _local_host(self) -> str:
        return f"127.0.0.1:{self.server.server_port}"

    def _send(self, status: int, content_type: str, content: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; frame-ancestors 'self'")
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, status: int, result: dict) -> None:
        self._send(status, "application/json", json.dumps(result).encode("utf-8"))

    def do_GET(self) -> None:
        if self.headers.get("Host") != self._local_host:
            self._send_json(403, {"error": "Open Studio at its local URL."})
        elif self.path in PAGES:
            name, content_type = PAGES[self.path]
            self._send(200, content_type, (ASSETS / name).read_bytes())
        elif self.path in {"/api/demo/briefing", "/api/demo/scan"}:
            self._send_json(200, run_demo(self.path.rsplit("/", 1)[1]))
        elif self.path == "/api/connections":
            self._send_json(200, {"connections": connection_status()})
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path not in {"/api/task", "/api/connections", "/api/actions"}:
            self.send_error(404)
            return
        if self.headers.get("Host") != self._local_host or self.headers.get("Origin") != f"http://{self._local_host}":
            self._send_json(403, {"error": "Open Studio at its local URL to continue."})
            return
        if self.headers.get_content_type() != "application/json":
            self._send_json(415, {"error": "Send the task as JSON."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 24_576:
                raise ValueError
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError
        except ValueError:
            self._send_json(400, {"error": "Enter a valid request to continue."})
            return

        try:
            if self.path == "/api/task":
                request = payload.get("request")
                if not isinstance(request, str) or not request.strip() or len(request) > 500:
                    raise ValueError("Enter a request of up to 500 characters.")
                result = run_task(request)
            elif self.path == "/api/connections":
                provider, credential = payload.get("provider"), payload.get("credential")
                if not isinstance(provider, str) or not isinstance(credential, str):
                    raise ValueError("Choose a service and enter its credential.")
                save_connection(provider, credential)
                result = {"success": True, "connections": connection_status()}
            else:
                fields = [payload.get(key, "") for key in ("provider", "repo", "title", "content")]
                if not all(isinstance(value, str) for value in fields):
                    raise ValueError("Enter values for the action's fields.")
                provider, repo, title, content = fields
                result = run_reviewed_action(provider, payload.get("confirmed"), repo, title, content)
        except MissingConnection as exc:
            self._send_json(409, {"error": str(exc), "connection": exc.provider})
            return
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
            return
        except OSError:
            self._send_json(500, {"error": "Studio could not access the local credential vault."})
            return
        self._send_json(200, result)


def create_server(port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), StudioHandler)
