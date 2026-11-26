import click
import sys
import yaml
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from agentforge import __version__
from agentforge.output import OutputFormatter
from agentforge.vault import CredentialVault
from agentforge.platforms import get_platform
from agentforge.pipeline import Pipeline
from agentforge.scheduler import Scheduler
from agentforge.notifier import Notifier
from agentforge.doctor import Doctor
from agentforge.installer import Installer
from agentforge.plugins.loader import PluginLoader

BANNER = """
 █─▄▄─█─▄▄▄▄█─▄▄▄─█▄─▀█▄─▄█─▄▄▄▄█─▄▄▄▄█─▄▄▄─█─▄▄▄▄█─▄▄▄▄█
 █─██─█─██▄─█─███─██─█▄▀─██─▄▄▄██─▄▄▄─█─███▀█─██▄─█─██▄─█
 ▀▄▄▄▄▀▄▄▄▄▄▀▄▄▄▄▄▀▄▄▄▀▀▄▄▀▄▄▄▄▄▀▄▄▄▄▄▀▄▄▄▄▄▀▄▄▄▄▄▀▄▄▄▄▄▀
               HANDS FOR YOUR AI AGENT
"""

class CLIContext:
    def __init__(self, output_format: str):
        self.output_format = output_format

@click.group(invoke_without_command=True)
@click.option('--output', '-o', type=click.Choice(['text', 'json', 'csv', 'markdown']), default='text', help='Select structured output format.')
@click.option('--version', '-v', is_flag=True, help='Show AgentForge version.')
@click.pass_context
def cli(ctx, output, version):
    """AgentForge CLI: Read, Write, and Automate across the internet."""
    console = Console()
    
    if version:
        console.print(f"AgentForge v{__version__}")
        ctx.exit()
        
    ctx.obj = CLIContext(output_format=output)
    
    if ctx.invoked_subcommand is None:
        # Show Banner and Help
        try:
            BANNER.encode(console.encoding)
            banner = BANNER
        except UnicodeEncodeError:
            banner = "AgentForge"
        banner_text = Text(banner, style="magenta bold")
        console.print(Panel(banner_text, border_style="magenta", subtitle=f"Version {__version__}"))
        click.echo(ctx.get_help())

# --- PLATFORM COMMANDS ---

# 1. Web
@cli.command()
@click.argument('url')
@click.option('--no-jina', is_flag=True, help='Disable Jina Reader and fetch HTML directly.')
@click.pass_context
def web(ctx, url, no_jina):
    """Read and extract clean text from any URL."""
    platform = get_platform("web")
    res = platform.read(url, use_jina=not no_jina)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

# 2. Search
@cli.command()
@click.argument('query')
@click.option('--limit', '-n', default=5, type=int, help='Maximum results.')
@click.pass_context
def search(ctx, query, limit):
    """Search the web (Exa API or free DuckDuckGo)."""
    platform = get_platform("search")
    res = platform.search(query, limit=limit)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

# 3. YouTube
@cli.group()
def youtube():
    """Extract metadata/transcripts and search YouTube."""
    pass

@youtube.command(name='read')
@click.argument('url')
@click.pass_context
def yt_read(ctx, url):
    """Read video details and captions."""
    platform = get_platform("youtube")
    res = platform.read(url)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

@youtube.command(name='search')
@click.argument('query')
@click.option('--limit', '-n', default=5, type=int, help='Maximum results.')
@click.pass_context
def yt_search(ctx, query, limit):
    """Search for YouTube videos."""
    platform = get_platform("youtube")
    res = platform.search(query, limit=limit)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

# 4. RSS
@cli.command()
@click.argument('url')
@click.option('--limit', '-n', default=10, type=int, help='Number of feed entries.')
@click.pass_context
def rss(ctx, url, limit):
    """Read entries from an RSS/Atom feed URL."""
    platform = get_platform("rss")
    res = platform.read(url, limit=limit)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

# 5. Twitter
@cli.group()
def twitter():
    """Read, search, post, and like tweets on Twitter/X."""
    pass

@twitter.command(name='read')
@click.argument('target')
@click.pass_context
def tw_read(ctx, target):
    """Read a specific tweet or thread by ID/URL."""
    platform = get_platform("twitter")
    res = platform.read(target)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

@twitter.command(name='search')
@click.argument('query')
@click.option('--limit', '-n', default=5, type=int, help='Max tweets.')
@click.pass_context
def tw_search(ctx, query, limit):
    """Search tweets."""
    platform = get_platform("twitter")
    res = platform.search(query, limit=limit)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

@twitter.command(name='post')
@click.argument('content')
@click.option('--reply-to', '-r', help='Reply to a tweet ID.')
@click.pass_context
def tw_post(ctx, content, reply_to):
    """Create a new tweet (or reply)."""
    platform = get_platform("twitter")
    res = platform.write(content, reply_to=reply_to)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

# 6. GitHub
@cli.group()
def github():
    """Manage repos, issues, pull requests, and comments."""
    pass

@github.command(name='read')
@click.argument('repo')
@click.option('--readme', is_flag=True, help='Directly read the README.')
@click.pass_context
def gh_read(ctx, repo, readme):
    """Read repository details, issues list, or README."""
    platform = get_platform("github")
    action = "readme" if readme else "repo"
    res = platform.read(repo, action=action)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

@github.command(name='search')
@click.argument('query')
@click.option('--limit', '-n', default=5, type=int, help='Max repos.')
@click.pass_context
def gh_search(ctx, query, limit):
    """Search repositories on GitHub."""
    platform = get_platform("github")
    res = platform.search(query, limit=limit)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

@github.command(name='create-issue')
@click.argument('repo')
@click.option('--title', '-t', required=True, help='Issue title.')
@click.option('--body', '-b', required=True, help='Issue body description.')
@click.pass_context
def gh_issue(ctx, repo, title, body):
    """Create a new issue on a GitHub repository."""
    platform = get_platform("github")
    res = platform.write(body, action="create-issue", repo=repo, title=title)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

@github.command(name='comment')
@click.argument('repo')
@click.option('--issue', '-i', required=True, help='Issue number.')
@click.option('--body', '-b', required=True, help='Comment content.')
@click.pass_context
def gh_comment(ctx, repo, issue, body):
    """Comment on an issue or pull request."""
    platform = get_platform("github")
    res = platform.write(body, action="comment", repo=repo, issue_number=issue)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

# 7. Reddit
@cli.group()
def reddit():
    """Read, search subreddits, post and reply on Reddit."""
    pass

@reddit.command(name='read')
@click.argument('target')
@click.pass_context
def rd_read(ctx, target):
    """Read details and comment tree of a Reddit post."""
    platform = get_platform("reddit")
    res = platform.read(target)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

@reddit.command(name='search')
@click.argument('query')
@click.option('--sub', help='Search within specific subreddit.')
@click.option('--limit', '-n', default=5, type=int, help='Max results.')
@click.pass_context
def rd_search(ctx, query, sub, limit):
    """Search Reddit posts."""
    platform = get_platform("reddit")
    res = platform.search(query, subreddit=sub, limit=limit)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

@reddit.command(name='post')
@click.argument('content')
@click.option('--sub', '-s', required=True, help='Subreddit name.')
@click.option('--title', '-t', required=True, help='Post title.')
@click.pass_context
def rd_post(ctx, content, sub, title):
    """Submit a text post to a subreddit."""
    platform = get_platform("reddit")
    res = platform.write(content, action="post", subreddit=sub, title=title)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

@reddit.command(name='reply')
@click.argument('content')
@click.option('--to', required=True, help='Target post or comment ID (e.g. t3_xxxx or t1_xxxx).')
@click.pass_context
def rd_reply(ctx, content, to):
    """Reply to a submission or comment."""
    platform = get_platform("reddit")
    res = platform.write(content, action="reply", reply_to=to)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

# 8. LinkedIn
@cli.group()
def linkedin():
    """Read updates and post updates to LinkedIn."""
    pass

@linkedin.command(name='read')
@click.argument('url')
@click.pass_context
def li_read(ctx, url):
    """Read a public profile or company page details via Jina."""
    platform = get_platform("linkedin")
    res = platform.read(url)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

@linkedin.command(name='post')
@click.argument('content')
@click.option('--subject', help='Optional share title.')
@click.pass_context
def li_post(ctx, content, subject):
    """Post a share update to your LinkedIn profile."""
    platform = get_platform("linkedin")
    res = platform.write(content, subject=subject)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

# 9. Email
@cli.command()
@click.argument('body')
@click.option('--to', required=True, help='Recipient email.')
@click.option('--subject', '-s', default='AgentForge Update', help='Email subject.')
@click.option('--cc', help='Optional CC addresses (comma separated).')
@click.option('--html', is_flag=True, help='Format body content as HTML.')
@click.pass_context
def email(ctx, body, to, subject, cc, html):
    """Send an automated SMTP email."""
    platform = get_platform("email")
    res = platform.write(body, to=to, subject=subject, cc=cc, html=html)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

# 10. Slack
@cli.command()
@click.argument('message')
@click.option('--webhook', help='Slack Webhook URL override.')
@click.pass_context
def slack(ctx, message, webhook):
    """Send a notification message to a Slack channel."""
    platform = get_platform("slack")
    res = platform.write(message, webhook_url=webhook)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

# 11. Discord
@cli.command()
@click.argument('message')
@click.option('--webhook', help='Discord Webhook URL override.')
@click.pass_context
def discord(ctx, message, webhook):
    """Send a notification message to a Discord webhook."""
    platform = get_platform("discord")
    res = platform.write(message, webhook_url=webhook)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

# 12. Telegram
@cli.command()
@click.argument('message')
@click.option('--chat-id', help='Telegram chat/channel ID override.')
@click.pass_context
def telegram(ctx, message, chat_id):
    """Send a message to a Telegram chat/channel."""
    platform = get_platform("telegram")
    res = platform.write(message, chat_id=chat_id)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)


# --- UTILITIES ---

# Doctor
@cli.command()
def doctor():
    """Run full diagnostic environment suite."""
    Doctor().diagnose()

# Install
@cli.command()
@click.option('--port', default=8765, type=click.IntRange(0, 65535), show_default=True)
def studio(port):
    """Open a local browser workspace for the bundled demo workflows."""
    from agentforge.studio import create_server

    try:
        server = create_server(port)
    except OSError as exc:
        raise click.ClickException(f"Could not start Studio on port {port}: {exc}") from exc
    with server:
        click.echo(f"AgentForge Studio: http://127.0.0.1:{server.server_port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            click.echo("Studio stopped.")


@cli.command()
@click.option('--safe', is_flag=True, help='Safe mode (detect only, no installations).')
@click.option('--skill', help='Copy SKILL.md playbook to target path.')
def install(safe, skill):
    """Auto-install system and Python dependencies."""
    installer = Installer(safe_mode=safe)
    if skill:
        installer.setup_skill(skill)
    else:
        installer.install_all()

# Vault
@cli.group()
def vault():
    """Manage local authenticated platform credentials securely."""
    pass

@vault.command(name='set')
@click.argument('platform')
@click.argument('key')
@click.argument('value')
@click.pass_context
def vault_set(ctx, platform, key, value):
    """Store credential entry (e.g. vault set github token XXXXX)."""
    v = CredentialVault()
    v.set(platform, key, value)
    OutputFormatter.render({"platform": platform, "key": key, "status": "Saved successfully."}, format_type=ctx.obj.output_format)

@vault.command(name='get')
@click.argument('platform')
@click.argument('key')
@click.pass_context
def vault_get(ctx, platform, key):
    """Retrieve credential entry."""
    v = CredentialVault()
    val = v.get(platform, key)
    if val:
        OutputFormatter.render({key: val}, format_type=ctx.obj.output_format)
    else:
        OutputFormatter.render({"error": f"Key '{key}' not found for platform '{platform}'."}, format_type=ctx.obj.output_format)

@vault.command(name='list')
@click.pass_context
def vault_list(ctx):
    """List configured platforms and keys (values masked)."""
    v = CredentialVault()
    list_res = v.list_credentials()
    OutputFormatter.render(list_res, format_type=ctx.obj.output_format)

@vault.command(name='delete')
@click.argument('platform')
@click.argument('key')
@click.pass_context
def vault_delete(ctx, platform, key):
    """Remove credential entry."""
    v = CredentialVault()
    success = v.delete(platform, key)
    OutputFormatter.render({"platform": platform, "key": key, "deleted": success}, format_type=ctx.obj.output_format)

# Pipeline
@cli.group()
def pipeline():
    """Run and validate multi-platform YAML workflows."""
    pass

@pipeline.command(name='run')
@click.argument('yaml_file')
@click.pass_context
def pipeline_run(ctx, yaml_file):
    """Execute pipeline YAML workflow."""
    try:
        res = Pipeline(config_path=yaml_file).run()
    except (OSError, yaml.YAMLError) as exc:
        res = {"success": False, "error": str(exc)}
    OutputFormatter.render(res, format_type=ctx.obj.output_format)
    if not res["success"]:
        ctx.exit(1)

@pipeline.command(name='validate')
@click.argument('yaml_file')
@click.pass_context
def pipeline_validate(ctx, yaml_file):
    """Validate pipeline YAML structure."""
    try:
        errors = Pipeline(config_path=yaml_file).validate()
    except (OSError, yaml.YAMLError) as exc:
        errors = [str(exc)]
    if errors:
        OutputFormatter.render({"valid": False, "errors": errors}, format_type=ctx.obj.output_format)
        ctx.exit(1)
    else:
        OutputFormatter.render({"valid": True, "notes": "Pipeline structure is valid."}, format_type=ctx.obj.output_format)

# Watch
@cli.command()
@click.option('--platform', '-p', required=True, help='Platform to monitor (twitter, reddit, search).')
@click.option('--query', '-q', required=True, help='Query keyword or search terms.')
@click.option('--interval', '-i', default='30m', help='Monitoring check interval (e.g. 15m, 1h, 1d).')
@click.option('--notify', '-n', required=True, help='Notification channel configured in Notifier.')
def watch(platform, query, interval, notify):
    """Start automated scheduled background keyword monitoring."""
    s = Scheduler()
    job_id = s.add_watch(platform, query, interval, notify)
    s.start()
    Console().print(f"[green]✓ Started background watch job with ID: [bold]{job_id}[/bold][/green]")
    Console().print(f"  Monitoring [cyan]{platform.upper()}[/cyan] query: \"{query}\" every {interval}. Alerts: {notify}")
    Console().print("  Keep this process running to continue scheduler.")
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        s.stop()
        Console().print("\n[yellow]Scheduler stopped.[/yellow]")

# Notify
@cli.group()
def notify():
    """Configure notification alerts channels."""
    pass

@notify.command(name='setup')
@click.argument('name')
@click.option('--type', '-t', required=True, type=click.Choice(['slack', 'discord', 'telegram', 'email', 'webhook']), help='Notification channel type.')
@click.option('--url', help='Webhook URL or general URL.')
@click.option('--bot-token', help='Telegram bot token.')
@click.option('--chat-id', help='Telegram chat or channel ID.')
@click.option('--smtp-host', help='SMTP host for emails.')
@click.option('--smtp-port', default=587, type=int, help='SMTP port.')
@click.option('--smtp-user', help='SMTP user login.')
@click.option('--smtp-pass', help='SMTP password.')
@click.option('--sender', help='SMTP default sender address.')
@click.pass_context
def notify_setup(ctx, name, type, **kwargs):
    """Configure notification channel (e.g. setup slack-alerts --type slack --url ...)."""
    # Clean None values
    config = {k: v for k, v in kwargs.items() if v is not None}
    if "url" in config and type in ("slack", "discord"):
        config["webhook_url"] = config.pop("url")
        
    n = Notifier()
    n.setup_channel(name, type, **config)
    OutputFormatter.render({"channel": name, "type": type, "status": "Configured successfully."}, format_type=ctx.obj.output_format)

@notify.command(name='send')
@click.argument('channel')
@click.argument('message')
@click.pass_context
def notify_send(ctx, channel, message):
    """Send test alert to a notification channel."""
    n = Notifier()
    res = n.send(channel, message)
    OutputFormatter.render(res, format_type=ctx.obj.output_format)

@notify.command(name='list')
@click.pass_context
def notify_list(ctx):
    """List configured notification channels."""
    n = Notifier()
    channels = n.list_channels()
    OutputFormatter.render(channels, format_type=ctx.obj.output_format)

# Plugins
@cli.group()
def plugin():
    """Install, list, and create custom AgentForge plugins."""
    pass

@plugin.command(name='list')
@click.pass_context
def plugin_list(ctx):
    """List discovered custom plugins."""
    loader = PluginLoader()
    plugins = loader.discover_plugins()
    OutputFormatter.render(plugins, format_type=ctx.obj.output_format)

@plugin.command(name='install')
@click.argument('path')
@click.pass_context
def plugin_install(ctx, path):
    """Install plugin from a local directory path."""
    loader = PluginLoader()
    success = loader.install_local_plugin(path)
    OutputFormatter.render({"source": path, "installed": success}, format_type=ctx.obj.output_format)

@plugin.command(name='create')
@click.argument('name')
@click.option('--cls', required=True, help='Platform python class name (e.g. MyPlatform).')
@click.pass_context
def plugin_create(ctx, name, cls):
    """Generate custom plugin template files."""
    loader = PluginLoader()
    path = loader.create_plugin_template(name, cls)
    OutputFormatter.render({"plugin": name, "class": cls, "template_path": path}, format_type=ctx.obj.output_format)

if __name__ == '__main__':
    cli()
