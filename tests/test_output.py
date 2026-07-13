import pytest
from rich.console import Console
from agentforge.output import OutputFormatter

def test_output_render_json(capsys):
    data = {"key": "value"}
    OutputFormatter.render(data, format_type="json")
    captured = capsys.readouterr()
    # Check if value exists in output
    assert "key" in captured.out
    assert "value" in captured.out

def test_output_render_csv(capsys):
    data = [{"header1": "val1", "header2": "val2"}]
    OutputFormatter.render(data, format_type="csv")
    captured = capsys.readouterr()
    lines = captured.out.strip().split("\r\n")
    if len(lines) == 1:
        lines = captured.out.strip().split("\n")
    assert "header1,header2" in lines[0]
    assert "val1,val2" in lines[1]

def test_output_render_markdown(capsys):
    data = {"title": "Hello", "views": 100}
    OutputFormatter.render(data, format_type="markdown")
    captured = capsys.readouterr()
    assert "| Key | Value |" in captured.out
    assert "| title | Hello |" in captured.out
    assert "| views | 100 |" in captured.out

def test_output_render_text(capsys):
    data = {"name": "Test Platform", "status": "Ready"}
    OutputFormatter.render(data, format_type="text")
    captured = capsys.readouterr()
    assert "Property" in captured.out
    assert "Value" in captured.out
    assert "Test Platform" in captured.out
