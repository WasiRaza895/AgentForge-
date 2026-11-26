import json
from click.testing import CliRunner
from agentforge.cli import cli
from agentforge import __version__

def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert "CLI: Read, Write, and Automate" in result.output

def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert __version__ in result.output

def test_cli_doctor():
    runner = CliRunner()
    result = runner.invoke(cli, ['doctor'])
    assert result.exit_code == 0
    assert "System Environment Diagnostics" in result.output

def test_cli_vault(tmp_path, monkeypatch):
    # Keep test credentials isolated from the developer's real vault.
    monkeypatch.setattr(
        "agentforge.utils.get_config_dir",
        lambda: tmp_path / ".agentforge",
    )
    runner = CliRunner()
    
    # Test setting a credential
    set_res = runner.invoke(cli, ['vault', 'set', 'test_platform', 'test_key', 'test_val'])
    assert set_res.exit_code == 0
    
    # Test listing credentials
    list_res = runner.invoke(cli, ['vault', 'list'])
    assert list_res.exit_code == 0
    assert "test_platform" in list_res.output
    
    # Test getting a credential
    get_res = runner.invoke(cli, ['vault', 'get', 'test_platform', 'test_key'])
    assert get_res.exit_code == 0
    assert "test_val" in get_res.output
    
    # Test deleting credential
    del_res = runner.invoke(cli, ['vault', 'delete', 'test_platform', 'test_key'])
    assert del_res.exit_code == 0
    
    # Verify deletion
    verify_res = runner.invoke(cli, ['vault', 'get', 'test_platform', 'test_key'])
    assert "error" in verify_res.output


def test_cli_workflow_failure_returns_nonzero(tmp_path):
    workflow = tmp_path / "bad.yaml"
    workflow.write_text("name: Invalid\nsteps:\n  - bad-step\n", encoding="utf-8")
    runner = CliRunner()
    for action in ("run", "validate"):
        result = runner.invoke(cli, ["--output", "json", "pipeline", action, str(workflow)])
        assert result.exit_code == 1
        assert "Expected a mapping" in json.dumps(json.loads(result.output))


def test_cli_runs_bundled_briefing():
    result = CliRunner().invoke(cli, ["--output", "json", "pipeline", "run", "examples/rss_briefing.yaml"])
    assert result.exit_code == 0
    report = json.loads(result.output)
    assert [len(step["result"]["entries"]) for step in report["log"]] == [3, 2]
