import schedule
import threading
import time
import uuid
from typing import Dict, Any, List, Optional, Callable
from agentforge.platforms import get_platform
from agentforge.notifier import Notifier

class WatchJob:
    """A scheduled monitoring job that queries a platform, detects new items, and notifies."""
    
    def __init__(self, platform: str, query: str, interval_seconds: int, notify_channel: str, callback: Optional[Callable] = None):
        self.id = str(uuid.uuid4())[:8]
        self.platform_name = platform
        self.query = query
        self.interval_seconds = interval_seconds
        self.notify_channel = notify_channel
        self.callback = callback
        
        self.last_seen_ids = set()
        self.first_run = True

    def _get_item_id(self, item: Dict[str, Any]) -> str:
        """Extracts a unique identity string for a result item."""
        # Check standard id fields
        for field in ("id", "url", "link", "title"):
            if item.get(field):
                return str(item.get(field))
        # Hash items as fallback
        return str(hash(frozenset(item.items())))

    def run_check(self) -> None:
        """Executes search and alerts on new results."""
        try:
            platform = get_platform(self.platform_name)
            results = platform.search(self.query)
            
            # Filter valid result list
            if not isinstance(results, list) or not results or "error" in results[0]:
                return

            new_items = []
            current_ids = set()
            
            for item in results:
                item_id = self._get_item_id(item)
                current_ids.add(item_id)
                if item_id not in self.last_seen_ids:
                    new_items.append(item)
                    
            # Update cache
            self.last_seen_ids = current_ids
            
            # Don't spam notifications on initial startup/empty cache
            if self.first_run:
                self.first_run = False
                return

            if new_items:
                message = f"🔔 [AgentForge] New results found on {self.platform_name.upper()} for: \"{self.query}\"\n\n"
                for idx, item in enumerate(new_items[:3], 1):
                    title = item.get("title", item.get("text", "No details"))
                    url = item.get("url", item.get("link", ""))
                    message += f"{idx}. {title}\n   Link: {url}\n\n"
                
                if len(new_items) > 3:
                    message += f"... and {len(new_items) - 3} more new items."
                    
                # Dispatch notification
                notifier = Notifier()
                notifier.send(self.notify_channel, message)
                
                if self.callback:
                    self.callback(new_items)
        except Exception:
            pass  # Fail silently in scheduler thread

class Scheduler:
    """Manages background threads running scheduled monitoring loops."""
    
    def __init__(self):
        self.jobs: Dict[str, WatchJob] = {}
        self._thread: Optional[threading.Thread] = None
        self._running = False

    @staticmethod
    def parse_interval(interval_str: str) -> int:
        """Parses '30m', '1h', '1d' into seconds."""
        match = re.match(r"^(\d+)([mhd])$", interval_str.strip().lower())
        if not match:
            raise ValueError(f"Invalid interval format: {interval_str}. Use e.g. 30m, 1h, 1d.")
        val, unit = match.groups()
        val = int(val)
        if unit == "m":
            return val * 60
        elif unit == "h":
            return val * 3600
        elif unit == "d":
            return val * 86400
        return 3600

    def add_watch(self, platform: str, query: str, interval_str: str, notify_channel: str) -> str:
        """Registers a new watch task."""
        seconds = self.parse_interval(interval_str)
        job = WatchJob(platform, query, seconds, notify_channel)
        
        # Schedule the check
        schedule.every(seconds).seconds.do(job.run_check).tag(job.id)
        self.jobs[job.id] = job
        
        # Run initial check asynchronously
        threading.Thread(target=job.run_check, daemon=True).start()
        return job.id

    def list_jobs(self) -> List[Dict[str, Any]]:
        """Returns details on all active jobs."""
        return [
            {
                "id": j.id,
                "platform": j.platform_name,
                "query": j.query,
                "interval_seconds": j.interval_seconds,
                "notify_channel": j.notify_channel
            }
            for j in self.jobs.values()
        ]

    def remove_job(self, job_id: str) -> bool:
        """Cancels a scheduled job by its tag."""
        if job_id in self.jobs:
            schedule.clear(job_id)
            del self.jobs[job_id]
            return True
        return False

    def _loop(self) -> None:
        while self._running:
            schedule.run_pending()
            time.sleep(1)

    def start(self) -> None:
        """Starts the scheduler thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stops the scheduler thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
import re
