# 🔨 AgentForge

<p align="center">
  <strong>Give your AI agent hands to shape the internet — not just eyes to read it.</strong>
</p>

<p align="center">
  Read tweets. Post threads. Monitor competitors. Automate workflows.<br>
  One CLI. Zero API fees. Works natively with Claude Code, Cursor, Windsurf, OpenClaw & more.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="MIT License" /></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10+-green.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" /></a>
</p>

---

## 📖 Table of Contents
- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [Feature Comparison](#feature-comparison)
- [Supported Platforms](#supported-platforms)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Workflow Pipelines (YAML)](#workflow-pipelines-yaml)
- [Automated Keyword Monitoring](#automated-keyword-monitoring)
- [Notification Dispatcher](#notification-dispatcher)
- [Secure Credential Vault](#secure-credential-vault)
- [For AI Agents (SKILL.md)](#for-ai-agents-skillmd)
- [Plugin System](#plugin-system)
- [License](#license)

---

## The Problem

Existing tools (like Agent-Reach) give your AI agent **eyes** to read the internet.
But reading is only half the story.

- Your agent can search Twitter — *but it cannot post a thread or reply.*
- Your agent can read Reddit — *but it cannot comment or engage.*
- Your agent can read GitHub issues — *but it cannot create one.*
- Your agent can do research — *but it cannot send a Slack summary, Discord alert, or email digest.*

**AgentForge gives your agent HANDS.**

---

## The Solution

AgentForge is a local-first, zero-fee command-line interface (CLI) and Model Context Protocol (MCP) server that empowers AI agents to perform bidirectional actions (both **READ** and **WRITE**) across 12+ platforms, coordinate them in declarative YAML pipelines, and monitor keywords on cron schedules.

---

## Feature Comparison

| Capability | Agent-Reach | **AgentForge** |
|---|---|---|
| 📖 Read Twitter, Reddit, YouTube | ✅ | ✅ |
| 🌐 General web scraping & search | ✅ | ✅ |
| ✍️ Write & reply on Twitter/X | ❌ | **✅ (Tweepy / xreach)** |
| ✍️ Submit & reply on Reddit | ❌ | **✅ (PRAW)** |
| ✍️ Create issues, PRs, comments on GitHub | ❌ | **✅ (gh CLI)** |
| ✍️ Post updates to LinkedIn | ❌ | **✅ (REST API)** |
| 📧 Send SMTP Emails (HTML, CC) | ❌ | **✅ (smtplib)** |
| 💬 Slack & Discord notification webhooks | ❌ | **✅ (httpx)** |
| 💬 Telegram message sending | ❌ | **✅ (Bot API)** |
| 🔗 Cross-platform YAML workflows | ❌ | **✅ (Pipeline Engine)** |
| 👁️ Scheduled keyword monitoring | ❌ | **✅ (Scheduler)** |
| 🔐 Encrypted credential storage | ❌ | **✅ (AES/Fernet Vault)** |
| 🔌 Dynamic plugin support | ❌ | **✅ (Loader)** |

---

## Supported Platforms

| Platform | Read | Write | Search | Auth Method |
|---|---|---|---|---|
| **Web** | ✅ (Jina / direct) | ❌ | ❌ | None |
| **Search** | ❌ | ❌ | ✅ (Exa / DDG) | Optional Exa API key |
| **YouTube** | ✅ (yt-dlp) | ❌ | ✅ (yt-dlp) | None |
| **RSS** | ✅ (feedparser) | ❌ | ❌ | None |
| **GitHub** | ✅ (gh CLI) | ✅ (issue, PR, comment) | ✅ (gh CLI) | Optional Vault Token |
| **Twitter/X** | ✅ (Nitter / xreach) | ✅ (post, reply) | ✅ (Nitter / xreach) | Optional API Keys |
| **Reddit** | ✅ (JSON API) | ✅ (post, reply) | ✅ (JSON API) | Optional API Keys |
| **LinkedIn** | ✅ (Jina Reader) | ✅ (shares) | ❌ | access_token / person_id |
| **Slack** | ❌ | ✅ (webhooks) | ❌ | webhook_url |
| **Discord** | ❌ | ✅ (webhooks) | ❌ | webhook_url |
| **Email** | ❌ | ✅ (SMTP) | ❌ | host, port, user, pass |
| **Telegram** | ❌ | ✅ (bot api) | ❌ | bot_token, chat_id |

---

## Quick Start

### 1. Installation
Install AgentForge using `pip` or `uv`:

```bash
pip install .
```

### 2. Auto-Install Dependencies
Run `install` to let AgentForge detect your environment and pull missing CLI tools (like `yt-dlp` or `gh`):

```bash
agentforge install
```

### 3. Diagnostics Check
Verify system status and platform configurations:

```bash
agentforge doctor
```

---

## Usage Examples

### Web Search & Reading
```bash
# Search the web using DuckDuckGo
agentforge search "AI agents 2026"

# Read web page content (clean markdown)
agentforge web https://example.com
```

### GitHub Operations
```bash
# View repo details
agentforge github read owner/repo

# Create a new issue
agentforge github create-issue owner/repo --title "Critical Bug" --body "Detailed explanation"

# Comment on an issue
agentforge github comment owner/repo --issue 123 --body "Working on this now!"
```

### Twitter / X
```bash
# Read a tweet
agentforge twitter read https://twitter.com/user/status/123456

# Post a tweet
agentforge twitter post "AgentForge has officially launched! 🚀"
```

---

## Workflow Pipelines (YAML)

Chaining actions across multiple platforms is easy with YAML pipelines.

### Example: `daily_digest.yaml`
```yaml
name: "Daily AI Research Digest"
steps:
  - name: "Search Twitter"
    platform: twitter
    action: search
    params:
      query: "AI agents OR LLM tools"
      limit: 10
    output_var: tweets
  
  - name: "Post Slack Alert"
    platform: slack
    action: send
    params:
      message: "🤖 Found {tweets.count} new tweets on AI agents today."
```

Run the pipeline:
```bash
agentforge pipeline run daily_digest.yaml
```

---

## Automated Keyword Monitoring

Start background watches that trigger actions when new search results appear:

```bash
agentforge watch --platform twitter --query "AgentForge" --interval 30m --notify slack-alerts
```

---

## Notification Dispatcher

Set up and manage channels (Slack, Discord, Telegram, Email, Webhooks):

```bash
# Configure Slack channel
agentforge notify setup slack-channel --type slack --url "https://hooks.slack.com/services/..."

# Test notification delivery
agentforge notify send slack-channel "Test notification from AgentForge! 🔔"
```

---

## Secure Credential Vault

All access tokens, passwords, and API keys are stored locally at `~/.agentforge/credentials.json` and encrypted at rest using AES symmetric key encryption (`cryptography.fernet`).

```bash
# Save credentials
agentforge vault set twitter api_key "YOUR_API_KEY"

# List configured keys (values masked)
agentforge vault list

# Delete credentials
agentforge vault delete twitter api_key
```

---

## For AI Agents (SKILL.md)

AgentForge includes an agent-native playbook (`skill/SKILL.md`) that teaches models like Claude or GPT exactly how to use this tool to interact with the web. Copy it to your agent directory:

```bash
agentforge install --skill /path/to/agent/skills/
```

---

## Plugin System

Extend AgentForge by writing custom python platforms.

### 1. Generate boilerplate template
```bash
agentforge plugin create custom_platform --cls CustomPlatform
```

### 2. Install plugin locally
```bash
agentforge plugin install ~/.agentforge/plugins/custom_platform
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
