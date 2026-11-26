"""Loopback browser interface for AgentForge's supported read-only tasks."""

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape

from agentforge.pipeline import Pipeline
from agentforge.utils import truncate


ASSETS = Path(__file__).with_name("studio_assets")
PAGES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/studio.css": ("studio.css", "text/css; charset=utf-8"),
    "/studio.js": ("studio.js", "text/javascript; charset=utf-8"),
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
            "query": search.group(1), "limit": 5, "use_exa": False,
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
        if self.path in PAGES:
            name, content_type = PAGES[self.path]
            self._send(200, content_type, (ASSETS / name).read_bytes())
        elif self.path in {"/api/demo/briefing", "/api/demo/scan"}:
            self._send_json(200, run_demo(self.path.rsplit("/", 1)[1]))
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/api/task":
            self.send_error(404)
            return
        host = f"127.0.0.1:{self.server.server_port}"
        if self.headers.get("Host") != host or self.headers.get("Origin") != f"http://{host}":
            self._send_json(403, {"error": "Open Studio at its local URL to run a task."})
            return
        if self.headers.get_content_type() != "application/json":
            self._send_json(415, {"error": "Send the task as JSON."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError
            payload = json.loads(self.rfile.read(length))
        except ValueError:
            self._send_json(400, {"error": "Enter a short request to run a task."})
            return
        request = payload.get("request") if isinstance(payload, dict) else None
        if not isinstance(request, str) or not request.strip():
            self._send_json(400, {"error": "Enter a request to run a task."})
            return

        try:
            result = run_task(request)
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
            return
        self._send_json(200, result)


def create_server(port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), StudioHandler)
