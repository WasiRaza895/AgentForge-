from unittest.mock import Mock

import pytest

from agentforge.studio import run_demo, run_task


def test_studio_works_from_outside_checkout(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    scan = run_demo("scan")
    assert scan["success"] is True
    assert len(scan["log"]) == 1

    briefing = run_demo("briefing")
    assert briefing["success"] is True
    assert [len(step["result"]["entries"]) for step in briefing["log"]] == [3, 2]
    assert briefing["context_keys"] == ["feed", "related"]


def test_plain_language_search_uses_no_api_key(monkeypatch):
    platform = Mock()
    platform.search.return_value = [{"title": "Python tools"}]
    monkeypatch.setattr("agentforge.pipeline.get_platform", lambda name: platform)

    report = run_task("Could you please search the web for Python tools")
    assert report["success"] is True
    assert report["log"][0]["result"][0]["title"] == "Python tools"
    platform.search.assert_called_once_with("Python tools", limit=5, use_exa=False)


def test_plain_language_read_uses_direct_http(monkeypatch):
    platform = Mock()
    platform.read.return_value = {"success": True, "content": "Example page"}
    monkeypatch.setattr("agentforge.pipeline.get_platform", lambda name: platform)

    report = run_task("Read example.com")
    assert report["success"] is True
    assert report["log"][0]["result"]["content"] == "Example page"
    platform.read.assert_called_once_with("https://example.com", use_jina=False)


def test_plain_language_offline_demo():
    assert run_task("Run the release briefing.")["context_keys"] == ["feed", "related"]


@pytest.mark.parametrize("request_text", ["Send an email", "Read file:///local", "Read https://user:password@example.com"])
def test_task_rejects_unsupported_requests(request_text):
    with pytest.raises(ValueError, match="Try"):
        run_task(request_text)
