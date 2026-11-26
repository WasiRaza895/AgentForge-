"""Loopback browser interface for AgentForge's bundled read-only demos."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from xml.sax.saxutils import escape

from agentforge.pipeline import Pipeline


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

    def do_GET(self) -> None:
        if self.path in PAGES:
            name, content_type = PAGES[self.path]
            self._send(200, content_type, (ASSETS / name).read_bytes())
        elif self.path in {"/api/demo/briefing", "/api/demo/scan"}:
            result = run_demo(self.path.rsplit("/", 1)[1])
            self._send(200, "application/json", json.dumps(result).encode("utf-8"))
        else:
            self.send_error(404)


def create_server(port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), StudioHandler)
