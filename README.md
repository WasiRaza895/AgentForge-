# 🔨 AgentForge

**Give your AI agent hands to act on the internet—not just eyes to read it.**

AgentForge is a local-first toolkit for reading, writing, searching, notifying, and running workflows across platforms. In Studio, connect Google Gemini and describe a task in plain English. Gemini chooses the tools and AgentForge runs them. You can also call the same AgentForge adapters from the CLI or a YAML workflow.

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

- **12 built-in adapters** for web, feeds, search, and platform actions. Some require external tools or account credentials.
- **YAML workflows** that pass data between steps and report what ran, what failed, and where execution stopped.
- **Local credentials** stored in an encrypted vault with a key on the same machine.
- **Scriptable output** in text, JSON, CSV, or Markdown.
- **Local plugins** that can add trusted Python adapters to workflows.

## Connect an AI model

In Studio, open **AI Model** and paste a Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey). Select **Connect Gemini** to check the key and save it in the local encrypted vault. Studio sends your task and the results needed for a summary to Gemini. It uses Gemini 3.5 Flash-Lite to plan the task and AgentForge adapters to perform the steps.

Try `search Saada Pay` or `Search Saada Pay, then summarize what it does`. To try a workflow across services, enter `Search Saada Pay, summarize what it does, then send the summary to Slack`. Studio shows the draft for review before posting. Short searches, webpage reads, and the offline briefing also run directly when Gemini is disconnected.

## Service connections

Use **Service Connections** for credentials that authorize actions on the platforms you use. Choose a service, paste its credential, and select **Save locally**. Studio asks for the missing credential when you open a write action.

| Service | What to add in Studio | What it enables |
|---|---|---|
| GitHub | A fine-grained access token with **Issues: write** on the target repository | Create an issue after you review the repository, title, and description. [GitHub setup](https://docs.github.com/en/rest/issues/issues#create-an-issue) |
| Slack | An incoming webhook URL for the destination channel | Send a message after you review the content and destination. [Slack setup](https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/) |
| Exa | An Exa API key | Use Exa for web searches. AgentForge can also search via DuckDuckGo without a key. [Exa API](https://docs.exa.ai/reference/search) |

Gemini plans with its model key. GitHub and Slack use their own credentials to carry out actions. Use `agentforge doctor` and `agentforge vault` to configure other adapters from the CLI.

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
.\.venv\Scripts\Activate.ps1

python -m pip install .
agentforge --version
```

From the repository root, run a workflow with the bundled feeds. It needs no API keys or network connection.

```bash
agentforge pipeline validate examples/rss_briefing.yaml
agentforge --output json pipeline run examples/rss_briefing.yaml
```

The first step reads three release notes. The second uses the first step's `{feed.metadata.link}` to read two implementation notes. The JSON result includes a log for both steps.

Start Studio and keep the terminal running while you use it.

```bash
agentforge studio --open
```

Under **What should AgentForge do?**, try `search Saada Pay`, `Read https://example.com`, or `Run the release briefing`. Live web tasks need internet access. The bundled briefing runs offline. To take an action, choose **Create a GitHub issue** or **Send a Slack message**, check the details, and confirm. Use **Workflows** to inspect the bundled YAML and copy its JSON output.

### Using AgentForge with an AI assistant

An AI assistant can use AgentForge commands to read sources, search, and perform actions on connected services, or put those commands together in YAML. The assistant handles the planning and AgentForge performs the steps. Review an assistant's proposed writes before it runs them.

Try a live read or check which integrations are available locally.

```bash
agentforge web https://example.com --no-jina
agentforge search "open-source AI agent tools" --limit 5
agentforge doctor
```

See the [installation guide](docs/install.md) and [quick-start guide](docs/quickstart.md) for more detail.

## What can it connect to?

| Platform | Read | Search | Write | Integration |
|---|:---:|:---:|:---:|---|
| Web | ✅ | — | — | Direct HTTP / Jina Reader |
| Search | — | ✅ | — | DuckDuckGo / optional Exa |
| YouTube | ✅ | ✅ | — | `yt-dlp` |
| RSS / Atom | ✅ | — | — | `feedparser` |
| GitHub | ✅ | ✅ | ✅ | GitHub CLI, with direct API issue creation in Studio |
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

## Search-to-Slack example

Set a Slack incoming webhook in the local vault, then save the YAML as `daily_digest.yaml`. Running this workflow sends a message to the configured Slack channel.

```bash
agentforge vault set slack webhook_url "YOUR_SLACK_WEBHOOK_URL"
```

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

Validate the YAML before running the workflow.

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
├── studio.py      # Local browser workspace for bundled demos
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
