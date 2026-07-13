# 🔨 AgentForge

<p align="center">
  <strong>Give your AI agent hands to act on the internet—not just eyes to read it.</strong>
</p>

<p align="center">
  A local-first Python CLI for reading, writing, searching, notifying, and running<br />
  multi-platform workflows from one consistent interface.
</p>

<p align="center">
  <a href="https://github.com/WasiRaza895/AgentForge-/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/WasiRaza895/AgentForge-/ci.yml?branch=main&style=flat-square&label=tests"></a>
  <a href="https://www.python.org/"><img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-blue?style=flat-square"></a>
  <a href="https://github.com/WasiRaza895/AgentForge-/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/WasiRaza895/AgentForge-?style=flat-square"></a>
</p>

> [!IMPORTANT]
> AgentForge is alpha software. Read-only commands are the safest place to start. Review every write action and workflow before using real accounts.

## Why AgentForge?

Agent tools often stop at research. AgentForge adds a shared command surface for actions: search the web, read feeds, create GitHub issues, send notifications, post updates, and chain steps together in YAML. Credentials stay in a local encrypted vault, and structured output makes commands easy to consume from scripts and AI coding tools.

- **One CLI:** a consistent interface across 12 platform adapters.
- **Read and write:** move from gathering context to taking an approved action.
- **Composable workflows:** connect platform actions with declarative YAML pipelines.
- **Local-first credentials:** encrypt secrets at rest instead of putting them in workflow files.
- **Agent-friendly output:** render results as text, JSON, CSV, or Markdown.
- **Extensible:** add custom platform adapters through the plugin loader.

## Quick start

AgentForge requires Python 3.10 or newer.

```bash
git clone https://github.com/WasiRaza895/AgentForge-.git
cd AgentForge-
python -m venv .venv
```

Activate the environment and install the project:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

python -m pip install .
agentforge --version
agentforge doctor
```

Try a read-only command:

```bash
agentforge search "open-source AI agent tools" --limit 5
agentforge web https://example.com
agentforge --output json rss https://hnrss.org/frontpage
```

See the [installation guide](docs/install.md) and [quick-start guide](docs/quickstart.md) for more detail.

## What can it connect to?

| Platform | Read | Search | Write | Integration |
|---|:---:|:---:|:---:|---|
| Web | ✅ | — | — | Direct HTTP / Jina Reader |
| Search | — | ✅ | — | DuckDuckGo / optional Exa |
| YouTube | ✅ | ✅ | — | `yt-dlp` |
| RSS / Atom | ✅ | — | — | `feedparser` |
| GitHub | ✅ | ✅ | ✅ | GitHub CLI |
| Twitter / X | ✅ | ✅ | ✅ | Nitter / `xreach` / API |
| Reddit | ✅ | ✅ | ✅ | JSON API / PRAW |
| LinkedIn | ✅ | — | ✅ | Jina Reader / REST API |
| Slack | — | — | ✅ | Webhooks |
| Discord | — | — | ✅ | Webhooks |
| Telegram | — | — | ✅ | Bot API |
| Email | — | — | ✅ | SMTP |

Some capabilities require third-party CLI tools, API access, or platform credentials. Run `agentforge doctor` to see what is available on your machine.

## Common commands

```bash
# GitHub
agentforge github read owner/repo
agentforge github create-issue owner/repo --title "Bug" --body "Details"

# Social platforms
agentforge twitter read https://twitter.com/user/status/123456
agentforge reddit search "local AI agents" --sub LocalLLaMA

# Notifications
agentforge notify setup team-alerts --type slack --url "https://hooks.slack.com/..."
agentforge notify send team-alerts "AgentForge workflow completed"

# Local credentials (values are masked when listed)
agentforge vault set twitter api_key "YOUR_API_KEY"
agentforge vault list
```

Use least-privilege credentials and never paste real tokens into committed scripts or issue reports.

## Workflow example

Create `daily_digest.yaml`:

```yaml
name: Daily AI research digest
steps:
  - name: Find updates
    platform: search
    action: search
    params:
      query: "open-source AI agents"
      limit: 5
    output_var: results

  - name: Notify the team
    platform: slack
    action: send
    params:
      message: "Found {results.count} relevant updates."
```

Validate and run it:

```bash
agentforge pipeline validate daily_digest.yaml
agentforge pipeline run daily_digest.yaml
```

More examples are available in [`examples/`](examples/).

## How it is organized

```text
src/agentforge/
├── platforms/     # Built-in platform adapters
├── plugins/       # Third-party adapter loading
├── cli.py         # Click command interface
├── pipeline.py    # YAML workflow engine
├── scheduler.py   # Repeating monitors
├── notifier.py    # Named notification channels
└── vault.py       # Encrypted local credentials
```

The agent usage playbook lives at [`skill/SKILL.md`](skill/SKILL.md). Plugin authors can start with the [plugin guide](docs/plugins.md).

## Project status and roadmap

The current focus is making the core reliable before expanding its surface area:

- [x] Unified CLI and structured output
- [x] YAML pipelines, scheduling, notifications, and encrypted vault
- [x] Built-in platform adapter and plugin architecture
- [x] Multi-version continuous integration
- [ ] More mocked integration tests and clearer platform error messages
- [ ] Stable configuration schema and migration policy
- [ ] Package publishing and signed releases
- [ ] Native MCP server interface

Have a use case that should influence the roadmap? Open a [feature request](https://github.com/WasiRaza895/AgentForge-/issues/new/choose).

## Contributing

Contributions are welcome. Start with [`CONTRIBUTING.md`](CONTRIBUTING.md), keep pull requests focused, and include tests for behavior changes. Security problems should be reported privately according to [`SECURITY.md`](SECURITY.md).

If AgentForge is useful to you, starring the repository and sharing a real workflow are the most helpful ways to support its early development.

## License

AgentForge is available under the [MIT License](LICENSE).
