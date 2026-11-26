# AgentForge Quickstart Guide

Get up and running with AgentForge in under 5 minutes.

---

## Step 1: Install & Diagnostics
Install AgentForge and check which integrations are available.
```bash
pip install -e .
agentforge doctor
```

From the repository root, try the release briefing with bundled data or open Studio.

```bash
agentforge --output json pipeline run examples/rss_briefing.yaml
agentforge studio
```

---

## Step 2: Read URL or Search the Web
Retrieve text from any website or query DuckDuckGo:
```bash
# Web search
agentforge search "SpaceX launch schedule"

# Read page details
agentforge web https://news.ycombinator.com
```

---

## Step 3: Configure Slack Alerts
Let's route research directly to Slack. Create an Incoming Webhook in Slack first, then configure it:
```bash
# Setup Slack notification channel
agentforge notify setup slack-channel --type slack --url "https://hooks.slack.com/services/..."

# Test alert delivery
agentforge notify send slack-channel "Hello Slack from AgentForge!"
```

---

## Step 4: Write Custom YAML Pipeline
Create `hackernews.yaml` to search for updates and send the count to Slack. Store the Slack webhook under `slack webhook_url` with `agentforge vault set` for this direct adapter call.

```yaml
name: "HN Search & Notify Pipeline"
steps:
  - name: "Web Search"
    platform: search
    action: search
    params:
      query: "LLM agents release"
      limit: 3
    output_var: search_results
    
  - name: "Post to Slack"
    platform: slack
    action: send
    params:
      message: "Found {search_results.count} recent results."
```

Run the pipeline:
```bash
agentforge pipeline run hackernews.yaml
```

---

## Step 5: Start Background Watch Jobs
Let's watch for a keyword on Reddit and notify Slack when new matching items appear:
```bash
agentforge watch --platform reddit --query "Python" --interval 15m --notify slack-channel
```
*(Press Ctrl+C to terminate the scheduler)*
