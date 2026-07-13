import pytest
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

def test_pipeline_run_failed_step():
    config = {
        "name": "Failed Pipeline",
        "steps": [
            {
                "name": "Step One",
                "platform": "slack", # slack write will fail because webhook is missing
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
