# Installation Guide

Follow this guide to install AgentForge and set up system dependencies.

---

## 1. Prerequisites
- **Python**: Version 3.10 or higher.
- **Node.js**: (Optional) Required for specific JS-based MCP plugins.

---

## 2. Installation Methods

### Method A: Local Pip Install (Development)
Clone the repository and install it in editable mode:
```bash
git clone https://github.com/yourusername/agentforge.git
cd agentforge
pip install -e .
```

### Method B: Install via uv (Recommended)
`uv` is extremely fast and manages environments cleanly:
```bash
uv pip install .
```

### Method C: Pipx (Isolated CLI tool)
Install AgentForge as a globally available tool without cluttering global python space:
```bash
pipx install .
```

---

## 3. Post-Installation Setup

Once installed, run the automated installation sequence to pull upstream binary dependencies (e.g. `yt-dlp` or `gh`):

```bash
agentforge install
```

Verify that all platforms are working and diagnosed successfully:

```bash
agentforge doctor
```

---

## 4. Platform-Specific Credentials Setup

Some platforms require keys or authentication to perform write actions. Store them in the Vault:

### GitHub CLI Auth (Recommended)
Login directly via gh CLI:
```bash
gh auth login
```
Alternatively, save a personal access token into the Vault:
```bash
agentforge vault set github token "YOUR_GITHUB_TOKEN"
```

### Twitter / X API keys
To enable tweeting or replying:
```bash
agentforge vault set twitter api_key "YOUR_KEY"
agentforge vault set twitter api_secret "YOUR_SECRET"
agentforge vault set twitter access_token "YOUR_TOKEN"
agentforge vault set twitter access_token_secret "YOUR_TOKEN_SECRET"
```

### Reddit API Credentials
To enable Reddit post submissions or comment replies:
```bash
agentforge vault set reddit client_id "YOUR_CLIENT_ID"
agentforge vault set reddit client_secret "YOUR_CLIENT_SECRET"
agentforge vault set reddit username "YOUR_USERNAME"
agentforge vault set reddit password "YOUR_PASSWORD"
```
