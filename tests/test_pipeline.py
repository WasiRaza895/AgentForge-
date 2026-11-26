from unittest.mock import Mock

from agentforge.pipeline import Pipeline

def test_pipeline_validation_empty():
    p = Pipeline(config_dict={})
    errors = p.validate()
    assert "Pipeline configuration is empty." in errors

def test_pipeline_validation_missing_fields():
    config = {
        "name": "Invalid Pipeline",
        "steps": [
            {"platform": "web"} # missing action
        ]
    }
    p = Pipeline(config_dict=config)
    errors = p.validate()
    assert "[Step 0] Missing 'action' parameter." in errors

def test_pipeline_variable_resolution():
    p = Pipeline(config_dict={})
    context = {
        "search_results": {
            "platform": "search",
            "action": "search",
            "success": True,
            "data": {
                "title": "HackerNews",
                "count": 5
            }
        }
    }
    
    # Test simple lookup
    val = "{search_results.data.title}"
    resolved = p._resolve_variables(val, context)
    assert resolved == "HackerNews"
    
    # Test string interpolation
    val2 = "The title is {search_results.data.title} and count is {search_results.data.count}"
    resolved2 = p._resolve_variables(val2, context)
    assert resolved2 == "The title is HackerNews and count is 5"

def test_pipeline_run_failed_step(monkeypatch):
    slack = Mock()
    slack.write.return_value = {"success": False, "error": "No webhook configured"}
    monkeypatch.setattr("agentforge.pipeline.get_platform", lambda _: slack)
    config = {
        "name": "Failed Pipeline",
        "steps": [
            {
                "name": "Step One",
                "platform": "slack",
                "action": "send",
                "params": {
                    "content": "Hello"
                },
                "abort_on_failure": True
            }
        ]
    }
    p = Pipeline(config_dict=config)
    res = p.run()
    assert res["success"] is False
    assert len(res["log"]) == 1
    assert res["log"][0]["success"] is False
    slack.write.assert_called_once_with("Hello")


def test_search_result_flows_into_notification(monkeypatch):
    search, slack = Mock(), Mock()
    search.search.return_value = [{"title": "A result"}]
    slack.write.return_value = {"success": True}
    monkeypatch.setattr("agentforge.pipeline.get_platform", {"search": search, "slack": slack}.__getitem__)
    pipeline = Pipeline(config_dict={"name": "Digest", "steps": [
        {"platform": "search", "action": "search", "params": {"query": "Python", "limit": 1}, "output_var": "results"},
        {"platform": "slack", "action": "send", "params": {"message": "Found {results.count}: {results.0.title}"}},
    ]})
    assert pipeline.run()["success"] is True
    search.search.assert_called_once_with("Python", limit=1)
    slack.write.assert_called_once_with("Found 1: A result")


def test_search_error_stops_workflow(monkeypatch):
    search, slack = Mock(), Mock()
    search.search.return_value = [{"error": "Provider unavailable"}]
    monkeypatch.setattr("agentforge.pipeline.get_platform", {"search": search, "slack": slack}.__getitem__)
    pipeline = Pipeline(config_dict={"name": "Digest", "steps": [
        {"platform": "search", "action": "search", "params": {"query": "Python"}},
        {"platform": "slack", "action": "send", "params": {"message": "Update"}},
    ]})
    result = pipeline.run()
    assert result["success"] is False
    assert result["log"][0]["error"] == "Provider unavailable"
    slack.write.assert_not_called()


def test_workflow_can_use_a_local_plugin(tmp_path, monkeypatch):
    from agentforge.plugins.loader import PluginLoader

    monkeypatch.setattr("agentforge.utils.get_config_dir", lambda: tmp_path)
    PluginLoader().create_plugin_template("sample_plugin", "SamplePlugin")
    pipeline = Pipeline(config_dict={"name": "Plugin", "steps": [
        {"platform": "sample_plugin", "action": "read", "params": {"target": "sample"}},
    ]})
    result = pipeline.run()
    assert result["success"] is True
    assert result["log"][0]["result"]["target"] == "sample"
