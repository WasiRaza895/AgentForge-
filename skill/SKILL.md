---
name: AgentForge
description: Playbook for reading, writing, searching, and automating tasks across Twitter, GitHub, Reddit, Slack, Discord, Telegram, Email, and general web pages.
---

# AgentForge Agent Playbook

You are equipped with **AgentForge**, a powerful command-line integration suite that gives you both **eyes to read** and **hands to write/act** across the internet.

Use this playbook to understand how to interact with the web, manage credentials, schedule watches, run automation pipelines, and handle errors.

---

## Workspace Rules (Enforced)
1. **Never write credential files to user workspaces.** All configurations, keys, and tokens must go into the vault: `agentforge vault set <platform> <key> <value>`.
2. **Never commit raw tokens or credentials** to project code.
3. **Use the vault** or set environment variables dynamically during shell commands.
4. **Use JSON format outputs (`--output json`)** when you need to process data inside scripts, Python code, or custom variables.

---

## 1. Diagnostics & Recovery
When a platform integration isn't responding, check dependencies and authentication state first:
```bash
agentforge doctor
```

If dependencies are missing, run the auto-installer:
```bash
agentforge install
```

---

## 2. Core Commands Reference

### Web Reading & Search
- **Search the web** (uses Exa API semantic search if configured, otherwise falls back to DuckDuckGo):
  ```bash
  agentforge search "query strings here"
  ```
- **Read URL contents** (converts html pages into clean text/markdown):
  ```bash
  agentforge web https://example.com/some/article
  ```

### Twitter / X
- **Read a tweet or thread**:
  ```bash
  agentforge twitter read https://twitter.com/username/status/123456
  ```
- **Search Twitter**:
  ```bash
  agentforge twitter search "query strings" --limit 5
  ```
- **Post a tweet**:
  ```bash
  agentforge twitter post "New content to publish here! 🚀"
  ```
- **Reply to a tweet**:
  ```bash
  agentforge twitter post "My reply text" --reply-to 1234567890
  ```

### GitHub
- **View repo info**:
  ```bash
  agentforge github read owner/repo
  ```
- **Read repository README**:
  ```bash
  agentforge github read owner/repo --readme
  ```
- **Create a GitHub issue**:
  ```bash
  agentforge github create-issue owner/repo --title "Bug: Issue Title" --body "Issue description details"
  ```
- **Post a comment on an issue**:
  ```bash
  agentforge github comment owner/repo --issue 42 --body "My comment content here."
  ```

### Reddit
- **Read post & comment tree**:
  ```bash
  agentforge reddit read https://www.reddit.com/r/subreddit/comments/id/title/
  ```
- **Search Reddit posts**:
  ```bash
  agentforge reddit search "python web scrapers" --limit 5
  ```
- **Create a post**:
  ```bash
  agentforge reddit post "Post text body content" --sub r/mySubreddit --title "Post Title"
  ```
- **Reply to post or comment**:
  ```bash
  agentforge reddit reply "My comment reply text" --to t3_postid
  ```

### LinkedIn
- **Read public profile or page**:
  ```bash
  agentforge linkedin read https://linkedin.com/in/username
  ```
- **Post an update**:
  ```bash
  agentforge linkedin post "Sharing automated update with my network!"
  ```

### SMTP Email
- **Send an email**:
  ```bash
  agentforge email "Body content text" --to recipient@email.com --subject "Agent Report"
  ```
- **Send HTML email**:
  ```bash
  agentforge email "<h1>Daily Summary</h1><p>Done.</p>" --to recipient@email.com --subject "Digest" --html
  ```

---

## 3. Workflow Pipelines (YAML)

You can chain actions across different platforms to automate complex research and distribution flows.

### Pipeline Config Schema
```yaml
name: "My Workflow Pipeline"
steps:
  - name: "Read Web Source"
    platform: web
    action: read
    params:
      target: "https://news.ycombinator.com"
    output_var: hn_news
    
  - name: "Summarize and Post to Slack"
    platform: slack
    action: send
    params:
      message: "HackerNews Digest:\n\n{hn_news.content}"
```

### Running Pipelines
- **Validate configuration**:
  ```bash
  agentforge pipeline validate my_pipeline.yaml
  ```
- **Run the pipeline**:
  ```bash
  agentforge pipeline run my_pipeline.yaml
  ```

---

## 4. Notifications & Alerts Setup
Configure notification channels so you can push updates to Slack, Discord, Telegram, or email.

- **Slack Configuration**:
  ```bash
  agentforge notify setup slack-alerts --type slack --url "https://hooks.slack.com/services/..."
  ```
- **Telegram bot Setup**:
  ```bash
  agentforge notify setup telegram-alerts --type telegram --bot-token "BOT_TOKEN" --chat-id "CHAT_ID"
  ```
- **Email defaults Setup**:
  ```bash
  agentforge notify setup email-alerts --type email --smtp-host "smtp.gmail.com" --smtp-port 587 --smtp-user "me@gmail.com" --smtp-pass "PASS" --to "recipient@email.com"
  ```
- **Send a test notification**:
  ```bash
  agentforge notify send slack-alerts "Hello channel!"
  ```

---

## 5. Automated Monitoring (Watch)
Start a background loop to watch keywords or pages and push alerts to notification channels when new items are detected.

- **Watch Twitter**:
  ```bash
  agentforge watch --platform twitter --query "LLMs" --interval 1h --notify slack-alerts
  ```
- **Watch Reddit**:
  ```bash
  agentforge watch --platform reddit --query "AgentForge" --interval 30m --notify telegram-alerts
  ```

---

## 6. Secure Credential Management
Save API keys and OAuth tokens using local Fernet encryption:

- **Save keys**:
  ```bash
  agentforge vault set <platform> <key> <value>
  ```
- **Delete keys**:
  ```bash
  agentforge vault delete <platform> <key>
  ```
- **List saved keys**:
  ```bash
  agentforge vault list
  ```
