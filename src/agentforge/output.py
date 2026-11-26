import json
import csv
import sys
from typing import Any, Union, Dict, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

class OutputFormatter:
    """Formatter to render CLI outputs in multiple formats (text, JSON, CSV, Markdown)."""
    
    @staticmethod
    def render(data: Any, format_type: str = "text") -> None:
        """Renders the given data using the specified format type."""
        console = Console()
        
        # If output is raw string, handle directly
        if isinstance(data, str) and format_type == "text":
            console.print(data)
            return

        if format_type == "json":
            OutputFormatter.to_json(data)
        elif format_type == "csv":
            OutputFormatter.to_csv(data)
        elif format_type == "markdown":
            OutputFormatter.to_markdown(data, console)
        else:
            OutputFormatter.to_text(data, console)

    @staticmethod
    def to_json(data: Any, console: Console | None = None) -> None:
        """Writes parseable JSON directly to the output stream."""
        stream = console.file if console is not None else sys.stdout
        json.dump(data, stream, indent=2)
        stream.write("\n")

    @staticmethod
    def to_csv(data: Any) -> None:
        """Prints tabular data in CSV format to stdout."""
        writer = csv.writer(sys.stdout)
        
        if isinstance(data, list):
            if not data:
                return
            # Assume list of dicts
            if isinstance(data[0], dict):
                headers = list(data[0].keys())
                writer.writerow(headers)
                for item in data:
                    writer.writerow([item.get(h, "") for h in headers])
            else:
                for row in data:
                    writer.writerow([row] if not isinstance(row, (list, tuple)) else row)
        elif isinstance(data, dict):
            # Key-Value output
            writer.writerow(["Key", "Value"])
            for k, v in data.items():
                writer.writerow([k, v])
        else:
            writer.writerow([data])

    @staticmethod
    def to_markdown(data: Any, console: Console) -> None:
        """Prints data as a Markdown formatted table or text."""
        if isinstance(data, list):
            if not data:
                console.print("*Empty results*")
                return
            if isinstance(data[0], dict):
                headers = list(data[0].keys())
                console.print("| " + " | ".join(headers) + " |")
                console.print("| " + " | ".join(["---"] * len(headers)) + " |")
                for item in data:
                    row_vals = [str(item.get(h, "")).replace("\n", " ") for h in headers]
                    console.print("| " + " | ".join(row_vals) + " |")
            else:
                for idx, val in enumerate(data):
                    console.print(f"- {val}")
        elif isinstance(data, dict):
            console.print("| Key | Value |")
            console.print("| --- | --- |")
            for k, v in data.items():
                val_str = str(v).replace("\n", "<br>")
                console.print(f"| {k} | {val_str} |")
        else:
            console.print(str(data))

    @staticmethod
    def to_text(data: Any, console: Console) -> None:
        """Prints data using rich console representation (tables, panels)."""
        if isinstance(data, list):
            if not data:
                console.print("[yellow]No data available.[/yellow]")
                return
            if isinstance(data[0], dict):
                # Build rich table
                table = Table(show_header=True, header_style="bold magenta")
                headers = list(data[0].keys())
                for h in headers:
                    table.add_column(h)
                for item in data:
                    table.add_row(*[str(item.get(h, "")) for h in headers])
                console.print(table)
            else:
                for item in data:
                    console.print(f"• {item}")
        elif isinstance(data, dict):
            # Print as key-value table
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Property", style="bold")
            table.add_column("Value")
            for k, v in data.items():
                table.add_row(k, str(v))
            console.print(table)
        else:
            console.print(Panel(str(data), title="Result"))
