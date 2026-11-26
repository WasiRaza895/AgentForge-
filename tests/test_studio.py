import json
from unittest.mock import Mock

import httpx
import pytest

from agentforge import utils
from agentforge.studio import run_demo, run_task
from agentforge.studio_ai import DEFAULT_MODEL, Gemini, MissingModel, ModelError, get_model, save_model_key
from agentforge.studio_connections import MissingConnection, connection_status, run_reviewed_action, save_connection


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
    monkeypatch.setattr("agentforge.studio.connection_status", lambda: {"exa": False})

    report = run_task("Could you please search the web for Python tools", use_ai=False)
    assert report["success"] is True
    assert report["log"][0]["result"][0]["title"] == "Python tools"
    platform.search.assert_called_once_with("Python tools", limit=5, use_exa=False)


def test_plain_language_read_uses_direct_http(monkeypatch):
    platform = Mock()
    platform.read.return_value = {"success": True, "content": "Example page"}
    monkeypatch.setattr("agentforge.pipeline.get_platform", lambda name: platform)

    report = run_task("Read example.com", use_ai=False)
    assert report["success"] is True
    assert report["log"][0]["result"]["content"] == "Example page"
    platform.read.assert_called_once_with("https://example.com", use_jina=False)


def test_plain_language_offline_demo():
    assert run_task("Run the release briefing.")["context_keys"] == ["feed", "related"]


@pytest.mark.parametrize("request_text", ["Send an email", "Read file:///local", "Read https://user:password@example.com"])
def test_task_rejects_unsupported_requests(request_text):
    with pytest.raises(ValueError, match="Try"):
        run_task(request_text, use_ai=False)


@pytest.fixture
def local_vault(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "get_config_dir", lambda: tmp_path)
    return tmp_path


def test_studio_configures_a_connection_without_exposing_the_key(local_vault):
    assert connection_status() == {"github": False, "slack": False, "exa": False}
    assert not list(local_vault.iterdir())
    save_connection("github", "example-github-token")
    save_connection("exa", "example-exa-token")
    assert connection_status() == {"github": True, "slack": False, "exa": True}
    encrypted = (local_vault / "credentials.json").read_bytes()
    assert b"example-github-token" not in encrypted and b"example-exa-token" not in encrypted


def test_studio_search_uses_a_configured_exa_key(local_vault, monkeypatch):
    save_connection("exa", "example-exa-token")
    platform = Mock()
    platform.search.return_value = [{"title": "Python tools"}]
    monkeypatch.setattr("agentforge.pipeline.get_platform", lambda name: platform)
    assert run_task("Search for Python tools", use_ai=False)["success"] is True
    platform.search.assert_called_once_with("Python tools", limit=5, use_exa=True)


def test_write_requires_a_credential_and_explicit_review(local_vault, monkeypatch):
    run = Mock()
    monkeypatch.setattr("agentforge.studio_connections.Pipeline.run", run)
    with pytest.raises(MissingConnection) as exc:
        run_reviewed_action("github", True, "owner/repo", "Example", "Details")
    assert exc.value.provider == "github"
    save_connection("github", "example-github-token")
    with pytest.raises(ValueError, match="Review and confirm"):
        run_reviewed_action("github", False, "owner/repo", "Example", "Details")
    run.assert_not_called()


def test_reviewed_issue_uses_github_api_with_the_saved_token(local_vault, monkeypatch):
    save_connection("github", "example-github-token")
    url = "https://github.com/owner/repo/issues/1"
    post = Mock(return_value=httpx.Response(201, json={"html_url": url}))
    monkeypatch.setattr("agentforge.platforms.github_platform.httpx.post", post)
    result = run_reviewed_action("github", True, "owner/repo", "A quoted \"title\"", "Line 1\nLine 2")
    assert result == {"success": True, "message": "GitHub issue created.", "url": url}
    assert post.call_args.args == ("https://api.github.com/repos/owner/repo/issues",)
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer example-github-token"
    assert post.call_args.kwargs["json"] == {"title": 'A quoted "title"', "body": "Line 1\nLine 2"}


def test_reviewed_slack_send_uses_the_saved_webhook(local_vault, monkeypatch):
    with pytest.raises(ValueError, match="Slack incoming webhook"):
        save_connection("slack", "https://example.com/services/T/B/key")
    webhook = "https://hooks.slack.com/services/T/B/example-key"
    save_connection("slack", webhook)
    client = Mock()
    client.__enter__ = Mock(return_value=client)
    client.__exit__ = Mock(return_value=False)
    client.post.return_value = httpx.Response(200, text="ok")
    monkeypatch.setattr("agentforge.platforms.slack.httpx.Client", Mock(return_value=client))
    assert run_reviewed_action("slack", True, "", "", "Reviewed update")["success"] is True
    client.post.assert_called_once_with(webhook, json={"text": "Reviewed update"})


def test_short_search_works_without_a_model(local_vault, monkeypatch):
    search = Mock()
    search.search.return_value = [{"title": "SadaPay"}]
    monkeypatch.setattr("agentforge.pipeline.get_platform", lambda _: search)
    assert run_task("search Saada Pay")["success"] is True
    search.search.assert_called_once_with("Saada Pay", limit=5, use_exa=False)
    with pytest.raises(MissingModel, match="Gemini"):
        run_task("Search Saada Pay, then summarize what it does")


def test_model_setup_checks_key_and_saves_it_locally(local_vault, monkeypatch):
    get = Mock(side_effect=[httpx.Response(403), httpx.Response(200)])
    monkeypatch.setattr("agentforge.studio_ai.httpx.get", get)
    with pytest.raises(ModelError, match="Google AI Studio"):
        save_model_key("test-bad-key")
    assert get_model() is None

    save_model_key("test-gemini-key")
    assert get_model() == Gemini("test-gemini-key")
    assert get.call_args.args[0].endswith(DEFAULT_MODEL)
    assert get.call_args.kwargs["headers"] == {"x-goog-api-key": "test-gemini-key"}
    assert b"test-gemini-key" not in (local_vault / "credentials.json").read_bytes()


def test_gemini_plan_searches_summarizes_and_waits_for_review(local_vault, monkeypatch):
    steps = [{"action": "search", "input": "Saada Pay"}, {"action": "summarize", "input": "what it does"}, {"action": "slack_message", "input": ""}]
    summary = "SadaPay result from https://example.com/source."

    def candidate(value):
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": value}]}}]})

    monkeypatch.setattr("agentforge.studio_ai.httpx.get", Mock(return_value=httpx.Response(200)))
    post = Mock(side_effect=[candidate(json.dumps({"steps": steps, "message": ""})), candidate(summary)])
    monkeypatch.setattr("agentforge.studio_ai.httpx.post", post)
    save_model_key("test-gemini-key")
    search = Mock()
    search.search.return_value = [{"title": "SadaPay", "url": "https://example.com/source"}]
    lookup = Mock(return_value=search)
    monkeypatch.setattr("agentforge.pipeline.get_platform", lookup)

    report = run_task("Search Saada Pay and send a summary to Slack")

    assert report["success"] and report["model"] == "Google Gemini"
    assert report["summary"] == summary
    assert report["draft"] == {"provider": "slack", "repo": "", "title": "", "content": summary}
    lookup.assert_called_once_with("search")
    search.write.assert_not_called()
    assert post.call_args_list[0].kwargs["json"]["generationConfig"]["responseMimeType"] == "application/json"
    assert "https://example.com/source" in post.call_args_list[1].kwargs["json"]["contents"][0]["parts"][0]["text"]


def test_google_key_is_not_forwarded_to_the_exa_service(local_vault):
    with pytest.raises(ValueError, match="AI Model"):
        save_connection("exa", "AIza-example-old-google-api-key")
