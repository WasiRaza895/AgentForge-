# Contributing to AgentForge

Thanks for helping make AgentForge more useful. Bug fixes, tests, documentation improvements, and focused platform integrations are welcome.

## Development setup

1. Fork and clone the repository.
2. Create a branch from `main`.
3. Create a virtual environment and install the project:

   ```bash
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   # macOS/Linux: source .venv/bin/activate
   python -m pip install -e ".[dev]"
   ```

4. Run the test suite:

   ```bash
   python -m pytest -q
   ```

## Pull requests

- Keep each pull request focused on one change.
- Add tests for behavior changes and update relevant documentation.
- Never commit credentials, access tokens, webhook URLs, or local vault files.
- Explain user-facing impact and how the change was verified.

For a new platform adapter, follow the existing implementations in `src/agentforge/platforms`, inherit from `BasePlatform`, and expose accurate capability flags.

By contributing, you agree that your contribution is licensed under the MIT License.
