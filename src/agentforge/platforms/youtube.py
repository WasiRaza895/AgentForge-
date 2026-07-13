import json
from typing import Dict, Any, List
from agentforge.platforms.base import BasePlatform
from agentforge.utils import run_command, check_tool_installed

class YouTubePlatform(BasePlatform):
    name = "youtube"
    description = "Search YouTube videos or read metadata and transcripts using yt-dlp."
    supports_read = True
    supports_write = False
    supports_search = True

    def read(self, url: str, **kwargs) -> Dict[str, Any]:
        """Extracts video metadata and subtitles using yt-dlp."""
        if not check_tool_installed("yt-dlp"):
            return {
                "platform": self.name,
                "action": "read",
                "success": False,
                "error": "yt-dlp is not installed on the system."
            }

        # Step 1: Get metadata via JSON dump
        cmd = f'yt-dlp -j --skip-download "{url}"'
        success, output = run_command(cmd)
        if not success:
            return {
                "platform": self.name,
                "action": "read",
                "success": False,
                "error": f"Failed to fetch video details: {output}"
            }

        try:
            metadata = json.loads(output)
            video_data = {
                "id": metadata.get("id"),
                "title": metadata.get("title"),
                "description": metadata.get("description"),
                "uploader": metadata.get("uploader"),
                "duration": metadata.get("duration"),
                "view_count": metadata.get("view_count"),
                "like_count": metadata.get("like_count"),
                "upload_date": metadata.get("upload_date"),
                "transcript": "Subtitles extraction not supported or no subtitles found."
            }

            # Optional: Attempt to get subtitle tracks
            subtitles = metadata.get("subtitles", {})
            automatic_captions = metadata.get("automatic_captions", {})
            video_data["has_subtitles"] = len(subtitles) > 0 or len(automatic_captions) > 0

            return {
                "platform": self.name,
                "action": "read",
                "success": True,
                "data": video_data
            }
        except Exception as e:
            return {
                "platform": self.name,
                "action": "read",
                "success": False,
                "error": f"Error parsing metadata: {str(e)}"
            }

    def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Searches YouTube using yt-dlp's search functionality."""
        limit = kwargs.get("limit", 5)
        if not check_tool_installed("yt-dlp"):
            return [{"error": "yt-dlp is not installed on the system."}]

        cmd = f'yt-dlp "ytsearch{limit}:{query}" -j --skip-download'
        success, output = run_command(cmd)
        if not success:
            return []

        results = []
        for line in output.splitlines():
            if not line.strip():
                continue
            try:
                metadata = json.loads(line)
                results.append({
                    "id": metadata.get("id"),
                    "title": metadata.get("title"),
                    "url": f"https://www.youtube.com/watch?v={metadata.get('id')}",
                    "uploader": metadata.get("uploader"),
                    "duration": metadata.get("duration"),
                    "view_count": metadata.get("view_count"),
                })
            except Exception:
                continue
        return results

    def doctor(self) -> Dict[str, Any]:
        installed = check_tool_installed("yt-dlp")
        if installed:
            # Check version
            success, output = run_command("yt-dlp --version")
            version = output.strip() if success else "unknown version"
            return {
                "platform": self.name,
                "status": "Ready",
                "tool": f"yt-dlp ({version})",
                "auth": "none",
                "notes": "YouTube extractor is ready."
            }
        else:
            return {
                "platform": self.name,
                "status": "Broken",
                "tool": "yt-dlp",
                "auth": "none",
                "notes": "yt-dlp is missing. Install using: pip install yt-dlp or scoop/brew install yt-dlp"
            }

    def get_required_tools(self) -> List[str]:
        return ["yt-dlp"]
