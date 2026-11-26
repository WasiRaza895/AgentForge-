from agentforge.studio import run_demo


def test_studio_works_from_outside_checkout(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    scan = run_demo("scan")
    assert scan["success"] is True
    assert len(scan["log"]) == 1

    briefing = run_demo("briefing")
    assert briefing["success"] is True
    assert [len(step["result"]["entries"]) for step in briefing["log"]] == [3, 2]
    assert briefing["context_keys"] == ["feed", "related"]
